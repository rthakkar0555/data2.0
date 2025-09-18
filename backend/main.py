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
import qrcode
import json
import io
from PIL import Image

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
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")

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
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
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

def generate_qr_code(company_name: str, product_name: str, product_code: str = None) -> io.BytesIO:
    """
    Generate QR code with product information
    """
    try:
        # Data to encode in QR code
        data = {
            "company_name": company_name,
            "product_name": product_name,
            "product_code": product_code or product_name,
        }
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR code (1 is the smallest)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Sets the error correction level
            box_size=10,  # Size of each QR code pixel
            border=4,  # Thickness of the border
        )
        
        # Add data to the QR code
        qr.add_data(json.dumps(data))
        qr.make(fit=True)
        
        # Create an image from the QR code instance
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to BytesIO for upload
        qr_buffer = io.BytesIO()
        img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        return qr_buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR code generation failed: {str(e)}")

def upload_qr_to_cloudinary(qr_buffer: io.BytesIO, public_id: str) -> dict:
    """
    Upload QR code to Cloudinary and return the upload result
    """
    try:
        result = cloudinary.uploader.upload(
            qr_buffer,
            resource_type="image",  # For QR code images
            public_id=public_id,
            folder="qr_codes"  # Organize QR codes in a folder
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR code Cloudinary upload failed: {str(e)}")

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

        # Generate and upload QR code
        qr_uri = None
        qr_public_id = None
        try:
            qr_buffer = generate_qr_code(company_name, resolved_product_name, product_code)
            qr_public_id = f"{company_name}_{resolved_product_name}_qr"
            qr_result = upload_qr_to_cloudinary(qr_buffer, qr_public_id)
            qr_uri = qr_result["secure_url"]
            print(f"✅ QR code generated and uploaded to Cloudinary: {qr_uri}")
        except Exception as e:
            print(f"⚠️  QR code generation/upload failed: {e}")
            # Continue without QR code - the upload will still succeed

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
                "qr_uri": qr_uri,
                "qr_public_id": qr_public_id,
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

        # Create embeddings and store in Qdrant with improved batch handling
        try:
            embedding_model = NVIDIANIMEmbeddings()
            
            # Check if collection exists and create/recreate if needed
            qdrant_client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY")
            )
            
            collections = qdrant_client.get_collections()
            collection_exists = any(col.name == os.getenv("QDRANT_COLLECTION_NAME") for col in collections.collections)
            
            # Process documents in smaller batches to avoid timeout/memory issues
            batch_size = 50  # Smaller batch size for better reliability
            total_docs = len(split_docs)
            print(f"📊 Processing {total_docs} document chunks in batches of {batch_size}")
            
            if not collection_exists:
                print(f"🆕 Creating new {os.getenv('QDRANT_COLLECTION_NAME')} collection...")
                # Create collection for first time with first batch
                first_batch = split_docs[:batch_size]
                vector_store = QdrantVectorStore.from_documents(
                    documents=first_batch,
                    url=os.getenv("QDRANT_URL"),
                    api_key=os.getenv("QDRANT_API_KEY"),
                    collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                    embedding=embedding_model
                )
                print(f"✅ Created collection with first {len(first_batch)} documents")
                
                # Add remaining documents in batches
                remaining_docs = split_docs[batch_size:]
                if remaining_docs:
                    for i in range(0, len(remaining_docs), batch_size):
                        batch = remaining_docs[i:i + batch_size]
                        try:
                            vector_store.add_documents(batch)
                            print(f"✅ Added batch {i//batch_size + 2}: {len(batch)} documents")
                        except Exception as batch_err:
                            print(f"⚠️  Batch {i//batch_size + 2} failed: {batch_err}")
                            # Continue with next batch
            else:
                print(f"📚 Adding documents to existing {os.getenv('QDRANT_COLLECTION_NAME')} collection...")
                # Add to existing collection
                vector_store = QdrantVectorStore.from_existing_collection(
                    url=os.getenv("QDRANT_URL"),
                    api_key=os.getenv("QDRANT_API_KEY"),
                    collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                    embedding=embedding_model
                )
                
                # Add documents in batches
                for i in range(0, len(split_docs), batch_size):
                    batch = split_docs[i:i + batch_size]
                    try:
                        vector_store.add_documents(batch)
                        print(f"✅ Added batch {i//batch_size + 1}: {len(batch)} documents")
                    except Exception as batch_err:
                        print(f"⚠️  Batch {i//batch_size + 1} failed: {batch_err}")
                        # Continue with next batch
                
            print("✅ All documents processed for Qdrant storage")
                
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
                "qr_uri": qr_uri,
                "qr_public_id": qr_public_id,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_multiple_pdfs/")
