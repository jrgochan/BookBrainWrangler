"""
Core module for Book Knowledge AI application.
Contains fundamental application components and configuration.
"""

from core.config import get_config
from core.constants import APP_VERSION

__all__ = [
    'get_config',
    'APP_VERSION',
]