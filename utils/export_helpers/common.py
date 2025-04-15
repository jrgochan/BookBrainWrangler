"""
Common utilities and constants for export functionality.
"""

import os
import json
import datetime
from typing import Optional, Dict, List, Any, Union, Tuple, Callable

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

# Export format definitions
EXPORT_FORMATS = {
    "markdown": {"extension": "md", "mime": "text/markdown", "name": "Markdown Document"},
    "json": {"extension": "json", "mime": "application/json", "name": "JSON Data"},
    "csv": {"extension": "zip", "mime": "application/zip", "name": "CSV Files (Zipped)"},
    "sqlite": {"extension": "db", "mime": "application/x-sqlite3", "name": "SQLite Database"}
}
