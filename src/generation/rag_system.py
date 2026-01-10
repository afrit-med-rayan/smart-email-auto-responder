"""
RAG System (Retrieval-Augmented Generation)

Retrieves relevant context from knowledge base to augment LLM generation.
Uses vector embeddings for semantic search.
"""

from typing import Dict, List, Optional, Tuple
import json
import os


class RAGSystem:
    """
    Retrieval-Augmented Generation system.
    
    Uses vector database (FAISS) for semantic search to retrieve
    relevant context for email generation.
    """
    
    def __init__(
        self,
        knowledge_base_path: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        top_k: int = 3
    ):
        """
        Initialize RAG system.
        
        Args:
            knowledge_base_path: Path to knowledge base directory
            embedding_model: Sentence transformer model name
            top_k: Number of documents to retrieve
        """
        self.knowledge_base_path = knowledge_base_path
        self.embedding_model_name = embedding_model
        self.top_k = top_k
        
        self.index = None
        self.documents = []
        self.embeddings_model = None
        
        # Load knowledge base if path provided
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self._load_knowledge_base(knowledge_base_path)
    
    def retrieve(
        self,
        query: str,
        intent: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """
        Retrieve relevant documents for query.
        
        Args:
            query: Query text (email content)
            intent: Optional intent filter
            top_k: Number of documents to retrieve (overrides default)
            
        Returns:
            List of retrieved documents with scores
        """
        if not self.index or not self.documents:
            return []
        
        k = top_k or self.top_k
        
        try:
            # Encode query
            query_embedding = self._encode(query)
            
            # Search index
            distances, indices = self.index.search(query_embedding, k)
            
            # Get documents
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    
                    # Filter by intent if specified
                    if intent and doc.get("intent") != intent:
                        continue
                    
                    results.append({
                        "content": doc.get("content", ""),
                        "metadata": doc.get("metadata", {}),
                        "score": float(distances[0][i]),
                        "intent": doc.get("intent", ""),
                    })
            
            return results
        
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []
    
    def augment_prompt(
        self,
        email: Dict[str, str],
        intent: str,
        top_k: int = 3
    ) -> str:
        """
        Retrieve context and format for LLM prompt.
        
        Args:
            email: Email dictionary
            intent: Classified intent
            top_k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        # Build query from email
        query = f"{email.get('subject', '')} {email.get('body', '')}"
        
        # Retrieve documents
        docs = self.retrieve(query, intent=intent, top_k=top_k)
        
        if not docs:
            return ""
        
        # Format context
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"{i}. {doc['content']}")
        
        return "\n".join(context_parts)
    
    def add_document(
        self,
        content: str,
        intent: str = "general",
        metadata: Optional[Dict] = None
    ):
        """
        Add document to knowledge base.
        
        Args:
            content: Document content
            intent: Associated intent
            metadata: Additional metadata
        """
        doc = {
            "content": content,
            "intent": intent,
            "metadata": metadata or {}
        }
        
        self.documents.append(doc)
        
        # Re-index if index exists
        if self.index is not None:
            self._rebuild_index()
    
    def _load_knowledge_base(self, path: str):
        """
        Load knowledge base from directory.
        
        Args:
            path: Path to knowledge base directory
        """
        try:
            # Load documents from JSON files
            for filename in os.listdir(path):
                if filename.endswith('.json'):
                    filepath = os.path.join(path, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        if isinstance(data, list):
                            self.documents.extend(data)
                        elif isinstance(data, dict):
                            self.documents.append(data)
            
            print(f"Loaded {len(self.documents)} documents from knowledge base")
            
            # Build index
            if self.documents:
                self._build_index()
        
        except Exception as e:
            print(f"Failed to load knowledge base: {e}")
    
    def _build_index(self):
        """Build FAISS index from documents."""
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            # Load embedding model
            if self.embeddings_model is None:
                self.embeddings_model = SentenceTransformer(self.embedding_model_name)
            
            # Encode all documents
            contents = [doc.get("content", "") for doc in self.documents]
            embeddings = self.embeddings_model.encode(contents, show_progress_bar=False)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(embeddings).astype('float32'))
            
            print(f"Built FAISS index with {len(self.documents)} documents")
        
        except ImportError:
            print("FAISS or sentence-transformers not installed. RAG disabled.")
            print("Install with: pip install faiss-cpu sentence-transformers")
        except Exception as e:
            print(f"Failed to build index: {e}")
    
    def _rebuild_index(self):
        """Rebuild index after adding documents."""
        self.index = None
        self._build_index()
    
    def _encode(self, text: str):
        """
        Encode text to embedding.
        
        Args:
            text: Input text
            
        Returns:
            Embedding array
        """
        import numpy as np
        
        if self.embeddings_model is None:
            from sentence_transformers import SentenceTransformer
            self.embeddings_model = SentenceTransformer(self.embedding_model_name)
        
        embedding = self.embeddings_model.encode([text], show_progress_bar=False)
        return np.array(embedding).astype('float32')
    
    def save_knowledge_base(self, path: str):
        """
        Save knowledge base to file.
        
        Args:
            path: Output file path
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
        
        print(f"Saved knowledge base to {path}")


# Example usage
if __name__ == "__main__":
    # Create sample knowledge base
    rag = RAGSystem()
    
    # Add sample documents
    rag.add_document(
        content="Office hours are Monday and Wednesday 2-4 PM in Room 301.",
        intent="academic",
        metadata={"type": "policy"}
    )
    
    rag.add_document(
        content="Assignment extensions require approval from the professor at least 48 hours before the deadline.",
        intent="academic",
        metadata={"type": "policy"}
    )
    
    rag.add_document(
        content="Interview slots are available Monday-Friday 9 AM - 5 PM. Please confirm your availability.",
        intent="internship",
        metadata={"type": "template"}
    )
    
    # Test retrieval
    test_email = {
        "subject": "Office hours question",
        "body": "When are your office hours this week?"
    }
    
    context = rag.augment_prompt(test_email, intent="academic")
    print("Retrieved Context:")
    print(context)
