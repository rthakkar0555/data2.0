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

# Initialize NVIDIA NIM client lazily
client = None

def get_nvidia_client():
    """Get or initialize NVIDIA client lazily"""
    global client
    if client is None:
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
    return client

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
        
        nvidia_client = get_nvidia_client()
        if nvidia_client is None:
            raise Exception("NVIDIA NIM client not initialized")
        
        nvidia_client.chat.completions.create(
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
        elif company_name:
            # If only company_name is provided, filter by company only
            qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.company_name",
                        match=models.MatchValue(value=company_name)
                    )
                ]
            )

        # Perform search with filter first
        search_result = vector_db.similarity_search(query=query, k=8, filter=qdrant_filter)
        
        # If no results with filter, try with broader search but still within the same company
        if not search_result and qdrant_filter:
            logger.warning(f"No results with specific filter, trying broader search within company: {company_name}")
            # Try with just company filter if we had both company and product filters
            if company_name and product_code:
                company_only_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.company_name",
                            match=models.MatchValue(value=company_name)
                        )
                    ]
                )
                search_result = vector_db.similarity_search(query=query, k=8, filter=company_only_filter)
            
        # Only if still no results and we have a company filter, try without any filter
        if not search_result and company_name:
            logger.warning(f"No results found for company {company_name}, trying without filter")
            raise HTTPException(status_code=400, detail="No relevant information found in the uploaded documents.")
            
        if not search_result:
            logger.warning(f"No relevant documents found for query: {query}")
            raise HTTPException(status_code=400, detail="No relevant information found in the uploaded documents.")

        logger.info(f"Found {len(search_result)} search results")
        logger.debug(f"Search result: {search_result}")

        # Additional filtering: If we have both company_name and product_code, 
        # only include results that match both (to prevent cross-contamination)
        if company_name and product_code:
            filtered_results = []
            for result in search_result:
                result_company = result.metadata.get('company_name')
                result_product = result.metadata.get('product_code')
                if result_company == company_name and result_product == product_code:
                    filtered_results.append(result)
            
            if filtered_results:
                search_result = filtered_results
                logger.info(f"Filtered to {len(search_result)} results matching both company and product")
            else:
                logger.warning(f"No results match both company '{company_name}' and product '{product_code}'")

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
        - Use ## for major sections, ### for subsections
        - Use numbered lists (1., 2., 3.) for step-by-step instructions
        - Use bullet points (- or *) for features, tips, or general information
        - Use *bold text* for important warnings, key terms, or emphasis
        - Use code blocks for technical terms, model numbers, or specific values
        - Use > blockquotes for important safety warnings or notes
        - Separate each step with a blank line for better readability
        - Use horizontal rules (---) to separate major sections
        - Include page labels directly beside information in parentheses: (Page X)
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

        # Get response from NVIDIA NIM
        nvidia_client = get_nvidia_client()
        if nvidia_client is None:
            raise HTTPException(status_code=500, detail="NVIDIA NIM client not initialized")
        
        response = nvidia_client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.5,
            top_p=1,
            max_tokens=1024
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

        return {"response": ai_response}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))