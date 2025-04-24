# app/chatbot/rag_chatbot.py

import uuid
from datetime import datetime
from app.chatbot.model import TinyLlamaChatModel
from app.chatbot.config import Config
from app.chatbot.vectordb import VectorDB

class RAGChatbot:    
    def __init__(self, config: Config):
        """        
        Initialize the RAG chatbot.
        
        Args:
            config: Configuration for the chatbot
        """
        self.config = config
        self.vector_db = VectorDB(config.vector_dim, db_path="data/vector_db", chatbot=self)
        self.llm = TinyLlamaChatModel()
        self.chat_sessions = {}

    def create_session(self):
        """
        Create a new chat session.
        
        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        self.chat_sessions[session_id] = []
        return session_id

    def chat(self, user_input, session_id=None):
        """
        Process user input and generate a response.
        
        Args:
            user_input: User's message
            session_id: Optional session ID
            
        Returns:
            Dict: Response data including the bot's reply
        """
        if not session_id or session_id not in self.chat_sessions:
            session_id = self.create_session()

        if self.config.stop_word in user_input:
            return {"response": "Chat ended.", "session_id": session_id}

        # Search for relevant chunks
        faiss_query_embedding, llm_query_embedding, results = self.vector_db.search(user_input, top_k=self.config.retrieval_top_k)
        
        relevant_chunks = [{"text": r["text"], "source": r["metadata"].get("source", "unknown")} 
                          for r in results]

        if not results:
            response = "I don't have enough information to answer that question."
        else:
            
            # Build context from retrieved chunks
            context = "\n".join(r["text"] for r in results)
            try:
                # Generate response (placeholder - replace with actual LLM in production)
                response = self._generate_response(user_input, context)
            except Exception as e:
                return {"error": f"Error generating response: {str(e)}", "session_id": session_id}

        # Save message to session history
        message = {"user": user_input, "assistant": response, "timestamp": datetime.now().isoformat()}
        self.chat_sessions[session_id].append(message)

        # Add conversation to vector db for future retrieval
        try:
            self.vector_db.add_text(
                f"User: {user_input}\nAssistant: {response}", 
                {"source": "chat", "session_id": session_id}
            )
            self.vector_db.save("data/vector_db")
        except Exception as e:
            return {"error": f"Error saving to vector db: {str(e)}", "session_id": session_id}

        return {
            "response": response,
            "session_id": session_id,
            "relevant_chunks": relevant_chunks,
        }

    def _generate_response(self, query, context, llm_query_embedding = None):
        """
        Generate a response based on query and context.
        
        This is a placeholder method - replace with actual LLM integration.
        
        Args:
            query: User's question
            context: Retrieved context
            
        Returns:
            str: Generated response
        """
        # Placeholder for LLM integration
        # In a real implementation, you would call an LLM API here
        if not context:
            return "I don't have enough information to answer that question."
            
        # Very simple response generation for demo purposes
        return f"Based on the information I have, I can provide this answer: {context[:100]}..."

    def get_session_history(self, session_id):
        """
        Get chat history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List: Session message history
        """
        return self.chat_sessions.get(session_id, [])

    def get_all_sessions(self):
        """
        Get information about all chat sessions.
        
        Returns:
            Dict: Session information
        """
        return {
            sid: {
                "first_message": hist[0]["user"][:50] + "..." if hist else "",
                "timestamp": hist[0]["timestamp"] if hist else "",
                "message_count": len(hist)
            }
            for sid, hist in self.chat_sessions.items()
        }