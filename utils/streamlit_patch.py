"""
Patch for Streamlit to fix compatibility with PyTorch.
This module patches Streamlit's file watching functionality to prevent crashes with PyTorch.
"""

import sys
from functools import wraps
from utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)

def apply_patches():
    """Apply all necessary patches to make Streamlit work with PyTorch."""
    logger.info("Applying Streamlit compatibility patches")
    
    # Add a monkeypatch for Streamlit's module watching
    try:
        # Alternative approach: patch get_module_paths in local_sources_watcher
        from streamlit.watcher import local_sources_watcher
        
        original_get_module_paths = getattr(local_sources_watcher, 'get_module_paths', None)
        
        if original_get_module_paths:
            # Found the function - patch it
            @wraps(original_get_module_paths)
            def patched_get_module_paths(module_name):
                """
                A patched version of get_module_paths that safely handles PyTorch modules.
                """
                # Handle both string names and actual module objects
                module_name_str = module_name.__name__ if hasattr(module_name, '__name__') else str(module_name)
                
                if 'torch' in module_name_str:
                    logger.debug(f"Safely handling PyTorch module: {module_name_str}")
                    return []  # Return empty list for PyTorch modules
                
                # For all other modules, use the original function
                try:
                    return original_get_module_paths(module_name)
                except Exception as e:
                    logger.debug(f"Error in get_module_paths for module {module_name}: {str(e)}")
                    return []  # Return empty list on errors
            
            # Replace the original function with our patched version
            local_sources_watcher.get_module_paths = patched_get_module_paths
            logger.info("Successfully patched Streamlit's get_module_paths function")
        else:
            logger.warning("Could not find get_module_paths in local_sources_watcher, trying alternative patch")
            
            # Try to override the module methods or attributes that might interact with torch.classes
            if hasattr(local_sources_watcher, 'get_paths_with_error_message'):
                original_func = local_sources_watcher.get_paths_with_error_message
                
                @wraps(original_func)
                def patched_get_paths_with_error_message(*args, **kwargs):
                    """Safely handle any torch module interactions"""
                    try:
                        return original_func(*args, **kwargs)
                    except Exception as e:
                        if 'torch' in str(e):
                            logger.debug(f"Suppressing error in torch-related module: {str(e)}")
                            return []
                        raise
                
                local_sources_watcher.get_paths_with_error_message = patched_get_paths_with_error_message
                logger.info("Successfully patched Streamlit's get_paths_with_error_message function")
        
    except ImportError:
        logger.warning("Could not import streamlit.watcher.local_sources_watcher, patch not applied")
    except Exception as e:
        logger.error(f"Failed to patch Streamlit: {str(e)}")
        
    # Direct patch for torch._classes module to handle the specific error case
    try:
        import torch
        import types
        
        # Check if the _classes module exists
        if hasattr(torch, '_classes'):
            # Create a custom __getattr__ that prevents the error accessing __path__._path
            original_getattr = getattr(torch._classes, '__getattr__', None)
            
            def safe_getattr(self, name):
                # Special case for the error mentioned in the logs
                if name == '__path__' and hasattr(self, 'name'):
                    logger.debug(f"Safely handling torch._classes.__path__ access")
                    # Return a fake path object that has the _path attribute
                    class FakePath:
                        _path = []
                    return FakePath()
                
                # For other attributes, use the original __getattr__ if available
                if original_getattr:
                    return original_getattr(self, name)
                
                # Default behavior
                raise AttributeError(f"module 'torch._classes' has no attribute '{name}'")
            
            # Set the safe __getattr__ on the module
            torch._classes.__getattr__ = safe_getattr
            logger.info("Successfully patched torch._classes.__getattr__")
    
    except ImportError:
        logger.warning("Could not import torch, specific patch not applied")
    except Exception as e:
        logger.error(f"Failed to patch torch._classes: {str(e)}")
    
    # Patch asyncio event loop handling
    try:
        import asyncio
        
        # Define a function to ensure there's a running event loop
        def ensure_event_loop():
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
        # Patch asyncio.get_running_loop to ensure a loop exists
        original_get_running_loop = asyncio.get_running_loop
        
        @wraps(original_get_running_loop)
        def patched_get_running_loop():
            try:
                return original_get_running_loop()
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
                
        # Replace the original function with our patched version
        asyncio.get_running_loop = patched_get_running_loop
        logger.info("Successfully patched asyncio.get_running_loop")
        
    except ImportError:
        logger.warning("Could not import asyncio, patch not applied")
    except Exception as e:
        logger.error(f"Failed to patch asyncio: {str(e)}")
