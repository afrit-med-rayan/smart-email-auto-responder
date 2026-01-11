"""
RAG System Module

Retrieval Augmented Generation using FAISS and Sentence Transformers.
Retrieves relevant context (FAQs, templates, past emails) to augment generation.
"""

import os
import logging
import json
from typing import List, Dict, Any
from src.config_loader import config

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    HAS_RAG_DEPS = True
except ImportError:
    HAS_RAG_DEPS = False

logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG system for knowledge retrieval."""
    
    def __init__(self):
        self.index = None
        self.documents = []
        self.model = None
        
        if HAS_RAG_DEPS and config:
            try:
                model_name = config.models["embeddings"].name
                logger.info(f"Loading Embedding Model: {model_name}")
                self.model = SentenceTransformer(model_name)
                
                # Initialize FAISS index
                # 384 dimensions for all-MiniLM-L6-v2
                self.dimension = 384 
                self.index = faiss.IndexFlatL2(self.dimension)
                
                # Load KB if exists
                self._load_knowledge_base()
                
            except Exception as e:
                logger.warning(f"Failed to init RAG: {e}")

    def retrieve(self, query: str, k: int = 3) -> List[str]:
        """
        Retrieve top-k relevant documents.
        
        Args:
            query: Search query (email text)
            k: Number of results
            
        Returns:
            List of document text
        """
        if not self.model or not self.index or self.index.ntotal == 0:
            return []
            
        try:
            # Encode query
            query_vector = self.model.encode([query])
            
            # Search
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.documents):
                    results.append(self.documents[idx])
                    
            return results
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    def add_document(self, text: str):
        """Add document to index."""
        if not self.model:
            return
            
        try:
            vector = self.model.encode([text])
            if self.index is None:
                self.index = faiss.IndexFlatL2(vector.shape[1])
                
            self.index.add(vector)
            self.documents.append(text)
            
        except Exception as e:
            logger.error(f"Indexing error: {e}")

    def _load_knowledge_base(self):
        """Load initial KB from data file."""
        kb_path = os.path.join(config.paths.data_dir, "knowledge_base.json")
        if os.path.exists(kb_path):
            try:
                with open(kb_path, "r") as f:
                    docs = json.load(f)
                    for doc in docs:
                         self.add_document(doc["content"])
                logger.info(f"Loaded {len(docs)} documents into RAG index")
            except Exception as e:
                logger.error(f"Failed to load KB: {e}")

# Example usage
if __name__ == "__main__":
    rag = RAGSystem()
    rag.add_document("The university policy for extensions requires a 24h notice.")
    rag.add_document("Office hours are Mon-Wed 10-12.")
    
    print(rag.retrieve("Can I get an extension?"))
