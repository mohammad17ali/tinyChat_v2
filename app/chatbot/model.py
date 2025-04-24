from sentence_transformers import SentenceTransformer

class TinyLlamaChatModel:
    """Dummy chat model that returns a fixed response when GPU resources are absent."""
    def __init__(self, model_name: str = None, use_local: bool = True):
        # Instead of loading a real model, just note that GPU is not available
        import logging
        logger = logging.getLogger(__name__)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.warning("GPU resource not present. Using dummy response generator.")
        self.use_local = use_local


    def generate_embedding(self, text: str):
        """Generate embedding for the given text using SentenceTransformer."""
        return self.embedding_model.encode(text)


    def generate_response(self, user_message: str, context: str = "", max_new_tokens: int = 256) -> str:
        """
        Always returns a dummy message indicating GPU absence.
        """
        return "GPU resource not present"
