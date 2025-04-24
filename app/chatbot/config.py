# app/chatbot/config.py

class Config:
    def __init__(self):
        # Vector database settings
        self.vector_dim = 768  # Dimension of embeddings
        
        # Chunking settings
        self.chunk_size = 500  # Maximum chunk size in characters
        
        # Retrieval settings
        self.retrieval_top_k = 4  # Number of chunks to retrieve
        
        # Response generation settings
        self.max_new_tokens = 500  # Maximum length of generated responses
        
        # Other settings
        self.stop_word = "!quit"  # Word to stop the conversation