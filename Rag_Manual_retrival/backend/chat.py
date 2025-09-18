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
            search_result = vector_db.similarity_search(query=query, k=8, filter=None)
            
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
        
        # System prompt
        SYSTEM_PROMPT = f"""
        Role: You are "Companion AI" — provide usage, troubleshooting, parts, and maintenance guidance strictly from the provided Context.

        Hard rules:
        - Answer ONLY using the information in the Context below. Do not add outside knowledge, guesses, or general guidance.
        - If the requested information is not in Context, say exactly: "I couldn't find relevant information in the available manuals for your query."
        - Answer in English. Keep tone clear, empathetic, and concise.
        - For every fact or step derived from Context, include the page label directly beside the information in parentheses: (Page X)
        - Prioritize safety: warn before risky steps; include unplug/power-off where indicated by Context.
        - If the question is not related to manual guidance, usage, troubleshooting or maintenance then say "I can't help with that. I only provide guidance related to manual usage, troubleshooting, and maintenance."
        - If question is about troubleshooting or maintenance then provide step by step guidance.
        - IMPORTANT: Only provide information that is directly relevant to the user's query. Do not include information about other products or manuals that are not related to the specific question asked.
        - Focus on the most relevant information from the context that directly answers the user's query.
        - Do not search in web and do not provide any information that is not in the context.

        CRITICAL FORMATTING REQUIREMENTS:
        - Use proper Markdown structure with clear hierarchy
        - Start with a main heading using # (single hash)
        - Use ## for major sections, ### for subsections
        - Use numbered lists (1., 2., 3.) for step-by-step instructions
        - Use bullet points (- or *) for features, tips, or general information
        - Use *bold text* for important warnings, key terms, or emphasis
        - Use code blocks for technical terms, model numbers, or specific values
        - Use > blockquotes for important safety warnings or notes
        - Separate each step with a blank line for better readability
        - Use horizontal rules (---) to separate major sections
        - Ensure proper spacing between all elements
        - IMPORTANT: Include page labels directly beside the information in parentheses: (Page X)
        - DO NOT include a "Reference Documents" section in your response - this will be added automatically
        - NEVER include PDF URLs inline with the content or at the end of your response

        Example structure:
        # Main Topic

        ## Introduction
        Brief overview paragraph (Page 1).

        ## Step-by-Step Instructions
        1. *First step* - Detailed description (Page 6)

        2. *Second step* - Detailed description (Page 7)

        3. *Third step* - Detailed description (Page 8)

        ## Important Notes
        - Important point 1 (Page 10)
        - Important point 2 (Page 11)

        > *Safety Warning*: Important safety information here (Page 5)
        
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