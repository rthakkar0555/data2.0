import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from qdrant_client.http import models       
from langchain_openai import OpenAIEmbeddings
from nvidia_embeddings import NVIDIANIMEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from openai import OpenAI
from langchain_nvidia_ai_endpoints.reranking import NVIDIARerank

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Disable pymongo debug logs
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
logging.getLogger("pymongo.pool").setLevel(logging.WARNING)
logging.getLogger("pymongo.server_selection").setLevel(logging.WARNING)

load_dotenv()

# Initialize NVIDIA NIM client lazily
client = None
reranker = None

def get_nvidia_client():
    """Get or initialize NVIDIA client lazily"""
    global client
    if client is None:
        try:
            client = OpenAI(
                base_url=os.getenv("NVIDIA_BASE_URL"),
                api_key=os.getenv("NVIDIA_API_KEY")
            )
            # List available models (non-blocking)
            try:
                resp = client.models.list()
                logger.debug(f"Available NVIDIA models: {[m.id for m in resp.data[:10]]}...")
            except Exception as list_error:
                logger.warning(f"Could not list NVIDIA models: {list_error}")
            
            # Skip the test request - let actual usage handle errors
            # This prevents initialization failure due to model availability issues
            logger.info("NVIDIA NIM client initialized (test skipped)")
        except Exception as e:
            logger.error(f"NVIDIA NIM client initialization failed: {e}")
            client = None
    return client

def get_nvidia_reranker():
    """Get or initialize NVIDIA reranker lazily"""
    global reranker
    if reranker is None:
        rerank_model = os.getenv("NVIDIA_RERANK_MODEL")
        if not rerank_model:
            logger.warning("⚠️ NVIDIA_RERANK_MODEL not set in environment variables. Reranking will be disabled.")
            return None
        try:
            reranker = NVIDIARerank(
                model=rerank_model,
                base_url=os.getenv("NVIDIA_BASE_URL"),
                nvidia_api_key=os.getenv("NVIDIA_API_KEY")
            )
            logger.info(f"✅ NVIDIA Reranker initialized successfully with model: {rerank_model}")
        except Exception as e:
            logger.error(f"❌ NVIDIA Reranker initialization failed: {e}")
            reranker = None
    return reranker

def get_available_nvidia_models():
    """Get list of available NVIDIA models for debugging"""
    try:
        nvidia_client = get_nvidia_client()
        if nvidia_client is None:
            return []
        resp = nvidia_client.models.list()
        return [m.id for m in resp.data]
    except Exception as e:
        logger.warning(f"Could not list NVIDIA models: {e}")
        return []

router = APIRouter()

# Global conversation memory storage for single user
# This will be expanded to support multiple users later
conversation_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"
)

class QueryRequest(BaseModel):
    query: str
    company_name: str
    product_name: str
    user_id: str | None = "default_user"  # For future multi-user support

