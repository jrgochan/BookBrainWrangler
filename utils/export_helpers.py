"""
Export utilities for generating content from the knowledge base.
This module is now a wrapper over the modular implementation in the export_helpers directory.
"""

# Re-export all the public functions from the modular export_helpers package
from utils.export_helpers.common import EXPORT_FORMATS
from utils.export_helpers.markdown import generate_knowledge_export, save_markdown_to_file
from utils.export_helpers.exports import export_knowledge_base

# Include private helper functions for backward compatibility
from utils.export_helpers.markdown import export_to_markdown as _export_markdown
from utils.export_helpers.json import export_to_json as _export_json
from utils.export_helpers.csv import export_to_csv as _export_csv
from utils.export_helpers.sqlite import export_to_sqlite as _export_sqlite

__all__ = [
    'EXPORT_FORMATS',
    'generate_knowledge_export',
    'save_markdown_to_file',
    'export_knowledge_base',
    '_export_markdown',
    '_export_json',
    '_export_csv',
    '_export_sqlite'
]
