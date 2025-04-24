# app/chatbot/vectordb.py

import os
import json
import numpy as np
import faiss
from typing import Dict, List, Tuple
from app.chatbot.model import TinyLlamaChatModel

class VectorDB:
    def __init__(self, vector_dim: int, db_path: str = None, chatbot=None):
        """
        Initialize the vector database.
        
        Args:
            vector_dim: Dimension of the vectors
            db_path: Optional path to load from a saved database
        """
        self.vector_dim = vector_dim
        self.index = faiss.IndexFlatL2(vector_dim)
        self.chunks = []
        self.metadata = []
        self.chatbot = chatbot
        
        if db_path and os.path.exists(db_path):
            self.load(db_path)
    
    def add_text(self, text: str, metadata: Dict = None):
        """
        Add text to the vector database by chunking and embedding it.
        
        Args:
            text: Text to add to the database
            metadata: Optional metadata associated with the text
        """
        if metadata is None:
            metadata = {"source": "chat"}
            
        # Create chunks from text
        chunks = self._create_chunks(text, self.chatbot)
        
        # Add each chunk to the database
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = str(i)
            self._add_chunk(chunk, chunk_metadata)
    
    def _create_chunks(self, text: str, chatbot=None) -> List[str]:
        """
        Split text into chunks based on word count.
        
        Args:
            text: Text to split into chunks
            chatbot: Optional chatbot with config to get chunk size
            
        Returns:
            List of text chunks
        """
        chunk_size = 500  # Default chunk size
        
        if chatbot and hasattr(chatbot, 'config') and hasattr(chatbot.config, 'chunk_size'):
            chunk_size = chatbot.config.chunk_size
        
        # Split text into words
        words = text.split(' ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            if current_length >= chunk_size:
                chunks.append(' '.join(current_chunk)+ ' ')
                current_chunk = []
                current_length = 0

        # Add the remaining chunk if any
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
    
    def _add_chunk(self, chunk: str, metadata: Dict):
        """
        Add a chunk to the database.
        
        Args:
            chunk: Text chunk to add
            metadata: Metadata associated with the chunk
        """
        # Generate embedding for the chunk using sentence transformers
        if self.chatbot and self.chatbot.llm:
            embedding = np.array([self.chatbot.llm.generate_embedding(chunk)], dtype=np.float32)
        faiss.normalize_L2(embedding)
        
        # Add to Faiss index
        self.index.add(embedding)        
        
        # Store the chunk and metadata
        self.chunks.append(chunk)
        self.metadata.append(metadata)
    
    def search(self, query: str, top_k: int = 3) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Search for similar chunks to the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            Tuple containing:
                - faiss_query_embedding (np.ndarray): The embedding of the query for Faiss.
                - llm_query_embedding (np.ndarray): Placeholder embedding for the LLM.
                - results (List[Dict]): A list of dictionaries, each containing:
                    - text (str): The text of the chunk.
                    - metadata (Dict): Metadata associated with the chunk.
                    - score (float): The similarity score.
        """

        if self.index.ntotal == 0:
            return np.array([]), np.array([]), []

        # Generate embedding for the query
        faiss_query_embedding = np.array([self.chatbot.llm.generate_embedding(query)], dtype=np.float32)
        faiss.normalize_L2(faiss_query_embedding)

        llm_query_embedding = faiss_query_embedding  # Placeholder for now
        
        # Generate embedding for the query
        # Perform search
        D, I = self.index.search(faiss_query_embedding, min(top_k, self.index.ntotal))
        
        # Format results
        results = []
        for idx, distance in zip(I[0], D[0]):
            if idx < len(self.chunks):
                results.append({
                    "text": self.chunks[idx],
                    "metadata": self.metadata[idx],
                    "score": float(distance)
                })
        
        return faiss_query_embedding, llm_query_embedding, results
    
    def save(self, path: str):
        """
        Save the index and metadata to disk.
        
        Args:
            path: Path to save the database
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save Faiss index
        faiss.write_index(self.index, f"{path}.index")
        
        # Save chunks and metadata
        with open(f"{path}.json", 'w') as f:
            json.dump({
                "chunks": self.chunks,
                "metadata": self.metadata
            }, f)
    
    def load(self, path: str):
        """
        Load the index and metadata from disk.
        
        Args:
            path: Path to load the database from
        """
        # Load Faiss index
        if os.path.exists(f"{path}.index"):
            self.index = faiss.read_index(f"{path}.index")
        
        # Load chunks and metadata
        if os.path.exists(f"{path}.json"):
            with open(f"{path}.json", 'r') as f:
                data = json.load(f)
                self.chunks = data.get("chunks", data.get("texts", []))  # Support both naming conventions
                self.metadata = data["metadata"]
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with statistics
        """
        sources = {}
        for meta in self.metadata:
            source = meta.get("source", "unknown")
            if source in sources:
                sources[source] += 1
            else:
                sources[source] = 1
                
        return {
            "total_chunks": len(self.chunks),
            "sources": sources,
        }