"""
Taipy configuration for Book Knowledge AI application.
"""

from taipy.config import Config

# Define application-wide configuration

# Set default values for global settings
Config.configure_global_app(
    name="Book Knowledge AI",
    version="1.0.0",
    theme="light",
    debug=True
)

# Configure data nodes
# These are used to store and exchange data between different parts of the application
Config.configure_data_node(
    id="books_data",
    storage_type="pickle",
    default_data=[]
)

Config.configure_data_node(
    id="knowledge_base_data",
    storage_type="pickle",
    default_data={}
)

Config.configure_data_node(
    id="chat_history",
    storage_type="pickle",
    default_data=[]
)

# Configure job execution settings
# These control how various background tasks are executed
Config.configure_job_executions(
    mode="standalone",
    max_nb_of_workers=4
)

# Configure server settings
Config.configure_server(
    host="0.0.0.0",
    port=5000,
    debug=True
)

# Load the configuration
config = Config.load()