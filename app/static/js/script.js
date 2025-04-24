// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const newChatButton = document.getElementById('new-chat-btn');
const chatHistory = document.getElementById('chat-history');
const contextPanel = document.getElementById('context-panel');
const documentsList = document.getElementById('documents-list');
const fileUpload = document.getElementById('file-upload');
const urlInput = document.getElementById('url-input');
const urlUploadBtn = document.getElementById('url-upload-btn');
const currentChatTitle = document.getElementById('current-chat-title');
const dbStatsCount = document.getElementById('db-stats-count');
const attachmentButton = document.getElementById('attachment-button');
const uploadModal = document.getElementById('upload-modal');
const closeModal = document.querySelector('.close');
const modalUploadForm = document.getElementById('modal-upload-form');

// State
let currentSessionId = null;
let isThinking = false;

// Initialize the app
function initApp() {
    loadChatSessions();
    loadDBStats();
    loadDocuments();
    
    // Create a new session by default
    createNewSession();
    
    // Setup event listeners
    setupEventListeners();
}

// Set up event listeners
function setupEventListeners() {
    // Send message on button click or Enter key
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Textarea auto-resize
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
    });
    
    // New chat button
    newChatButton.addEventListener('click', createNewSession);
    
    // File upload
    fileUpload.addEventListener('change', handleFileUpload);
    
    // URL upload
    urlUploadBtn.addEventListener('click', handleUrlUpload);
    
    // Attachment button opens modal
    attachmentButton.addEventListener('click', () => {
        uploadModal.style.display = 'block';
    });
    
    // Close modal
    closeModal.addEventListener('click', () => {
        uploadModal.style.display = 'none';
    });
    
    // Modal upload form
    modalUploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const modalFileUpload = document.getElementById('modal-file-upload');
        if (modalFileUpload.files.length > 0) {
            const formData = new FormData();
            formData.append('file', modalFileUpload.files[0]);
            uploadFile(formData);
            uploadModal.style.display = 'none';
        }
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === uploadModal) {
            uploadModal.style.display = 'none';
        }
    });
}

// Create a new chat session
function createNewSession() {
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: "Hi, I'm starting a new chat.",
            session_id: null
        }),
    })
    .then(response => response.json())
    .then(data => {
        currentSessionId = data.session_id;
        currentChatTitle.textContent = "New Conversation";
        resetChatMessages();
        loadChatSessions();
    })
    .catch(error => {
      console.error("Error creating new session:", error);
      chatMessages.innerHTML = "";
      const errorMessage = document.createElement("div");
      errorMessage.classList.add("error-message");
      errorMessage.textContent =
        "There was an error starting a new session. Please try again.";
      chatMessages.appendChild(errorMessage);
    });
}

// Load existing chat sessions
function loadChatSessions() {
  console.log('loading sessions')
    fetch('/api/sessions')
        .then(response => response.json())
        .then(sessions => {
            chatHistory.innerHTML = '';
            
            // Sort sessions by timestamp (newest first)
            const sortedSessions = Object.entries(sessions).sort((a, b) => {
                return new Date(b[1].timestamp) - new Date(a[1].timestamp);
            });
            
            sortedSessions.forEach(([id, session]) => {
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                if (id === currentSessionId) {
                    chatItem.classList.add('active');
                }
                
                chatItem.innerHTML = `
                    <i class="fas fa-comment"></i>
                    <div class="chat-item-title">${session.first_message}</div>
                    <div class="chat-item-date">${formatDate(session.timestamp)}</div>
                `;
                
                chatItem.addEventListener('click', () => loadSession(id));
                chatHistory.appendChild(chatItem);
            });
        })
        .catch(error => {
            console.error('Error loading sessions:', error);
        });
}

// Load a specific chat session
function loadSession(sessionId) {
    fetch(`/api/sessions/${sessionId}`)
        .then(response => response.json())
        .then(history => {
            currentSessionId = sessionId;
            resetChatMessages();
            
            // Update active session in the UI
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
                if (item.querySelector('.chat-item-title').textContent === history[0]?.user) {
                    item.classList.add('active');
                }
            });
            
            // Set chat title
            if (history.length > 0) {
                const firstMsg = history[0].user;
                currentChatTitle.textContent = firstMsg.length > 30 ? 
                    firstMsg.substring(0, 30) + '...' : firstMsg;
            }
            
            // Display messages
            history.forEach(msg => {
                addMessageToChat(msg.user, 'user');
                addMessageToChat(msg.assistant, 'bot');
            });
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error loading session:', error);
        });
}

