"""
Main export functionality for knowledge base data.
"""

import json
from typing import Any, Optional, Tuple, Callable, Dict

from .common import EXPORT_FORMATS, logger
from .markdown import export_to_markdown
from .json import export_to_json
from .csv import export_to_csv
from .sqlite import export_to_sqlite

def export_knowledge_base(
    book_manager: Any, 
    knowledge_base: Any,
    format_type: str = "markdown",
    include_metadata: bool = True,
    include_content: bool = True,
    include_embeddings: bool = False,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bytes, str, str]:
    """
    Export knowledge base to the specified format.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        format_type: Format type ("markdown", "json", "csv", "sqlite")
        include_metadata: Whether to include book metadata
        include_content: Whether to include chunk content
        include_embeddings: Whether to include embedding vectors
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (file_data, filename, mime_type)
    """
    # Validate format type
    if format_type not in EXPORT_FORMATS:
        raise ValueError(f"Invalid format type: {format_type}")
    
    # Format info
    format_info = EXPORT_FORMATS[format_type]
    extension = format_info["extension"]
    mime_type = format_info["mime"]
    
    # Generate timestamp for filename
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"knowledge_base_export_{timestamp}.{extension}"
    
    # Update progress
    if progress_callback:
        progress_callback(0.05, f"Starting export in {format_info['name']} format")
    
    # Get indexed books
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    
    if not kb_book_ids:
        # No books in knowledge base
        if format_type == "markdown":
            return "# Knowledge Base Export\n\nNo books in knowledge base.".encode('utf-8'), filename, mime_type
        elif format_type == "json":
            data = {
                "metadata": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "books": 0,
                    "chunks": 0
                },
                "books": []
            }
            return json.dumps(data, indent=2).encode('utf-8'), filename, mime_type
        else:
            # For other formats, use a placeholder
            return f"No books in knowledge base.".encode('utf-8'), filename, mime_type
    
    # Based on format type, call appropriate export function
    if format_type == "markdown":
        content = export_to_markdown(book_manager, knowledge_base, include_metadata, include_content, include_embeddings, progress_callback)
        return content.encode('utf-8'), filename, mime_type
    elif format_type == "json":
        content = export_to_json(book_manager, knowledge_base, include_metadata, include_content, include_embeddings, progress_callback)
        return json.dumps(content, indent=2).encode('utf-8'), filename, mime_type
    elif format_type == "csv":
        file_data = export_to_csv(book_manager, knowledge_base, include_metadata, include_content, include_embeddings, progress_callback)
        return file_data, filename, mime_type
    elif format_type == "sqlite":
        file_data = export_to_sqlite(book_manager, knowledge_base, include_metadata, include_content, include_embeddings, progress_callback)
        return file_data, filename, mime_type
    else:
        raise ValueError(f"Export format not implemented: {format_type}")
