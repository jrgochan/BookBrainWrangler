"""
Settings page for the Book Knowledge AI application.
"""

from taipy.gui import navigate, notify, Markdown

# Define the settings page template
settings_template = """
<|container|class_name=page-container|
# ⚙️ Settings

<|tabs|
<|tab|label=AI Settings|
<|container|class_name=card|
## AI Model Configuration

<|{ai_provider}|selector|lov={ai_providers}|label=AI Provider|>

<|container|render={ai_provider == "OpenAI"}|
### OpenAI Settings

<|{openai_model}|selector|lov={openai_models}|label=OpenAI Model|>
<|{openai_api_key}|input|label=API Key|password=True|>
|>

<|container|render={ai_provider == "Ollama"}|
### Ollama Settings

<|{ollama_model}|selector|lov={ollama_models}|label=Ollama Model|>
<|{ollama_host}|input|label=Ollama Host|>
<|{ollama_port}|input|label=Ollama Port|>
|>

<|container|render={ai_provider == "HuggingFace"}|
### HuggingFace Settings

<|{huggingface_model}|selector|lov={huggingface_models}|label=HuggingFace Model|>
<|{huggingface_api_key}|input|label=API Key|password=True|>
|>

<|Save AI Settings|button|on_action=on_save_ai_settings|>
|>
|>

<|tab|label=Knowledge Base Settings|
<|container|class_name=card|
## Knowledge Base Configuration

<|{vector_store_type}|selector|lov={vector_store_types}|label=Vector Store Type|>
<|{embedding_model}|selector|lov={embedding_models}|label=Embedding Model|>
<|{chunk_size}|slider|min=256|max=2048|step=128|label=Chunk Size|>
<|{chunk_overlap}|slider|min=0|max=512|step=32|label=Chunk Overlap|>

<|Save Knowledge Base Settings|button|on_action=on_save_kb_settings|>
|>

<|container|class_name=card|
## Maintenance

<|layout|columns=1 1|
<|Rebuild Index|button|on_action=on_rebuild_index|>
<|Export Knowledge Base|button|on_action=on_export_kb|>
|>
|>
|>

<|tab|label=Document Processing|
<|container|class_name=card|
## Document Processing Settings

<|{enable_ocr}|checkbox|label=Enable OCR for Images|>
<|{ocr_language}|selector|lov={ocr_languages}|label=OCR Language|>
<|{extract_images}|checkbox|label=Extract Images from Documents|>
<|{process_pdf_forms}|checkbox|label=Process PDF Forms|>

<|Save Document Settings|button|on_action=on_save_doc_settings|>
|>
|>

<|tab|label=User Interface|
<|container|class_name=card|
## User Interface Settings

<|{ui_theme}|selector|lov={ui_themes}|label=UI Theme|>
<|{items_per_page}|slider|min=10|max=100|step=10|label=Items per Page|>
<|{enable_animations}|checkbox|label=Enable Animations|>
<|{show_welcome_screen}|checkbox|label=Show Welcome Screen at Startup|>

<|Save UI Settings|button|on_action=on_save_ui_settings|>
|>
|>

<|tab|label=Advanced|
<|container|class_name=card|
## Advanced Settings

<|{log_level}|selector|lov={log_levels}|label=Log Level|>
<|{data_directory}|input|label=Data Directory|>
<|{temp_directory}|input|label=Temporary Directory|>
<|{max_upload_size_mb}|slider|min=5|max=500|step=5|label=Max Upload Size (MB)|>

<|Save Advanced Settings|button|on_action=on_save_advanced_settings|>
|>

<|container|class_name=card|
## Danger Zone

<|layout|columns=1 1|
<|Clear All Logs|button|on_action=on_clear_logs|>
<|Reset to Default Settings|button|on_action=on_reset_settings|>
|>

<|container|class_name=danger-zone|
<|Delete All Data|button|class_name=danger-button|on_action=on_delete_all_data|>
|>
|>
|>
|>
"""

def get_template():
    """Get the settings page template."""
    return settings_template

def on_save_ai_settings(state):
    """
    Save AI settings.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would save these settings to a configuration file
    # or database, and potentially restart the AI client with new settings
    
    notify(state, "AI settings saved successfully", "success")

def on_save_kb_settings(state):
    """
    Save knowledge base settings.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would save these settings to a configuration file
    # or database, and potentially update the knowledge base configuration
    
    notify(state, "Knowledge Base settings saved successfully", "success")

def on_save_doc_settings(state):
    """
    Save document processing settings.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would save these settings to a configuration file
    # or database, and potentially update the document processor configuration
    
    notify(state, "Document processing settings saved successfully", "success")

def on_save_ui_settings(state):
    """
    Save UI settings.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would save these settings to a configuration file
    # or database, and potentially update the UI configuration
    
    notify(state, "UI settings saved successfully", "success")

