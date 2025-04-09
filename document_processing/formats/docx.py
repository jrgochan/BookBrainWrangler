"""
DOCX document processor for Book Knowledge AI.
Handles extraction of text and images from DOCX files.
"""

import os
import io
import zipfile
from typing import Dict, List, Any, Optional, Callable, Union, BinaryIO
from pathlib import Path

import docx
from docx.document import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph
from docx.opc.constants import RELATIONSHIP_TYPE as RT

from utils.logger import get_logger
from core.exceptions import DocumentProcessingError

# Get a logger for this module
logger = get_logger(__name__)

def process_docx(file_path: str, include_images: bool = True, 
                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Process a DOCX file and extract its content.
    
    Args:
        file_path: Path to the DOCX file
        include_images: Whether to include images in the extraction
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary with extracted content:
        {
            'text': str,            # Full text content
            'images': List[bytes],  # List of image data in bytes
            'metadata': Dict        # Document metadata
        }
    """
    logger.info(f"Processing DOCX file: {file_path}")
    
    try:
        # Load the document
        doc = docx.Document(file_path)
        
        # Extract text content
        text_content = extract_text_from_docx(doc, progress_callback)
        
        # Extract images if requested
        images = []
        if include_images:
            images = extract_images_from_docx(file_path, progress_callback)
        
        # Extract metadata
        metadata = extract_metadata_from_docx(doc)
        
        # Return the extracted content
        return {
            'text': text_content,
            'images': images,
            'metadata': metadata
        }
    
    except Exception as e:
        logger.error(f"Error processing DOCX file: {str(e)}")
        raise DocumentProcessingError(f"Failed to process DOCX file: {str(e)}")

def extract_text_from_docx(doc: DocxDocument, 
                         progress_callback: Optional[Callable] = None) -> str:
    """
    Extract text from a DOCX document.
    
    Args:
        doc: The docx.Document object
        progress_callback: Optional callback for progress updates
        
    Returns:
        Extracted text content
    """
    # Get all paragraphs
    paragraphs = doc.paragraphs
    
    # Initialize an empty text string
    text = []
    
    # Calculate total number of paragraphs for progress tracking
    total_paragraphs = len(paragraphs)
    
    # Process each paragraph
    for i, paragraph in enumerate(paragraphs):
        # Skip empty paragraphs
        if paragraph.text.strip():
            text.append(paragraph.text)
        
        # Update progress
        if progress_callback and total_paragraphs > 0:
            progress = i / total_paragraphs
            progress_callback(i, total_paragraphs, {
                "text": f"Extracting text: paragraph {i+1}/{total_paragraphs}",
                "type": "text_extraction"
            })
    
    # Process tables
    for i, table in enumerate(doc.tables):
        # Add a paragraph break before table content
        text.append("\n")
        
        # Process each row and cell
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                # Get text from the cell
                cell_text = cell.text.strip()
                if cell_text:
                    row_text.append(cell_text)
            
            # Add the row text to the document text
            if row_text:
                text.append(" | ".join(row_text))
        
        # Add a paragraph break after table content
        text.append("\n")
        
        # Update progress
        if progress_callback:
            progress_callback(total_paragraphs + i, total_paragraphs + len(doc.tables), {
                "text": f"Extracting table {i+1}/{len(doc.tables)}",
                "type": "table_extraction"
            })
    
    # Join all paragraph texts with newlines
    return "\n".join(text)

def extract_images_from_docx(file_path: str, 
                           progress_callback: Optional[Callable] = None) -> List[bytes]:
    """
    Extract images from a DOCX file.
    
    Args:
        file_path: Path to the DOCX file
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of image data in bytes
    """
    images = []
    
    try:
        # DOCX files are ZIP files, so we can open them as such
        with zipfile.ZipFile(file_path) as zip_ref:
            # Get a list of all files in the ZIP
            file_list = zip_ref.namelist()
            
            # Filter for image files (in the word/media directory)
            image_files = [f for f in file_list if f.startswith('word/media/')]
            
            # Calculate total number of images for progress tracking
            total_images = len(image_files)
            
            # Extract each image
            for i, image_path in enumerate(image_files):
                # Read the image data
                with zip_ref.open(image_path) as image_file:
                    image_data = image_file.read()
                    images.append(image_data)
                
                # Update progress
                if progress_callback and total_images > 0:
                    progress = i / total_images
                    progress_callback(i, total_images, {
                        "text": f"Extracting image {i+1}/{total_images}",
                        "type": "image_extraction"
                    })
    
    except Exception as e:
        logger.warning(f"Error extracting images from DOCX: {str(e)}")
        # Continue with empty images list
    
    return images

def extract_metadata_from_docx(doc: DocxDocument) -> Dict[str, Any]:
    """
    Extract metadata from a DOCX document.
    
    Args:
        doc: The docx.Document object
        
    Returns:
        Dictionary with metadata
    """
    # Initialize an empty metadata dictionary
    metadata = {}
    
    try:
        # Get core properties
        core_properties = doc.core_properties
        
        # Extract available metadata
        if core_properties.title:
            metadata['title'] = core_properties.title
        
        if core_properties.author:
            metadata['author'] = core_properties.author
        
        if core_properties.subject:
            metadata['subject'] = core_properties.subject
        
        if core_properties.keywords:
            # Split keywords by commas or semicolons
            keywords = core_properties.keywords
            keyword_list = [k.strip() for k in keywords.replace(';', ',').split(',') if k.strip()]
            metadata['categories'] = keyword_list
        
        if core_properties.language:
            metadata['language'] = core_properties.language
        
        if core_properties.created:
            metadata['created'] = core_properties.created.isoformat()
        
        if core_properties.modified:
            metadata['modified'] = core_properties.modified.isoformat()
        
        if core_properties.last_modified_by:
            metadata['last_modified_by'] = core_properties.last_modified_by
    
    except Exception as e:
        logger.warning(f"Error extracting metadata from DOCX: {str(e)}")
        # Continue with partial metadata
    
    return metadata

def get_docx_thumbnail(file_path: str, width: int = 200) -> Optional[str]:
    """
    Generate a thumbnail for a DOCX file.
    Since DOCX files don't have natural thumbnails like PDFs,
    this function looks for the first image in the document.
    
    Args:
        file_path: Path to the DOCX file
        width: Width of the thumbnail in pixels
        
    Returns:
        Base64-encoded image data or None if generation fails
    """
    try:
        # Extract images from the DOCX file
        images = extract_images_from_docx(file_path)
        
        # If there are images, use the first one as the thumbnail
        if images:
            from utils.image_helpers import resize_image, image_to_base64
            
            # Get the first image
            image_data = images[0]
            
            # Resize the image
            resized_image = resize_image(image_data, width=width)
            
            # Convert to base64
            if resized_image:
                return image_to_base64(resized_image)
        
        # If no images found, return None
        return None
    
    except Exception as e:
        logger.error(f"Error creating DOCX thumbnail: {str(e)}")
        return None