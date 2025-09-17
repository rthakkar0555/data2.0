"""
Custom NVIDIA NIM Embeddings class for LangChain compatibility
"""

from typing import List, Optional, Any
from openai import OpenAI
import os
from langchain_core.embeddings import Embeddings

class NVIDIANIMEmbeddings(Embeddings):
    """Custom embeddings class for NVIDIA NIM API that inherits from LangChain Embeddings"""
    
    def __init__(self):
        super().__init__()
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key="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"
        )
        self.model = "nvidia/nv-embed-v1"
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error embedding query: {e}")
            raise e
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents with batch processing"""
        embeddings = []
        batch_size = 100  # Process in batches to avoid API limits
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            try:
                # Use batch API call for better performance
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts
                )
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Batch embedding failed, falling back to individual processing: {e}")
                # Fallback to individual processing if batch fails
                for text in batch_texts:
                    try:
                        embeddings.append(self.embed_query(text))
                    except Exception as individual_error:
                        print(f"Error embedding individual text: {individual_error}")
                        # Add zero vector as fallback
                        embeddings.append([0.0] * 1024)  # Assuming 1024 dimensions
        return embeddings
    
    def _embed_query(self, text: str) -> List[float]:
        """Internal method for embedding queries"""
        return self.embed_query(text)
    
    def _embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Internal method for embedding documents"""
        return self.embed_documents(texts)
