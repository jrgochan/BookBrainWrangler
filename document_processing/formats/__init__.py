"""
Document format handlers for Book Knowledge AI.
"""

# Helper functions for document processing
def get_page_count(file_path: str) -> int:
    """
    Get the number of pages in a document.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Number of pages
    """
    import os
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        if ext == '.pdf':
            # PDF file
            from PyPDF2 import PdfReader
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                return len(reader.pages)
        
        elif ext in ['.docx', '.doc']:
            # DOCX file - estimate based on paragraphs
            import docx
            doc = docx.Document(file_path)
            return max(1, len(doc.paragraphs) // 40)  # Rough estimate
        
        elif ext == '.txt':
            # Text file - estimate based on lines
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                lines = file.readlines()
                return max(1, len(lines) // 50)  # Rough estimate
        
        else:
            # Unsupported file type
            return 0
    
    except:
        # Any error, return 0
        return 0

def extract_page_as_image(file_path: str, page_number: int, dpi: int = 200) -> bytes:
    """
    Extract a specific page from a document as an image.
    
    Args:
        file_path: Path to the document file
        page_number: Page number to extract (0-based)
        dpi: Resolution of the extracted image
        
    Returns:
        Image data in bytes or empty bytes if extraction fails
    """
    import os
    import io
    from PIL import Image
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        if ext == '.pdf':
            # PDF file
            from pdf2image import convert_from_path
            images = convert_from_path(
                file_path,
                dpi=dpi,
                fmt='jpeg',
                first_page=page_number + 1,  # pdf2image uses 1-based indexing
                last_page=page_number + 1
            )
            
            if images:
                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='JPEG')
                return img_byte_arr.getvalue()
        
        elif ext in ['.docx', '.doc']:
            # DOCX - no direct page extraction, would need to use Word automation
            # or render the whole document
            pass
        
        # Unsupported or failed extraction
        return bytes()
    
    except:
        # Any error, return empty bytes
        return bytes()