@router.get("/health/")
async def health_check():
    health_status = {
        "status": "healthy",
        "qdrant": "unknown",
        "nvidia_client": "unknown",
        "nvidia_model_test": "unknown",
        "reranker": "unknown"
    }
    
    try:
        # Test Qdrant connection
        from qdrant_client import QdrantClient
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        qdrant.get_collections()
        health_status["qdrant"] = "available"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {str(e)}")
        health_status["qdrant"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check NVIDIA client initialization
        nvidia_client = get_nvidia_client()
        if nvidia_client is None:
            health_status["nvidia_client"] = "not initialized"
            health_status["status"] = "degraded"
        else:
            health_status["nvidia_client"] = "initialized"
            
            # Test model availability (non-blocking)
            try:
                nvidia_client.chat.completions.create(
                    model=os.getenv("NVIDIA_CHAT_MODEL"),
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=1
                )
                health_status["nvidia_model_test"] = "available"
            except Exception as model_error:
                logger.warning(f"NVIDIA model test failed: {model_error}")
                health_status["nvidia_model_test"] = f"error: {str(model_error)}"
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"NVIDIA client health check failed: {str(e)}")
        health_status["nvidia_client"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Test NVIDIA reranker
        nvidia_reranker = get_nvidia_reranker()
        if nvidia_reranker is None:
            health_status["reranker"] = "not available"
        else:
            health_status["reranker"] = "available"
    except Exception as e:
        logger.warning(f"Reranker health check failed: {str(e)}")
        health_status["reranker"] = f"error: {str(e)}"
    
    # Return 200 even if degraded, so monitoring can see the status
    return health_status

@router.post("/query/")
async def process_query(request: QueryRequest):
    try:
        query = request.query
        company_name = request.company_name
        product_name = request.product_name
        user_id = request.user_id or "default_user"
        
        # Debug logging for received parameters
        logger.info(f"\n\n\n\n\n\n\n\n\n\n=== RECEIVED PARAMETERS ===\n\n\n\n\n\n\n\n\n")
        logger.info(f"query: '{query}'")
        logger.info(f"company_name: '{company_name}' (type: {type(company_name)})")
        logger.info(f"product_name: '{product_name}' (type: {type(product_name)})")
        logger.info(f"user_id: '{user_id}'")
        logger.info(f"==========================")

        # Embedding
        embedding_model = NVIDIANIMEmbeddings()

        # Connect to Qdrant
        try:
            vector_db = QdrantVectorStore.from_existing_collection(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
                collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
                embedding=embedding_model
            )
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant collection: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"{str(e)} Vector database not available. Please ensure Qdrant is running and documents are uploaded.")

        # -----------------------------
        # ✅ Strict Metadata filtering - Both company_name and product_code required
        # -----------------------------
        
        # Check if both company_name and product_name are provided and not empty
        if not company_name or not product_name or company_name.strip() == "" or product_name.strip() == "":
            logger.warning(f"Missing or empty required parameters: company_name='{company_name}', product_name='{product_name}'")
            raise HTTPException(status_code=400, detail="Both company_name and product_name are required to search for context.")
        
        logger.info(f"\n\n\n\n\n\n\n\n\n\ncompany_name: {company_name}, product_name: {product_name}\n\n\n\n\n\n\n\n\n\n")
        
        # Create strict filter requiring both company_name and product_name
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.company_name",
                    match=models.MatchValue(value=company_name)
                ),
                models.FieldCondition(
                    key="metadata.product_name",
                    match=models.MatchValue(value=product_name)
                )
            ]
        )
        
        # Debug logging for filter
        logger.info(f"Using filter: company_name='{company_name}', product_name='{product_name}'")
        logger.info(f"Filter object: {qdrant_filter}")
        
        # Perform search with strict filter - get more results for reranking
        search_result = vector_db.similarity_search(query=query, k=15, filter=qdrant_filter)
        
        # Debug logging
        logger.info(f"Initial search result count: {len(search_result) if search_result else 0}")
        if search_result:
            logger.info(f"First result metadata: {search_result[0].metadata}")
            logger.info(f"First result company: {search_result[0].metadata.get('company_name')}")
            logger.info(f"First result product: {search_result[0].metadata.get('product_name')}")
        
        # If no results found with strict filter, return "no context found"
        if not search_result:
            logger.warning(f"No context found for company_name='{company_name}' and product_name='{product_name}'")
            raise HTTPException(status_code=400, detail="No context found for the specified company and product combination.")

        logger.info(f"Found {len(search_result)} search results before reranking")
        
        # Apply NVIDIA reranking for better context
        try:
            nvidia_reranker = get_nvidia_reranker()
            if nvidia_reranker is not None:
                logger.info("🔄 Applying NVIDIA reranking to improve context relevance...")
                reranked_chunks = nvidia_reranker.compress_documents(
                    query=query,
                    documents=search_result
                )
                # Take top 8 reranked results
                search_result = reranked_chunks[:8]
                logger.info(f"✅ Reranking completed. Using top {len(search_result)} most relevant chunks")
            else:
                logger.warning("⚠️ NVIDIA reranker not available, using original search results")
        except Exception as rerank_error:
            logger.error(f"❌ Reranking failed: {rerank_error}")
            logger.info("🔄 Continuing with original search results")
        
        logger.info(f"Final result count: {len(search_result)}")
        logger.debug(f"Final search result: {search_result}")

        # Format context (include metadata for debugging)
        context = "\n\n\n".join([
            f"page_content: {result.page_content}\n"
            f"page_label: {result.metadata.get('page_label')}\n"
            f"company_name: {result.metadata.get('company_name')}\n"
            f"product_name: {result.metadata.get('product_name')}\n"
            f"source: {result.metadata.get('source')}\n"
            f"total_pages: {result.metadata.get('total_pages')}\n"
            f"page: {result.metadata.get('page')}"
            for result in search_result
        ])
        
        logger.info(f"Context length: {len(context)} characters")
        
        # Collect unique PDF URLs from search results
        pdf_urls = set()
        for result in search_result:
            source = result.metadata.get('source')
            if source:
                pdf_urls.add(source)
        
        # Enhanced System prompt for human-like expert guidance
        SYSTEM_PROMPT = f"""
        You are an experienced technical expert and guide who specializes in equipment manuals, troubleshooting, and maintenance. Your role is to provide helpful, human-like guidance based on the technical documentation provided.

        ## Your Expertise & Approach:
        - You're a knowledgeable expert who understands both the technical aspects and the user's practical needs
        - You communicate like a helpful colleague who has years of experience with this equipment
        - You provide context and explain the "why" behind instructions, not just the "what"
        - You anticipate common issues and provide proactive tips
        - You use conversational language while maintaining technical accuracy

        ## Response Guidelines:
        - **Source Material**: Use ONLY the information provided in the Context below. Never add external knowledge or assumptions.
        - **Missing Information**: If the requested information isn't in the Context, respond: "I couldn't find specific information about that in the available documentation. You might want to check with the manufacturer or your technical support team."
        - **Scope**: Focus on manual guidance, troubleshooting, maintenance, and usage. For unrelated questions, say: "I specialize in equipment guidance and troubleshooting. I'd be happy to help with questions about usage, maintenance, or technical issues."
        - **Safety First**: Always prioritize safety warnings and include power-off/unplugging steps when mentioned in the documentation.
        - **Page References**: Include page labels in parentheses (Page X) for all information sourced from the documentation.

        ## Communication Style:
        - Start responses with understanding and empathy (e.g., "I understand you're dealing with...", "Let me help you with...")
        - Use conversational transitions like "Here's what you need to know...", "The key thing to remember is...", "You'll want to..."
        - Explain the reasoning behind steps when helpful
        - Provide context about why certain steps are important
        - Use encouraging language for troubleshooting steps
        - End with helpful next steps or additional considerations

        ## Formatting Requirements:
        - Use clear Markdown structure with proper hierarchy
        - Start with a main heading using # (single hash)
        - only give the answer of the query, do not give any other information 
        - the ans should be in the same langage as user and if user specificaly has mentioned to give ans in hindi or gujrati then give ans
        - Use ## for major sections, ### for subsections
        - Use numbered lists (1., 2., 3.) for step-by-step instructions
        - Use bullet points (- or *) for features, tips, or general information
        - Use *bold text* for important warnings, key terms, or emphasis
        - Use code blocks for technical terms, model numbers, or specific values
        - Use > blockquotes for important safety warnings or notes
        - Separate each step with a blank line for better readability
        - Use horizontal rules (---) to separate major sections
        - must Include page labels directly beside information in parentheses: (Page X)
        - DO NOT include a "Reference Documents" section - this will be added automatically
        - NEVER include PDF URLs inline with content or at the end

        ## Example Response Structure:
        # [Main Topic] - Expert Guidance

        ## Understanding Your Situation
        Brief empathetic introduction that acknowledges the user's need (Page X).

        ## What You Need to Know
        Key information and context about the topic (Page Y).

        ## Step-by-Step Solution
        1. *First step* - Detailed description with explanation of why this step matters (Page Z)

        2. *Second step* - Detailed description with helpful tips (Page A)

        3. *Third step* - Detailed description with common pitfalls to avoid (Page B)

        ## Pro Tips & Important Notes
        - Helpful tip 1 with explanation (Page C)
        - Helpful tip 2 with context (Page D)

        > *Safety First*: Important safety information with explanation of risks (Page E)

        ## What to Do Next
        Guidance on follow-up steps or when to seek additional help.

        ---
        
        Context:
        {context}
        """

        # Get conversation history from memory
        chat_history = conversation_memory.chat_memory.messages
        
        # Prepare messages for LLM including conversation history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add conversation history
        for message in chat_history:
            if isinstance(message, HumanMessage):
                messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                messages.append({"role": "assistant", "content": message.content})
        
        # Add current user query
        messages.append({"role": "user", "content": query})
        
        logger.info(f"Total messages in conversation: {len(messages)}")
        
        # Get response from NVIDIA NIM
        nvidia_client = get_nvidia_client()
        if nvidia_client is None:
            raise HTTPException(status_code=500, detail="NVIDIA NIM client not initialized")
        
        nvidia_model = os.getenv("NVIDIA_CHAT_MODEL")
        if not nvidia_model:
            raise HTTPException(status_code=500, detail="NVIDIA_CHAT_MODEL environment variable not set")
        
        try:
            response = nvidia_client.chat.completions.create(
                model=nvidia_model,
                messages=messages,
                temperature=0.8,
                top_p=1,
                max_tokens=1024
            )
        except Exception as api_error:
            error_msg = str(api_error)
            logger.error(f"NVIDIA API error: {error_msg}", exc_info=True)
            
            # Check for specific error types
            if "404" in error_msg or "Not Found" in error_msg:
                # Try to get available models for better error message
                available_models = get_available_nvidia_models()
                available_nvidia_models = [m for m in available_models if m.startswith("nvidia/")][:10]
                
                error_detail = f"NVIDIA model '{nvidia_model}' not found or not available for your account."
                if available_nvidia_models:
                    error_detail += f" Available NVIDIA models include: {', '.join(available_nvidia_models)}"
                error_detail += " Please check your NVIDIA API configuration and model name."
                
                raise HTTPException(
                    status_code=404,
                    detail=error_detail
                )
            elif "401" in error_msg or "Unauthorized" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="NVIDIA API authentication failed. Please check your NVIDIA_API_KEY."
                )
            elif "403" in error_msg or "Forbidden" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied to NVIDIA API. Please check your account permissions."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"NVIDIA API error: {error_msg}"
                )

        # Get the AI response
        ai_response = response.choices[0].message.content
        
        # Append PDF URLs at the end if they exist and AI hasn't already added them
        if pdf_urls and "## Reference Documents" not in ai_response:
            pdf_links_section = "\n\n## Reference Documents\n"
            for pdf_url in pdf_urls:
                # Extract filename from URL for display
                filename = pdf_url.split('/')[-1] if '/' in pdf_url else pdf_url
                pdf_links_section += f"[{filename}]({pdf_url})\n\n"
            
            ai_response += pdf_links_section

        # Save conversation to memory
        conversation_memory.chat_memory.add_user_message(query)
        conversation_memory.chat_memory.add_ai_message(ai_response)
        
        logger.info(f"Conversation saved to memory. Total messages: {len(conversation_memory.chat_memory.messages)}")

        return {"response": ai_response}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/clear/")
