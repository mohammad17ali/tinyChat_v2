from flask import Flask
from app.chatbot.config import Config
from app.chatbot.rag_chatbot import RAGChatbot
from app.routes import main


config = Config()
chatbot = RAGChatbot(config)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Register the blueprint
app.register_blueprint(main)

if __name__ == "__main__":
    app.run(debug=True)
