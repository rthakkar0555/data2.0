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
        """Embed multiple documents"""
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_query(text))
        return embeddings
    
    def _embed_query(self, text: str) -> List[float]:
        """Internal method for embedding queries"""
        return self.embed_query(text)
    
    def _embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Internal method for embedding documents"""
        return self.embed_documents(texts)