async def clear_conversation():
    """Clear the conversation memory"""
    try:
        conversation_memory.clear()
        logger.info("Conversation memory cleared")
        return {"message": "Conversation memory cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation memory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/history/")
async def get_conversation_history():
    """Get the current conversation history"""
    try:
        messages = conversation_memory.chat_memory.messages
        conversation_data = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation_data.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                conversation_data.append({"role": "assistant", "content": message.content})
        
        return {
            "total_messages": len(messages),
            "conversation": conversation_data
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/search/{company_name}/{product_name}")
async def debug_search(company_name: str, product_name: str, query: str = "test"):
    """Debug endpoint to test search without API processing"""
    try:
        logger.info(f"=== DEBUG SEARCH ===")
        logger.info(f"company_name: '{company_name}'")
        logger.info(f"product_name: '{product_name}'")
        logger.info(f"query: '{query}'")
        
        # Initialize embedding model
        embedding_model = NVIDIANIMEmbeddings()
        
        # Connect to Qdrant
        vector_db = QdrantVectorStore.from_existing_collection(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
            embedding=embedding_model
        )
        
        # Create strict filter
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.company_name",
                    match=models.MatchValue(value=company_name)
                ),
                models.FieldCondition(
                    key="metadata.product_name",
                    match=models.MatchValue(value=product_name)
                )
            ]
        )
        
        logger.info(f"Filter: {qdrant_filter}")
        
        # Perform search - get more results for reranking
        search_result = vector_db.similarity_search(query=query, k=15, filter=qdrant_filter)
        
        logger.info(f"Initial search result count: {len(search_result) if search_result else 0}")
        
        # Apply reranking if available
        try:
            nvidia_reranker = get_nvidia_reranker()
            if nvidia_reranker is not None:
                logger.info("🔄 Applying NVIDIA reranking for debug...")
                reranked_chunks = nvidia_reranker.compress_documents(
                    query=query,
                    documents=search_result
                )
                search_result = reranked_chunks[:8]  # Take top 8
                logger.info(f"✅ Reranking completed. Using top {len(search_result)} results")
            else:
                logger.warning("⚠️ NVIDIA reranker not available for debug")
        except Exception as rerank_error:
            logger.error(f"❌ Reranking failed in debug: {rerank_error}")
        
        logger.info(f"Final search result count: {len(search_result) if search_result else 0}")
        
        if search_result:
            result_data = []
            for i, result in enumerate(search_result):
                result_info = {
                    "index": i,
                    "company_name": result.metadata.get('company_name'),
                    "product_name": result.metadata.get('product_name'),
                    "source": result.metadata.get('source'),
                    "page": result.metadata.get('page'),
                    "content_preview": result.page_content[:100] + "..." if len(result.page_content) > 100 else result.page_content
                }
                result_data.append(result_info)
                logger.info(f"Result {i}: company='{result.metadata.get('company_name')}', product='{result.metadata.get('product_name')}'")
            
            return {
                "status": "success",
                "count": len(search_result),
                "results": result_data
            }
        else:
            # Let's also try without filter to see what's available
            logger.info("No results with filter, checking what's available...")
            all_results = vector_db.similarity_search(query=query, k=20)
            
            available_data = []
            companies = set()
            products = set()
            company_product_combinations = set()
            
            for result in all_results:
                company = result.metadata.get('company_name', 'N/A')
                product = result.metadata.get('product_name', 'N/A')
                companies.add(company)
                products.add(product)
                company_product_combinations.add(f"{company}|{product}")
                
                available_data.append({
                    "company_name": company,
                    "product_name": product,
                    "source": result.metadata.get('source'),
                    "page": result.metadata.get('page'),
                    "content_preview": result.page_content[:50] + "..." if len(result.page_content) > 50 else result.page_content
                })
            
            # Check for exact matches with different cases
            exact_matches = []
            for combo in company_product_combinations:
                stored_company, stored_product = combo.split('|')
                if (stored_company.lower() == company_name.lower() and 
                    stored_product.lower() == product_name.lower()):
                    exact_matches.append(f"Found case-insensitive match: '{stored_company}' + '{stored_product}'")
            
            return {
                "status": "no_results_with_filter",
                "requested": {"company_name": company_name, "product_name": product_name},
                "available_companies": sorted(list(companies)),
                "available_products": sorted(list(products)),
                "company_product_combinations": sorted(list(company_product_combinations)),
                "exact_matches": exact_matches,
                "sample_data": available_data[:10]  # First 10 results
            }
            
    except Exception as e:
        logger.error(f"Debug search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/all-data")
