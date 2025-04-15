"""
Taipy configuration for the Book Knowledge AI application.
"""
from taipy import Config
from taipy.config import Scope


# Define data nodes for application state
knowledge_base_node_cfg = Config.configure_data_node(
    id="knowledge_base",
    scope=Scope.GLOBAL,
    storage_type="pickle",
    default_data=None
)

books_node_cfg = Config.configure_data_node(
    id="books",
    scope=Scope.GLOBAL,
    storage_type="pickle",
    default_data=[]
)

search_results_node_cfg = Config.configure_data_node(
    id="search_results",
    scope=Scope.GLOBAL,
    storage_type="pickle",
    default_data=[]
)

# Define tasks for data processing
load_books_task_cfg = Config.configure_task(
    id="load_books_task",
    function=None,  # Will be set at runtime
    inputs=[],
    outputs=[books_node_cfg]
)

search_archive_task_cfg = Config.configure_task(
    id="search_archive_task",
    function=None,  # Will be set at runtime
    inputs=[],
    outputs=[search_results_node_cfg]
)

# Define scenarios for main application workflows
main_scenario_cfg = Config.configure_scenario(
    id="main_scenario",
    tasks=[load_books_task_cfg, search_archive_task_cfg]
)

# Define global application configuration
app_config = {
    "title": "Book Knowledge AI",
    "theme": {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "info": "#17becf",
        "warning": "#d62728",
        "danger": "#e377c2",
        "light": "#f5f5f5",
        "dark": "#333333",
    },
    "layout": {
        "page_size": "lg",
        "control_size": "md",
        "gap": "15px",
    },
}