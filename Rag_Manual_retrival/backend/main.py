from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from nvidia_embeddings import NVIDIANIMEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import os
import shutil
import chat
import auth
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.http import models
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

app = FastAPI()

# Include the routers
app.include_router(chat.router)
app.include_router(auth.router)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# -----------------------------
# MongoDB setup
# -----------------------------
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://rishi:rishi123@cluster0.1tfj3.mongodb.net/datquest"
)
MONGODB_DB = os.getenv("MONGODB_DB", "datquest")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "uploads")

try:
    mongo_client = MongoClient(MONGODB_URI)
    mongo_db = mongo_client[MONGODB_DB]
    mongo_collection = mongo_db[MONGODB_COLLECTION]
    # Test connection
    mongo_client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    mongo_client = None
    mongo_db = None
    mongo_collection = None

# -----------------------------
# Cloudinary setup
# -----------------------------
cloudinary.config(
    cloud_name="rishiproject",
    api_key="451394548967359",
    api_secret="vQi8o9Cjypie4bHxvhrDSKdZjFs"
)

def upload_to_cloudinary(file_path: str, public_id: str = None) -> dict:
    """
    Upload a file to Cloudinary and return the upload result
    """
    try:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="raw",  # For PDF files
            public_id=public_id,
            folder="pdf_manuals"  # Organize PDFs in a folder
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