async def debug_all_data():
    """Debug endpoint to show all available data in the collection"""
    try:
        logger.info("=== DEBUG ALL DATA ===")
        
        # Initialize embedding model
        embedding_model = NVIDIANIMEmbeddings()
        
        # Connect to Qdrant
        vector_db = QdrantVectorStore.from_existing_collection(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
            embedding=embedding_model
        )
        
        # Get all data without any filter
        all_results = vector_db.similarity_search(query="test", k=50)
        
        logger.info(f"Total documents found: {len(all_results)}")
        
        companies = set()
        products = set()
        company_product_combinations = set()
        all_data = []
        
        for i, result in enumerate(all_results):
            company = result.metadata.get('company_name', 'N/A')
            product = result.metadata.get('product_name', 'N/A')
            companies.add(company)
            products.add(product)
            company_product_combinations.add(f"{company}|{product}")
            
            all_data.append({
                "index": i,
                "company_name": company,
                "product_name": product,
                "source": result.metadata.get('source'),
                "page": result.metadata.get('page'),
                "content_preview": result.page_content[:100] + "..." if len(result.page_content) > 100 else result.page_content
            })
        
        return {
            "total_documents": len(all_results),
            "unique_companies": sorted(list(companies)),
            "unique_products": sorted(list(products)),
            "company_product_combinations": sorted(list(company_product_combinations)),
            "all_data": all_data
        }
        
    except Exception as e:
        logger.error(f"Debug all data error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/reranking/{company_name}/{product_name}")
