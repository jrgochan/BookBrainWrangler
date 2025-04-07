import re

def cleanup_text(text):
    """
    Clean up extracted text from PDFs.
    
    Args:
        text: The raw text extracted from a PDF
        
    Returns:
        Cleaned up text
    """
    if not text:
        return ""
    
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Fix common OCR issues
    text = text.replace('|', 'I')  # Vertical bar often misrecognized as I
    text = text.replace('l', 'l')  # Lowercase L often misrecognized
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)  # Fix hyphenated words at line breaks
    
    # Remove page numbers (common in scanned books)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # Fix missing spaces after periods
    text = re.sub(r'(\w)\.(\w)', r'\1. \2', text)
    
    return text.strip()

def extract_metadata_from_pdf(pdf_path):
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with metadata fields
    """
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            info = reader.metadata
            
            if info:
                metadata = {
                    'title': info.get('/Title', ''),
                    'author': info.get('/Author', ''),
                    'subject': info.get('/Subject', ''),
                    'creator': info.get('/Creator', ''),
                    'producer': info.get('/Producer', ''),
                    'creation_date': info.get('/CreationDate', '')
                }
                return {k: v for k, v in metadata.items() if v}
            
        return {}
            
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {}

def chunk_large_text(text, max_chunk_size=4000):
    """
    Split very large text into manageable chunks for processing.
    
    Args:
        text: The large text to chunk
        max_chunk_size: Maximum size per chunk
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # Try to split at paragraph boundaries
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            # If the current chunk has content, add it to chunks
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Start a new chunk
            current_chunk = para + "\n\n"
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If any chunk is still too large, use a more aggressive splitting
    result = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            result.append(chunk)
        else:
            # Split at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_chunk_size:
                    current_chunk += sentence + " "
                else:
                    # Add the current chunk if it has content
                    if current_chunk:
                        result.append(current_chunk.strip())
                    
                    # If a single sentence is too long, split it by words
                    if len(sentence) > max_chunk_size:
                        words = sentence.split()
                        current_chunk = ""
                        
                        for word in words:
                            if len(current_chunk) + len(word) <= max_chunk_size:
                                current_chunk += word + " "
                            else:
                                result.append(current_chunk.strip())
                                current_chunk = word + " "
                    else:
                        current_chunk = sentence + " "
            
            # Add the last part if it has content
            if current_chunk:
                result.append(current_chunk.strip())
    
    return result
