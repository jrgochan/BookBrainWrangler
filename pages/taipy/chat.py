"""
Chat with AI page for the Book Knowledge AI application.
"""

from taipy.gui import navigate, notify, Markdown
import time
from datetime import datetime

# Define the chat page template
chat_template = """
<|container|class_name=page-container|
# 💬 Chat with AI

<|layout|columns=7 3|
<|container|class_name=chat-container|
<|container|class_name=chat-messages|
{chat_messages_content}
|>

<|container|class_name=chat-input|
<|{user_message}|input|label=Type your message...|class_name=chat-input-field|on_action=on_send_message|>
<|{on_send_message}|button|label=Send|>
|>
|>

<|container|class_name=chat-sidebar|
<|container|class_name=card|
## Chat Settings

<|{use_knowledge_base}|checkbox|label=Use Knowledge Base|>
<|{context_size}|slider|min=1|max=10|step=1|label=Context size|>
<|{temperature}|slider|min=0.1|max=1.0|step=0.1|label=Temperature|>

<|New Chat|button|on_action=on_new_chat|>
|>

<|container|class_name=card|
## Referenced Documents

{referenced_documents_content}
|>

<|container|class_name=card|
## Available Models

<|{ai_model}|selector|lov={available_models}|label=Select AI Model|>
|>
|>
|>
|>
"""

def get_template():
    """Get the chat page template."""
    return chat_template

def on_send_message(state):
    """
    Send a message to the AI and get a response.
    
    Args:
        state: The application state
    """
    if not state.user_message:
        return
    
    # Add user message to chat
    user_message = state.user_message
    state.user_message = ""
    
    timestamp = datetime.now().strftime("%H:%M")
    state.chat_messages.append({
        "role": "user",
        "content": user_message,
        "timestamp": timestamp
    })
    
    # Update UI
    state.chat_messages_content = render_chat_messages(state.chat_messages)
    
    # In a real implementation, we would:
    # context = ""
    # if state.use_knowledge_base:
    #     # Retrieve relevant context
    #     context = state.knowledge_base.search_for_context(user_message, limit=state.context_size)
    #     # Update referenced documents
    #     state.referenced_documents = extract_referenced_documents(context)
    #     state.referenced_documents_content = render_referenced_documents(state.referenced_documents)
    # 
    # # Get AI response
    # response = state.ai_client.generate_chat_response(
    #     state.chat_messages,
    #     context=context,
    #     temperature=state.temperature
    # )
    
    # For now, simulate AI response
    time.sleep(1)  # Simulate processing time
    
    ai_response = "This is a simulated AI response. In a real implementation, I would provide an answer based on your question and the knowledge base if enabled."
    if state.use_knowledge_base:
        ai_response += "\n\nI found some relevant information in your knowledge base that might help with your question."
        
        # Simulate referenced documents
        state.referenced_documents = [
            {
                "title": "Sample Document 1",
                "author": "Author 1",
                "relevance": 0.92
            },
            {
                "title": "Sample Document 2",
                "author": "Author 2",
                "relevance": 0.85
            }
        ]
        state.referenced_documents_content = render_referenced_documents(state.referenced_documents)
    
    # Add AI response to chat
    timestamp = datetime.now().strftime("%H:%M")
    state.chat_messages.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": timestamp
    })
    
    # Update UI
    state.chat_messages_content = render_chat_messages(state.chat_messages)

def on_new_chat(state):
    """
    Start a new chat session.
    
    Args:
        state: The application state
    """
    # Clear chat messages
    state.chat_messages = []
    state.chat_messages_content = "<p class='chat-welcome'>Ask me anything about your documents!</p>"
    
    # Clear referenced documents
    state.referenced_documents = []
    state.referenced_documents_content = "<p>No documents referenced yet.</p>"
    
    notify(state, "Started a new chat session", "success")

def render_chat_messages(messages):
    """
    Render chat messages.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        HTML string for rendering the chat messages
    """
    if not messages:
        return "<p class='chat-welcome'>Ask me anything about your documents!</p>"
    
    html = "<div class='chat-messages-list'>"
    
    for message in messages:
        role = message["role"]
        content = message["content"]
        timestamp = message["timestamp"]
        
        if role == "user":
            html += f"""
            <div class='chat-message chat-message-user'>
                <div class='chat-message-header'>
                    <span class='chat-message-role'>You</span>
                    <span class='chat-message-time'>{timestamp}</span>
                </div>
                <div class='chat-message-content'>{content}</div>
            </div>
            """
        else:
            html += f"""
            <div class='chat-message chat-message-ai'>
                <div class='chat-message-header'>
                    <span class='chat-message-role'>AI</span>
                    <span class='chat-message-time'>{timestamp}</span>
                </div>
                <div class='chat-message-content'>{content}</div>
            </div>
            """
    
    html += "</div>"
    return html

def render_referenced_documents(documents):
    """
    Render referenced documents.
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        HTML string for rendering the referenced documents
    """
    if not documents:
        return "<p>No documents referenced yet.</p>"
    
    html = "<div class='referenced-documents-list'>"
    
    for doc in documents:
        relevance_percentage = int(doc["relevance"] * 100)
        
        html += f"""
        <div class='referenced-document'>
            <div style='display: flex; justify-content: space-between;'>
                <strong>{doc["title"]}</strong>
                <span style='background-color: #e3f2fd; color: #1565c0; padding: 0.1rem 0.3rem; border-radius: 4px; font-size: 0.8rem;'>
                    {relevance_percentage}%
                </span>
            </div>
            <div style='font-size: 0.9rem; color: #666;'>{doc["author"]}</div>
        </div>
        """
    
    html += "</div>"
    return html

def init_state(state):
    """
    Initialize the state variables for this page.
    
    Args:
        state: The application state
    """
    # Chat state
    if "chat_messages" not in state:
        state.chat_messages = []
    if "chat_messages_content" not in state:
        state.chat_messages_content = "<p class='chat-welcome'>Ask me anything about your documents!</p>"
    if "user_message" not in state:
        state.user_message = ""
    
    # Settings state
    if "use_knowledge_base" not in state:
        state.use_knowledge_base = True
    if "context_size" not in state:
        state.context_size = 5
    if "temperature" not in state:
        state.temperature = 0.7
    if "ai_model" not in state:
        state.ai_model = "default"
    if "available_models" not in state:
        state.available_models = ["default", "gpt-3.5-turbo", "llama2-13b", "claude-instant"]
    
    # Referenced documents state
    if "referenced_documents" not in state:
        state.referenced_documents = []
    if "referenced_documents_content" not in state:
        state.referenced_documents_content = "<p>No documents referenced yet.</p>"