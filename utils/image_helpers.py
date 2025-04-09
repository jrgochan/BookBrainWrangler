"""
Image processing and generation utilities.
"""

import os
import io
import base64
from typing import Tuple, List, Optional, Any

from PIL import Image, ImageDraw, ImageFont
from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def generate_thumbnail(file_path: str, max_size: Tuple[int, int] = (200, 280), quality: int = 85) -> str:
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
                else:
                    # No images were generated from the PDF
                    return generate_placeholder_thumbnail("PDF", max_size)
            except Exception as e:
                logger.error(f"Error converting PDF to image: {e}")
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
        logger.error(f"Error generating thumbnail: {e}")
        return generate_placeholder_thumbnail("Error", max_size)

def generate_placeholder_thumbnail(text: str, size: Tuple[int, int] = (200, 280), 
                                  bg_color: Tuple[int, int, int] = (240, 240, 240), 
                                  text_color: Tuple[int, int, int] = (70, 70, 70)) -> str:
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

def wrap_text(text: str, font: Any, max_width: int) -> List[str]:
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