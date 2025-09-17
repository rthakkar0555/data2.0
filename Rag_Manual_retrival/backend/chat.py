import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from qdrant_client.http import models       
from langchain_openai import OpenAIEmbeddings
from nvidia_embeddings import NVIDIANIMEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize NVIDIA NIM client with error handling
try:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )
    # Test the client
    client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        messages=[{"role": "user", "content": "Test"}],
        max_tokens=1
    )
    print("NVIDIA NIM client initialized successfully")
except Exception as e:
    print(f"NVIDIA NIM client initialization failed: {e}")
    client = None

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    company_name: str | None = None
    product_code: str | None = None

@router.get("/health/")
async def health_check():
    try:
        from qdrant_client import QdrantClient
        qdrant = QdrantClient(
            url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM"
        )
        qdrant.get_collections()  # Test Qdrant connection
        
        if client is None:
            raise Exception("NVIDIA NIM client not initialized")
        
        client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1
        )  # Test NVIDIA NIM connection
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/query/")
async def process_query(request: QueryRequest):
    try:
        query = request.query
        company_name = request.company_name
        product_code = request.product_code
        logger.info(f"\n\n\n\ncompany_name: {company_name}, product_code: {product_code}\n\n\n\n")

        # Embedding
        embedding_model = NVIDIANIMEmbeddings()

        # Connect to Qdrant
        try:
            vector_db = QdrantVectorStore.from_existing_collection(
                url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM",
                collection_name="learn_vector3",
                embedding=embedding_model
            )
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant collection: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"{str(e)} Vector database not available. Please ensure Qdrant is running and documents are uploaded.")

        # -----------------------------
        # ✅ Metadata filtering
        # -----------------------------
        qdrant_filter = None
        if company_name and product_code:
            # Use dict-based filter (LangChain → Qdrant payload filter)
           qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.company_name",
                        match=models.MatchValue(value=company_name)
                    ),
                    models.FieldCondition(
                        key="metadata.product_code",
                        match=models.MatchValue(value=product_code)
                    )
                ]
            )

        # Perform search
        search_result = vector_db.similarity_search(query=query, k=5, filter=qdrant_filter)

        if not search_result and qdrant_filter:
            # fallback: retry without filter
            logger.warning(f"\n\n\n\n\n\nNo results with filter, retrying without filter for query: {query}")
            search_result = vector_db.similarity_search(query=query, k=5)

        if not search_result:
            logger.warning(f"No relevant documents found for query: {query}")
            raise HTTPException(status_code=400, detail="No relevant information found in the uploaded documents.")

        logger.debug(f"Search result: {search_result}")

        # Format context (include metadata for debugging)
        context = "\n\n\n".join([
            f"page_content: {result.page_content}\n"
            f"page_label: {result.metadata.get('page_label')}\n"
            f"company_name: {result.metadata.get('company_name')}\n"
            f"product_code: {result.metadata.get('product_code')}\n"
            f"source: {result.metadata.get('source')}\n"
            f"total_pages: {result.metadata.get('total_pages')}\n"
            f"page: {result.metadata.get('page')}"
            for result in search_result
        ])
        
        # System prompt
        SYSTEM_PROMPT = f"""
        Role: You are "Companion AI" — provide usage, troubleshooting, parts, and maintenance guidance strictly from the provided Context.

        Hard rules:
        - Answer ONLY using the information in the Context below. Do not add outside knowledge, guesses, or general guidance.
        - If the requested information is not in Context, say exactly: "Not found in Context."
        - Answer in English. Keep tone clear, empathetic, and concise.
        - For every fact or step derived from Context, append a citation: [src: page_label=<PAGE_LABEL> pdf_uri=<PDF_URI>].
        - Prioritize safety: warn before risky steps; include unplug/power-off where indicated by Context.
        - if the question is not related about manual guidandce usage troubleshooting or maintenance then say i am cant help with that.
        - if question is about troubleshooting or maintence then provide step by step guidance.
        Context:
        {context}
        """

        # Get response from NVIDIA NIM
        if client is None:
            raise HTTPException(status_code=500, detail="NVIDIA NIM client not initialized")
        
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.5,
            top_p=1,
            max_tokens=1024
        )

        return {"response": response.choices[0].message.content}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