async def upload_multiple_pdfs(
    files: list[UploadFile] = File(...),
    company_name: str = Form(...),
    product_name: str | None = Form(None),
    product_code: str | None = Form(None)
):
    """
    Upload multiple PDF files at once with improved batch processing
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Clear previous uploads
        for old_file in UPLOAD_DIR.iterdir():
            if old_file.is_file():
                old_file.unlink()
        uploaded_files.clear()
        
        # Determine product_name (fallback to product_code for backward compatibility)
        resolved_product_name = product_name or product_code
        if not resolved_product_name:
            raise HTTPException(status_code=400, detail="product_name or product_code is required")
        
        results = []
        all_split_docs = []
        
        # Process each file
        for file in files:
            try:
                # Save uploaded file temporarily for processing
                file_path = UPLOAD_DIR / file.filename
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
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
                    if file_path.exists():
                        file_path.unlink()
                    raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename} to Cloudinary: {str(e)}")

                # Generate and upload QR code
                qr_uri = None
                qr_public_id = None
                try:
                    qr_buffer = generate_qr_code(company_name, resolved_product_name, product_code)
                    qr_public_id = f"{company_name}_{resolved_product_name}_qr"
                    qr_result = upload_qr_to_cloudinary(qr_buffer, qr_public_id)
                    qr_uri = qr_result["secure_url"]
                    print(f"✅ QR code generated and uploaded to Cloudinary: {qr_uri}")
                except Exception as e:
                    print(f"⚠️  QR code generation/upload failed for {file.filename}: {e}")
                    # Continue without QR code - the upload will still succeed
                
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
                        "qr_uri": qr_uri,
                        "qr_public_id": qr_public_id,
                    }
                    insert_result = mongo_collection.insert_one(insert_doc)
                    inserted_id = str(insert_result.inserted_id)
                except Exception as db_err:
                    raise HTTPException(status_code=500, detail=f"Database insert failed for {file.filename}: {db_err}")
                
                # Extract core PDF metadata
                pdf_meta = {}
                try:
                    reader = PdfReader(str(file_path))
                    info = reader.metadata or {}
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
                    d.metadata["source"] = cloudinary_uri
                    d.metadata["db_id"] = inserted_id
                    d.metadata["filename"] = file.filename
                    # Merge core PDF metadata
                    for k, v in pdf_meta.items():
                        if v is not None:
                            d.metadata[k] = v
                
                # Chunk documents
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=500
                )
                split_docs = text_splitter.split_documents(documents=docs)
                
                # Add metadata to chunks
                for d in split_docs:
                    d.metadata = d.metadata or {}
                    d.metadata["product_name"] = resolved_product_name
                    d.metadata["filename"] = file.filename
                    d.metadata["db_id"] = inserted_id
                    d.metadata["company_name"] = company_name
                    d.metadata["product_code"] = product_code
                    d.metadata["source"] = cloudinary_uri
                    # Preserve page metadata and core PDF metadata
                    for k, v in pdf_meta.items():
                        if v is not None:
                            d.metadata[k] = v
                
                all_split_docs.extend(split_docs)
                uploaded_files.append(file.filename)
                
                # Clean up local file
                if file_path.exists():
                    file_path.unlink()
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "chunks": len(split_docs),
                    "db_id": inserted_id,
                    "cloudinary_uri": cloudinary_uri,
                    "qr_uri": qr_uri
                })
                
            except Exception as file_err:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(file_err)
                })
                # Clean up on error
                if 'file_path' in locals() and file_path.exists():
                    file_path.unlink()
        
        # Batch process all documents for Qdrant
        if all_split_docs:
            try:
                embedding_model = NVIDIANIMEmbeddings()
                
                qdrant_client = QdrantClient(
                    url=os.getenv("QDRANT_URL"),
                    api_key=os.getenv("QDRANT_API_KEY")
                )
                
                collections = qdrant_client.get_collections()
                collection_exists = any(col.name == os.getenv("QDRANT_COLLECTION_NAME") for col in collections.collections)
                
                batch_size = 50
                total_docs = len(all_split_docs)
                print(f"📊 Processing {total_docs} document chunks from {len(files)} files in batches of {batch_size}")
                
                if not collection_exists:
                    print(f"🆕 Creating new {os.getenv('QDRANT_COLLECTION_NAME')} collection...")
                    first_batch = all_split_docs[:batch_size]
                    vector_store = QdrantVectorStore.from_documents(
                        documents=first_batch,
                        url=os.getenv("QDRANT_URL"),
                        api_key=os.getenv("QDRANT_API_KEY"),
                        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                        embedding=embedding_model
                    )
                    print(f"✅ Created collection with first {len(first_batch)} documents")
                    
                    remaining_docs = all_split_docs[batch_size:]
                    if remaining_docs:
                        for i in range(0, len(remaining_docs), batch_size):
                            batch = remaining_docs[i:i + batch_size]
                            try:
                                vector_store.add_documents(batch)
                                print(f"✅ Added batch {i//batch_size + 2}: {len(batch)} documents")
                            except Exception as batch_err:
                                print(f"⚠️  Batch {i//batch_size + 2} failed: {batch_err}")
                else:
                    print(f"📚 Adding documents to existing {os.getenv('QDRANT_COLLECTION_NAME')} collection...")
                    vector_store = QdrantVectorStore.from_existing_collection(
                        url=os.getenv("QDRANT_URL"),
                        api_key=os.getenv("QDRANT_API_KEY"),
                        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                        embedding=embedding_model
                    )
                    
                    for i in range(0, len(all_split_docs), batch_size):
                        batch = all_split_docs[i:i + batch_size]
                        try:
                            vector_store.add_documents(batch)
                            print(f"✅ Added batch {i//batch_size + 1}: {len(batch)} documents")
                        except Exception as batch_err:
                            print(f"⚠️  Batch {i//batch_size + 1} failed: {batch_err}")
                
                print("✅ All documents processed for Qdrant storage")
                
            except Exception as qdrant_err:
                print(f"⚠️  Qdrant storage failed: {qdrant_err}")
        
        # Update current company
        global current_company_name
        current_company_name = company_name
        
        return {
            "message": f"Processed {len(files)} files",
            "files": uploaded_files,
            "results": results,
            "total_chunks": len(all_split_docs)
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
                "qr_uri": doc.get("qr_uri"),
            })
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
1
@app.post("/generate_qr_for_existing/")
async def generate_qr_for_existing():
    """
    Generate QR codes for existing entries that don't have them
    """
    try:
        if mongo_collection is None:
            raise HTTPException(status_code=500, detail="MongoDB connection not available")
        
        # Find documents without QR codes
        cursor = mongo_collection.find({"qr_uri": {"$exists": False}})
        updated_count = 0
        
        for doc in cursor:
            try:
                company_name = doc.get("company_name")
                product_name = doc.get("product_name")
                filename = doc.get("filename")
                
                if not all([company_name, product_name]):
                    continue
                
                # Generate QR code
                qr_buffer = generate_qr_code(company_name, product_name, filename)
                qr_public_id = f"{company_name}_{product_name}_qr"
                qr_result = upload_qr_to_cloudinary(qr_buffer, qr_public_id)
                qr_uri = qr_result["secure_url"]
                
                # Update document with QR code
                mongo_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"qr_uri": qr_uri, "qr_public_id": qr_public_id}}
                )
                
                updated_count += 1
                print(f"✅ Generated QR code for {company_name} - {product_name}: {qr_uri}")
                
            except Exception as e:
                print(f"⚠️  Failed to generate QR for {doc.get('company_name')} - {doc.get('product_name')}: {e}")
                continue
        
        return {
            "message": f"Generated QR codes for {updated_count} existing entries",
            "updated_count": updated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")

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
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY")
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
                    collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                    scroll_filter=db_id_filter,
                    limit=10
                )
                
                points_found = len(search_result[0]) if search_result[0] else 0
                print(f"📊 Found {points_found} points with db_id={db_id}")
                
                if points_found > 0:
                    delete_result = qdrant_client.delete(
                        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
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
                    collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                    scroll_filter=qdrant_filter,
                    limit=10
                )
                
                points_found = len(search_result[0]) if search_result[0] else 0
                print(f"📊 Found {points_found} points with product_name={product_name}, filename={product_code}")
                
                if points_found > 0:
                    delete_result = qdrant_client.delete(
                        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)