// Send a message
function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isThinking) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input and reset height
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Show thinking indicator
    showThinking();
    
    // Send to backend
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: currentSessionId
        }),
    })
    .then(response => response.json())
    .then(data => {
      if (!data || typeof data !== 'object') {
        hideThinking();
        console.error('Invalid data format received from server:', data);
        addMessageToChat('Sorry, there was an error processing your request.', 'bot');
        return;
      }


        // Hide thinking indicator
        hideThinking();
        
        // Add bot response to chat
        addMessageToChat(data.response, 'bot');
        
        // Update session ID if new

        if (data.session_id === undefined){
          console.error("session_id is undefined", data)
        } else if (data.response === undefined){
          console.error("response is undefined", data)
        }
        else if (data.session_id !== currentSessionId) {
            currentSessionId = data.session_id;
            loadChatSessions();
        }
        
        // Update context panel with relevant chunks
        updateContextPanel(data.relevant_chunks);
        
        // Update chat title if this is the first message
        if (currentChatTitle.textContent === "New Conversation" && message) {
            currentChatTitle.textContent = message.length > 30 ? 
                message.substring(0, 30) + '...' : message;
        }
        
        // Scroll to bottom
        scrollToBottom();
    })
    .catch(error => {
        hideThinking();
        console.error('Error sending message:', error);
        addMessageToChat('Sorry, there was an error processing your request.', 'bot');
    });
}

// Add a message to the chat
function addMessageToChat(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    const messageMeta = document.createElement('div');
    messageMeta.className = 'message-meta';
    
    // Add timestamp
    const now = new Date();
    const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    messageMeta.innerHTML = `<i class="fas fa-clock"></i> ${time}`;
    
    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageMeta);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Show thinking indicator
function showThinking() {
    isThinking = true;
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message bot-message thinking';
    thinkingDiv.id = 'thinking';
    
    thinkingDiv.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;
    
    chatMessages.appendChild(thinkingDiv);
    scrollToBottom();
}

// Hide thinking indicator
function hideThinking() {
    isThinking = false;
    const thinkingDiv = document.getElementById('thinking');
    if (thinkingDiv) {
        thinkingDiv.remove();
    }
}

// Update context panel with relevant chunks
function updateContextPanel(chunks) {
    contextPanel.innerHTML = '';
    
    if (!chunks || chunks.length === 0) {
        contextPanel.innerHTML = `
            <div class="no-context">
                <p>No relevant context found.</p>
            </div>
        `;
        return;
    }
    
    chunks.forEach(chunk => {
        const snippetDiv = document.createElement('div');
        snippetDiv.className = 'context-snippet';
        
        snippetDiv.innerHTML = `
            ${chunk.text}
            <div class="context-snippet-source">Source: ${chunk.source}</div>
        `;
        
        contextPanel.appendChild(snippetDiv);
    });
}

// Handle file upload
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadFile(formData);
}

// Upload file to backend
function uploadFile(formData) {
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            addMessageToChat(`File uploaded successfully: ${data.message}`, 'bot');
            // Refresh DB stats and documents list
            loadDBStats();
            loadDocuments();
        } else {
            addMessageToChat(`Error uploading file: ${data.error}`, 'bot');
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        addMessageToChat('Sorry, there was an error uploading your file.', 'bot');
    });
}

// Handle URL upload
function handleUrlUpload() {
    const url = urlInput.value.trim();
    if (!url) return;
    
    fetch('/api/upload-url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            addMessageToChat(`URL content is being processed: ${data.message}`, 'bot');
            // Clear URL input
            urlInput.value = '';
            // Refresh DB stats
            setTimeout(loadDBStats, 2000);
            setTimeout(loadDocuments, 2000);
        } else {
            addMessageToChat(`Error processing URL: ${data.error}`, 'bot');
        }
    })
    .catch(error => {
        console.error('Error processing URL:', error);
        addMessageToChat('Sorry, there was an error processing the URL.', 'bot');
    });
}

// Load DB stats
function loadDBStats() {
    fetch('/api/db-stats')
        .then(response => response.json())
        .then(stats => {
            dbStatsCount.textContent = stats.total_chunks;
        })
        .catch(error => {
            console.error('Error loading DB stats:', error);
        });
}

// Load documents
function loadDocuments() {
    fetch('/api/db-documents')
        .then(response => response.json())
        .then(stats => {
          documentsList.innerHTML = "";

          // If the stats are empty.
          if (Object.keys(stats).length === 0) {
            documentsList.innerHTML = `
              <div class="no-docs">
                <p>No documents in the database.</p>
              </div>
            `;
            return;
          }

          for (const [source, count] of Object.entries(stats)) {
            if (source === "chat" || source === "chat_history") continue;

            const docItem = document.createElement("div");
            docItem.className = "document-item";

            let icon = "fa-file-alt";
            if (source.endsWith(".pdf")) {
              icon = "fa-file-pdf";
            } else if (source.startsWith("http")) {
              icon = "fa-globe";
            }
            docItem.innerHTML = `
                    <div class="document-icon">
                        <i class="fas ${icon}"></i>
                    </div>
                    <div class="document-info">
                        <div class="document-title">${source}</div>
                        <div class="document-meta">${count} chunks</div>
                    </div>
                `;
            documentsList.appendChild(docItem);
          }
        })
        .catch(error => {
          documentsList.innerHTML = ""
            console.error('Error loading documents:', error);
        });
}

// Reset chat messages
function resetChatMessages() {
    chatMessages.innerHTML = '';
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    
    // If today, show time
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // If this year, show month and day
    if (date.getFullYear() === now.getFullYear()) {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
    
    // Otherwise show full date
    return date.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);