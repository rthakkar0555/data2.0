import os
from qdrant_client.http import models
from nvidia_embeddings import NVIDIANIMEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv

load_dotenv()

def test_retrieval(company_name, product_code, query):
    """Test retrieval with strict filtering"""
    
    # Check if both company_name and product_code are provided
    if not company_name or not product_code:
        return "Both company_name and product_code are required to search for context."
    
    # Initialize embedding model
    embedding_model = NVIDIANIMEmbeddings()
    
    # Connect to Qdrant
    vector_db = QdrantVectorStore.from_existing_collection(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
        embedding=embedding_model
    )
    
    # Create strict filter requiring both company_name and product_code
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
    
    # Perform search with strict filter
    search_result = vector_db.similarity_search(query=query, k=8, filter=qdrant_filter)
    print(search_result)
    # If no results found with strict filter, return "no context found"
    if not search_result:
        return "No context found for the specified company and product combination."
    
    return f"Found {len(search_result)} results for {company_name} - {product_code}"

# Test examples
if __name__ == "__main__":
    # Test with valid parameters
    result1 = test_retrieval("Asus", "tuf_f15", "saftey precautions")
    print(f"Test 1: {result1}")
    
    