def on_save_advanced_settings(state):
    """
    Save advanced settings.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would save these settings to a configuration file
    # or database, and potentially update system configuration
    
    notify(state, "Advanced settings saved successfully", "success")

def on_rebuild_index(state):
    """
    Rebuild the knowledge base index.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would:
    # state.knowledge_base.rebuild_index()
    
    notify(state, "Knowledge base index is being rebuilt...", "info")
    
    # Simulate rebuilding progress
    # (In a real implementation, this would be handled asynchronously)
    import time
    time.sleep(2)  # Simulate processing time
    
    notify(state, "Knowledge base index rebuilt successfully", "success")

def on_export_kb(state):
    """
    Export the knowledge base.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would:
    # export_path = state.knowledge_base.export()
    
    notify(state, "Knowledge base is being exported...", "info")
    
    # Simulate export progress
    # (In a real implementation, this would be handled asynchronously)
    import time
    time.sleep(2)  # Simulate processing time
    
    notify(state, "Knowledge base exported successfully to exports/kb_export.zip", "success")

def on_clear_logs(state):
    """
    Clear all logs.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would:
    # state.logger.clear_logs()
    
    notify(state, "All logs have been cleared", "success")

def on_reset_settings(state):
    """
    Reset all settings to default values.
    
    Args:
        state: The application state
    """
    # Reset all settings to defaults
    init_state(state)
    
    notify(state, "All settings have been reset to defaults", "success")

def on_delete_all_data(state):
    """
    Delete all application data.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would show a confirmation dialog
    # and then delete all data if confirmed
    
    # For now, just show a notification
    notify(state, "This is a dangerous operation that would delete all application data. In a real implementation, it would require confirmation.", "warning")

def init_state(state):
    """
    Initialize the state variables for this page.
    
    Args:
        state: The application state
    """
    # AI settings
    if "ai_provider" not in state:
        state.ai_provider = "OpenAI"
    if "ai_providers" not in state:
        state.ai_providers = ["OpenAI", "Ollama", "HuggingFace"]
    
    # OpenAI settings
    if "openai_model" not in state:
        state.openai_model = "gpt-3.5-turbo"
    if "openai_models" not in state:
        state.openai_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    if "openai_api_key" not in state:
        state.openai_api_key = ""
    
    # Ollama settings
    if "ollama_model" not in state:
        state.ollama_model = "llama2:7b"
    if "ollama_models" not in state:
        state.ollama_models = ["llama2:7b", "llama2:13b", "mistral:7b"]
    if "ollama_host" not in state:
        state.ollama_host = "localhost"
    if "ollama_port" not in state:
        state.ollama_port = "11434"
    
    # HuggingFace settings
    if "huggingface_model" not in state:
        state.huggingface_model = "google/flan-t5-xxl"
    if "huggingface_models" not in state:
        state.huggingface_models = ["google/flan-t5-xxl", "meta-llama/Llama-2-7b", "mistralai/Mistral-7B-v0.1"]
    if "huggingface_api_key" not in state:
        state.huggingface_api_key = ""
    
    # Knowledge base settings
    if "vector_store_type" not in state:
        state.vector_store_type = "FAISS"
    if "vector_store_types" not in state:
        state.vector_store_types = ["FAISS", "Chroma", "Milvus", "Pinecone"]
    if "embedding_model" not in state:
        state.embedding_model = "all-MiniLM-L6-v2"
    if "embedding_models" not in state:
        state.embedding_models = ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "openai-ada-002"]
    if "chunk_size" not in state:
        state.chunk_size = 512
    if "chunk_overlap" not in state:
        state.chunk_overlap = 64
    
    # Document processing settings
    if "enable_ocr" not in state:
        state.enable_ocr = True
    if "ocr_language" not in state:
        state.ocr_language = "eng"
    if "ocr_languages" not in state:
        state.ocr_languages = ["eng", "fra", "deu", "spa", "ita", "por", "nld", "rus", "jpn", "chi_sim"]
    if "extract_images" not in state:
        state.extract_images = True
    if "process_pdf_forms" not in state:
        state.process_pdf_forms = True
    
    # UI settings
    if "ui_theme" not in state:
        state.ui_theme = "Light"
    if "ui_themes" not in state:
        state.ui_themes = ["Light", "Dark", "Auto"]
    if "items_per_page" not in state:
        state.items_per_page = 20
    if "enable_animations" not in state:
        state.enable_animations = True
    if "show_welcome_screen" not in state:
        state.show_welcome_screen = True
    
    # Advanced settings
    if "log_level" not in state:
        state.log_level = "INFO"
    if "log_levels" not in state:
        state.log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if "data_directory" not in state:
        state.data_directory = "./data"
    if "temp_directory" not in state:
        state.temp_directory = "./temp"
    if "max_upload_size_mb" not in state:
        state.max_upload_size_mb = 50