def delete_from_cloudinary(public_id: str) -> bool:
    """
    Delete a file from Cloudinary using its public_id
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="raw")
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Cloudinary deletion failed: {e}")
        return False

# Store list of uploaded files
uploaded_files = []
current_company_name: str | None = None

@app.post("/upload_pdf/")
async def upload_pdf(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    product_name: str | None = Form(None),
    product_code: str | None = Form(None)
):
    try:
        # Remove all previously uploaded files
        for old_file in UPLOAD_DIR.iterdir():
            if old_file.is_file():
                old_file.unlink()
        uploaded_files.clear()

        # Optionally: Clear Qdrant collection (requires Qdrant client)
        # from qdrant_client import QdrantClient
        # client = QdrantClient(url="http://localhost:6333")
        # client.delete_collection(collection_name='learn_vector')

        # Save uploaded file temporarily for processing
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Determine product_name (fallback to product_code for backward compatibility)
        resolved_product_name = product_name or product_code
        if not resolved_product_name:
            raise HTTPException(status_code=400, detail="product_name or product_code is required")

        # Upload to Cloudinary
        try:
            cloudinary_result = upload_to_cloudinary(
                str(file_path), 
                public_id=f"{company_name}_{resolved_product_name}_{file.filename}"
            )
            cloudinary_uri = cloudinary_result["secure_url"]
            cloudinary_public_id = cloudinary_result["public_id"]
            print(f"✅ File uploaded to Cloudinary: {cloudinary_uri}")
        except Exception as e:
            # Clean up local file if Cloudinary upload fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to upload to Cloudinary: {str(e)}")

        # Insert metadata record in MongoDB
        try:
            if mongo_collection is None:
                raise HTTPException(status_code=500, detail="MongoDB connection not available")
            
            insert_doc = {
                "company_name": company_name,
                "product_name": resolved_product_name,
                "uri": cloudinary_uri,
                "cloudinary_public_id": cloudinary_public_id,
                "filename": file.filename,
            }
            insert_result = mongo_collection.insert_one(insert_doc)
            inserted_id = str(insert_result.inserted_id)
            # update current company
            global current_company_name
            current_company_name = company_name
        except Exception as db_err:
            raise HTTPException(status_code=500, detail=f"Database insert failed: {db_err}")

        # Extract core PDF metadata once per file
        pdf_meta = {}
        try:
            reader = PdfReader(str(file_path))
            info = reader.metadata or {}
            # Normalize keys to match user-provided schema
            pdf_meta["producer"] = info.get("/Producer") or info.get("producer")
            pdf_meta["creator"] = info.get("/Creator") or info.get("creator")
            pdf_meta["creationdate"] = info.get("/CreationDate") or info.get("creationdate")
            pdf_meta["moddate"] = info.get("/ModDate") or info.get("moddate")
            pdf_meta["total_pages"] = len(reader.pages)
            pdf_meta["source"] = cloudinary_uri
        except Exception:
            pdf_meta = {"source": cloudinary_uri}

        # Load PDF
        loader = PyPDFLoader(file_path=str(file_path))
        docs = loader.load()
        # Attach metadata
        for d in docs:
            d.metadata = d.metadata or {}
            d.metadata["company_name"] = company_name
            d.metadata["product_name"] = resolved_product_name
            d.metadata["product_code"] = product_code
            # Override the source with Cloudinary URI (PyPDFLoader sets it to local path)
            d.metadata["source"] = cloudinary_uri
            # Merge core PDF metadata into page-level docs
            for k, v in pdf_meta.items():
                if v is not None:
                    d.metadata[k] = v

        # Chunk documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=500
        )
        split_docs = text_splitter.split_documents(documents=docs)
        for d in split_docs:
            d.metadata = d.metadata or {}
            d.metadata["product_name"] = resolved_product_name
            d.metadata["filename"] = file.filename
            d.metadata["db_id"] = inserted_id
            d.metadata["company_name"] = company_name
            d.metadata["product_code"] = product_code
            # Ensure source is set to Cloudinary URI in chunks
            d.metadata["source"] = cloudinary_uri
            # Preserve page metadata and core PDF metadata into chunks
            for k, v in pdf_meta.items():
                if v is not None:
                    d.metadata[k] = v

        # Create embeddings and store in Qdrant
        try:
            embedding_model = NVIDIANIMEmbeddings()
            
            # Check if collection exists and create/recreate if needed
            qdrant_client = QdrantClient(
                url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM"
            )
            
            collections = qdrant_client.get_collections()
            collection_exists = any(col.name == 'learn_vector3' for col in collections.collections)
            
            if not collection_exists:
                print("🆕 Creating new learn_vector3 collection...")
                # Create collection for first time
                vector_store = QdrantVectorStore.from_documents(
                    documents=split_docs,
                    url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
                    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM",
                    collection_name='learn_vector3',
                    embedding=embedding_model
                )
                print("✅ Documents stored in Qdrant successfully (new collection)")
            else:
                print("📚 Adding documents to existing learn_vector3 collection...")
                # Add to existing collection
                vector_store = QdrantVectorStore.from_existing_collection(
                    url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
                    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM",
                    collection_name='learn_vector3',
                    embedding=embedding_model
                )
                
                # Add new documents to existing collection
                vector_store.add_documents(split_docs)
                print("✅ Documents added to existing Qdrant collection successfully")
                
        except Exception as qdrant_err:
            print(f"⚠️  Qdrant storage failed: {qdrant_err}")
            print("   Documents processed but not stored in vector database")
            # Continue without Qdrant - the upload will still succeed

        # Clean up local file after successful processing
        try:
            if file_path.exists():
                file_path.unlink()
                print(f"✅ Local file {file.filename} cleaned up")
        except Exception as cleanup_err:
            print(f"⚠️  Local file cleanup failed: {cleanup_err}")

        # Add file to uploaded_files list
        uploaded_files.append(file.filename)
        return {
            "message": f"PDF {file.filename} processed successfully",
            "files": uploaded_files,
            "db_record": {
                "_id": inserted_id,
                "company_name": company_name,
                "product_name": resolved_product_name,
                "uri": cloudinary_uri,
                "cloudinary_public_id": cloudinary_public_id,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_uploaded_files/")
async def get_uploaded_files():
    return {"files": uploaded_files}

@app.post("/remove_file/")
async def remove_file(file_name: str):
    global uploaded_files
    if file_name in uploaded_files:
        file_path = UPLOAD_DIR / file_name
        if file_path.exists():
            file_path.unlink()  # Remove the file from disk
        uploaded_files.remove(file_name)
        return {"message": f"File {file_name} removed successfully", "files": uploaded_files}
    raise HTTPException(status_code=400, detail="File not found")

# -----------------------------
# New APIs: companies and models
# -----------------------------
@app.get("/companies/")
async def list_companies():
    try:
        if mongo_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB connection not available")
        companies = mongo_collection.distinct("company_name")
        return {"companies": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/current/")
async def current_company():
    try:
        # Prefer in-memory last uploaded; fallback to latest in DB
        if current_company_name:
            return {"company_name": current_company_name}
        if mongo_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB connection not available")
        doc = mongo_collection.find_one(sort=[("_id", -1)])
        return {"company_name": (doc or {}).get("company_name")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{company}/models/")
async def list_models_for_company(company: str):
    try:
        if mongo_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB connection not available")
        cursor = mongo_collection.find({"company_name": company})
        models = []
        async_unsupported = []  # placeholder to keep structure clear
        for doc in cursor:
            models.append({
                "_id": str(doc.get("_id")),
                "company_name": doc.get("company_name"),
                "product_name": doc.get("product_name"),
                "filename": doc.get("filename"),
                "uri": doc.get("uri"),
            })
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
1
@app.delete("/delete_manual/")
async def delete_manual(
    product_name: str = Form(...),
    product_code: str = Form(...)
):
    """
    Delete manual from both MongoDB and Qdrant DB using product_name and product_code metadata
    """
    try:
        if mongo_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB connection not available")
        
        # Find the document in MongoDB first
        mongo_doc = mongo_collection.find_one({
            "product_name": product_name,
            "filename": product_code  # product_code is stored as filename in MongoDB
        })
        
        if not mongo_doc:
            raise HTTPException(status_code=404, detail="Manual not found in database")
        
        # Get Cloudinary public_id for deletion
        cloudinary_public_id = mongo_doc.get("cloudinary_public_id")
        
        # Delete from MongoDB
        mongo_result = mongo_collection.delete_one({
            "product_name": product_name,
            "filename": product_code
        })
        
        if mongo_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Failed to delete from MongoDB")
        
        # Delete from Cloudinary if public_id exists
        cloudinary_deleted = False
        if cloudinary_public_id:
            try:
                cloudinary_deleted = delete_from_cloudinary(cloudinary_public_id)
                if cloudinary_deleted:
                    print(f"✅ File deleted from Cloudinary: {cloudinary_public_id}")
                else:
                    print(f"⚠️  Failed to delete from Cloudinary: {cloudinary_public_id}")
            except Exception as cloudinary_err:
                print(f"⚠️  Cloudinary deletion error: {cloudinary_err}")
        
        # Delete from Qdrant DB using metadata filter
        try:
            qdrant_client = QdrantClient(
                url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM"
            )
            
            # Try multiple approaches to find and delete the points
            deletion_successful = False
            
            # Approach 1: Use db_id from MongoDB document
            if mongo_doc and "_id" in mongo_doc:
                db_id = str(mongo_doc["_id"])
                print(f"🔍 Trying deletion with db_id: {db_id}")
                
                db_id_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="db_id",
                            match=models.MatchValue(value=db_id)
                        )
                    ]
                )
                
                search_result = qdrant_client.scroll(
                    collection_name="learn_vector3",
                    scroll_filter=db_id_filter,
                    limit=10
                )
                
                points_found = len(search_result[0]) if search_result[0] else 0
                print(f"📊 Found {points_found} points with db_id={db_id}")
                
                if points_found > 0:
                    delete_result = qdrant_client.delete(
                        collection_name="learn_vector3",
                        points_selector=models.FilterSelector(filter=db_id_filter)
                    )
                    print(f"✅ Deleted {points_found} points using db_id with operation ID: {delete_result.operation_id}")
                    deletion_successful = True
            
            # Approach 2: Use product_name and filename if db_id approach didn't work
            if not deletion_successful:
                print(f"🔍 Trying deletion with product_name and filename: {product_name}, {product_code}")
                
                qdrant_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.product_name",
                            match=models.MatchValue(value=product_name)
                        ),
                        models.FieldCondition(
                            key="metadata.filename",
                            match=models.MatchValue(value=product_code)
                        )
                    ]
                )
                
                search_result = qdrant_client.scroll(
                    collection_name="learn_vector3",
                    scroll_filter=qdrant_filter,
                    limit=10
                )
                
                points_found = len(search_result[0]) if search_result[0] else 0
                print(f"📊 Found {points_found} points with product_name={product_name}, filename={product_code}")
                
                if points_found > 0:
                    delete_result = qdrant_client.delete(
                        collection_name="learn_vector3",
                        points_selector=models.FilterSelector(filter=qdrant_filter)
                    )
                    print(f"\n\n\n\n\n\n\n\n\n\nn\n\n✅ Deleted {points_found} points using product_name/filename with operation ID: {delete_result.operation_id}\n\n\n\n\n\n\n\n\n\n\n\n\n")
                    deletion_successful = True
            
            if not deletion_successful:
                print("⚠️  No points found in Qdrant matching any filter criteria")
            
        except Exception as qdrant_err:
            print(f"⚠️  Qdrant deletion failed: {qdrant_err}")
            # Continue even if Qdrant deletion fails - MongoDB deletion succeeded
            # This ensures data consistency where MongoDB is the source of truth
        
        return {
            "message": f"Manual '{product_name}' ({product_code}) deleted successfully",
            "mongo_deleted": mongo_result.deleted_count,
            "cloudinary_deleted": cloudinary_deleted,
            "product_name": product_name,
            "product_code": product_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete operation failed: {str(e)}")