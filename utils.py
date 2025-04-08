import re
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont

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

def generate_thumbnail(file_path, max_size=(200, 280), quality=85):
    """
    Generate a thumbnail image from a PDF or DOCX file.
    For PDFs, takes the first page as the thumbnail.
    For DOCX, generates a placeholder with the document title.
    
    Args:
        file_path: Path to the file
        max_size: Maximum thumbnail dimensions (width, height)
        quality: JPEG quality (1-100)
        
    Returns:
        Base64 encoded string of the thumbnail image
    """
    if not os.path.exists(file_path):
        return generate_placeholder_thumbnail("File Not Found", max_size)
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            # For PDFs, attempt to use pdf2image to convert first page to image
            try:
                import pdf2image
                
                # Convert the first page of the PDF to an image
                images = pdf2image.convert_from_path(
                    file_path, 
                    first_page=1, 
                    last_page=1, 
                    size=max_size
                )
                
                if images:
                    img = images[0]
                    # Convert to RGB if it's not already (in case it's RGBA or other format)
                    img = img.convert('RGB')
                    
                    # Resize the image to fit within max_size while maintaining aspect ratio
                    img.thumbnail(max_size)
                    
                    # Save to a byte buffer
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=quality)
                    buffer.seek(0)
                    
                    # Convert to base64
                    return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
            except Exception as e:
                print(f"Error converting PDF to image: {e}")
                # Fall back to placeholder with PDF label
                return generate_placeholder_thumbnail("PDF", max_size)
                
        elif file_ext == '.docx':
            # For DOCX, extract title from the filename and generate a placeholder
            title = os.path.basename(file_path).replace('.docx', '')
            return generate_placeholder_thumbnail(f"DOCX: {title}", max_size)
        else:
            # For unsupported formats, return a placeholder
            return generate_placeholder_thumbnail(f"File: {os.path.basename(file_path)}", max_size)
            
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return generate_placeholder_thumbnail("Error", max_size)

def generate_placeholder_thumbnail(text, size=(200, 280), bg_color=(240, 240, 240), text_color=(70, 70, 70)):
    """
    Generate a placeholder thumbnail with text.
    
    Args:
        text: Text to display on the placeholder
        size: Size of the thumbnail (width, height)
        bg_color: Background color as RGB tuple
        text_color: Text color as RGB tuple
        
    Returns:
        Base64 encoded string of the placeholder image
    """
    # Create a blank image
    img = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add a border
    border_width = 2
    draw.rectangle(
        (border_width, border_width, 
         size[0] - border_width, size[1] - border_width), 
        outline=(200, 200, 200), 
        width=border_width
    )
    
    # Determine font size based on image size
    font_size = max(10, size[0] // 10)  # Minimum 10px, or proportional to width
    
    # Try to use a system font, or fall back to default
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except:
        # Fall back to default font
        font = ImageFont.load_default()
    
    # Wrap text to fit within the image width
    wrapped_text = wrap_text(text, font, size[0] - 20)
    
    # Calculate text position to center it
    text_height = 0
    for line in wrapped_text:
        # Get text dimensions using the textbbox method (for newer PIL versions)
        try:
            # For newer PIL versions
            bbox = font.getbbox(line)
            line_height = bbox[3] - bbox[1]
        except AttributeError:
            # For older PIL versions, try textlength and fallback to approximation
            try:
                line_height = font_size + 4  # Approximate height based on font size
            except:
                line_height = font_size  # Fallback
        
        text_height += line_height + 5  # 5px line spacing
    
    y = (size[1] - text_height) // 2
    
    # Draw each line of text
    for line in wrapped_text:
        try:
            # Get text width for centering
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback using approximate width
            line_width = len(line) * (font_size // 2)  # Approximate width
            line_height = font_size + 4  # Approximate height
        
        x = (size[0] - line_width) // 2
        
        # Draw text with a subtle shadow for better visibility
        draw.text((x+1, y+1), line, font=font, fill=(30, 30, 30))
        draw.text((x, y), line, font=font, fill=text_color)
        
        y += line_height + 5  # 5px line spacing
    
    # Save to a byte buffer
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    
    # Convert to base64
    return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

def wrap_text(text, font, max_width):
    """
    Wrap text to fit within a given width.
    
    Args:
        text: Text to wrap
        font: Font to use for measuring text width
        max_width: Maximum width in pixels
        
    Returns:
        List of wrapped text lines
    """
    words = text.split(' ')
    wrapped_lines = []
    current_line = []
    
    for word in words:
        # Add the word to the current line
        current_line.append(word)
        
        # Check if the current line is too wide
        line = ' '.join(current_line)
        
        # Get line width using either getbbox or approximation
        try:
            # For newer PIL versions
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
        except AttributeError:
            # Fallback approximation
            try:
                # For older PIL versions that might have getsize
                try:
                    line_width = font.getsize(line)[0]
                except:
                    # Last resort: approximate based on character count
                    line_width = len(line) * (font.size // 2)
            except:
                # Very basic approximation if all else fails
                line_width = len(line) * 6
        
        if line_width > max_width:
            # Remove the last word
            if len(current_line) > 1:
                last_word = current_line.pop()
                wrapped_lines.append(' '.join(current_line))
                current_line = [last_word]
            else:
                # If a single word is longer than max_width, we have to keep it on its own line
                wrapped_lines.append(line)
                current_line = []
    
    # Add the last line if there's anything left
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    
    return wrapped_lines