async def debug_reranking(company_name: str, product_name: str, query: str = "test query"):
    """Debug endpoint to test reranking functionality"""
    try:
        logger.info(f"=== DEBUG RERANKING ===")
        logger.info(f"company_name: '{company_name}'")
        logger.info(f"product_name: '{product_name}'")
        logger.info(f"query: '{query}'")
        
        # Initialize embedding model
        embedding_model = NVIDIANIMEmbeddings()
        
        # Connect to Qdrant
        vector_db = QdrantVectorStore.from_existing_collection(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
            embedding=embedding_model
        )
        
        # Create strict filter
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.company_name",
                    match=models.MatchValue(value=company_name)
                ),
                models.FieldCondition(
                    key="metadata.product_name",
                    match=models.MatchValue(value=product_name)
                )
            ]
        )
        
        # Get initial search results
        initial_results = vector_db.similarity_search(query=query, k=15, filter=qdrant_filter)
        logger.info(f"Initial search results: {len(initial_results)}")
        
        if not initial_results:
            return {
                "status": "no_results",
                "message": "No documents found for the specified company and product"
            }
        
        # Test reranking
        reranking_info = {
            "reranker_available": False,
            "reranking_successful": False,
            "error": None
        }
        
        try:
            nvidia_reranker = get_nvidia_reranker()
            if nvidia_reranker is not None:
                reranking_info["reranker_available"] = True
                logger.info("Testing reranking...")
                
                reranked_chunks = nvidia_reranker.compress_documents(
                    query=query,
                    documents=initial_results
                )
                
                reranking_info["reranking_successful"] = True
                logger.info(f"Reranking successful. Got {len(reranked_chunks)} reranked chunks")
                
                # Compare original vs reranked order
                original_order = [i for i in range(len(initial_results))]
                reranked_order = []
                
                for reranked_chunk in reranked_chunks:
                    for i, original_chunk in enumerate(initial_results):
                        if (reranked_chunk.page_content == original_chunk.page_content and 
                            reranked_chunk.metadata == original_chunk.metadata):
                            reranked_order.append(i)
                            break
                
                return {
                    "status": "success",
                    "initial_count": len(initial_results),
                    "reranked_count": len(reranked_chunks),
                    "reranking_info": reranking_info,
                    "original_order": original_order,
                    "reranked_order": reranked_order,
                    "order_changed": original_order != reranked_order,
                    "sample_results": [
                        {
                            "index": i,
                            "content_preview": chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content,
                            "metadata": chunk.metadata
                        }
                        for i, chunk in enumerate(reranked_chunks[:5])  # Show top 5
                    ]
                }
            else:
                reranking_info["error"] = "NVIDIA reranker not initialized"
                logger.warning("NVIDIA reranker not available")
                
        except Exception as rerank_error:
            reranking_info["error"] = str(rerank_error)
            logger.error(f"Reranking test failed: {rerank_error}")
        
        return {
            "status": "reranking_failed",
            "initial_count": len(initial_results),
            "reranking_info": reranking_info,
            "sample_results": [
                {
                    "index": i,
                    "content_preview": chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content,
                    "metadata": chunk.metadata
                }
                for i, chunk in enumerate(initial_results[:5])  # Show top 5 original results
            ]
        }
        
    except Exception as e:
        logger.error(f"Debug reranking error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))