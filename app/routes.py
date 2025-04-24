import os
import logging
from flask import Blueprint, request, jsonify, render_template, send_from_directory, current_app
from werkzeug.utils import secure_filename

from app.chatbot import chatbot

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Use os.path.expanduser for the upload folder
UPLOAD_FOLDER = os.path.expanduser("~/tinychat/uploads")

# Create the uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api/chat', methods=['POST']) 
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', None) 

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        result = chatbot.chat(user_message, session_id)
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    return jsonify(result)

@main.route('/api/sessions', methods=['GET'])
def get_sessions():
    sessions = chatbot.get_all_sessions()
    return jsonify(sessions)

@main.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    history = chatbot.get_session_history(session_id)
    return jsonify(history)

@main.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':   
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)   
     
        try:
            current_app.logger.info(f"Starting process_and_add for file: {filename}")
            from app.chatbot.document_processor import DocumentProcessor
            current_app.logger.info(f"Calling DocumentProcessor.process_file for file: {filename}")
            chunks = DocumentProcessor.process_file(filepath)
            current_app.logger.info(f"File {filename} processed into {len(chunks)} chunks.")

            for chunk in chunks:
                current_app.logger.info(f"Adding chunk to vector DB. Source: {filename}")
                chatbot.vector_db.add_text(chunk, {"source": filename}, chatbot)
            current_app.logger.info(f"Saving vector DB after adding chunks from: {filename}")
            chatbot.vector_db.save("data/vector_db")
            current_app.logger.info(f"Saved vector DB after adding chunks from: {filename}")
            current_app.logger.info(f"Added {filename} to vector DB.")
            
            
            

            return jsonify({
                "success": True,
                "message": f"File {filename} uploaded and being processed.",
                
            })

        except Exception as e:
            current_app.logger.error(f"Error processing file {filename}: {str(e)}")
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500

    return jsonify({"error": "File type not allowed"}), 400

@main.route('/api/upload-url', methods=['POST'])
def upload_url():
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        from app.chatbot.document_processor import DocumentProcessor
        text = DocumentProcessor.process_webpage(url)
        chatbot.vector_db.add_text(text, {"source": url})
        chatbot.vector_db.save("data/vector_db")
        current_app.logger.info(f"Added {url} to vector DB.")

       
        
        return jsonify({
            "success": True,
            "message": f"URL {url} is being processed."
        })
    except Exception as e:
        return jsonify({"error": f"Error processing URL: {str(e)}"}), 500


@main.route('/api/db-stats', methods=['GET'])
def get_db_stats():
    stats = chatbot.vector_db.get_stats()
    return jsonify(stats)


@main.route('/api/db-documents', methods=['GET'])
def get_db_documents():
    try:
        stats = chatbot.vector_db.get_stats()
        sources = stats.get("sources", {})
        return jsonify(sources)
    except Exception as e:
        return jsonify({"error": f"Error processing get_db_documents: {str(e)}"}), 500


@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

