"""
Constants and default values for the Chat with AI feature.
"""

# Chat interface constants
AVATARS = {
    "user": "🧑‍💻",
    "assistant": "🤖",
    "system": "ℹ️"
}

# Knowledge source options
KNOWLEDGE_SOURCES = {
    "book_knowledge": "Book Knowledge",
    "model_knowledge": "Model Knowledge", 
    "combined": "Combined"
}

# Default system prompt
DEFAULT_SYSTEM_PROMPT = (
    "You are an AI assistant helping with knowledge about books in the user's library. "
    "Be concise, accurate, and helpful. When referencing information from books, "
    "mention the source if available. If you don't know something, say so honestly."
)

# Default chat configuration
DEFAULT_CHAT_CONFIG = {
    'temperature': 0.7,
    'max_tokens': 1000,
    'top_p': 0.9,
    'frequency_penalty': 0.0,
    'presence_penalty': 0.0,
    'stream': True,
    'show_context': False,
    'context_window': 4096,
    'num_ctx_results': 5
}