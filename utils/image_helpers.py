"""
Image processing utilities for Book Knowledge AI.
Provides functions for working with images.
"""

import io
import base64
from typing import Optional, Union, Tuple, List, Any
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def image_to_base64(image: Union[Image.Image, bytes], format: str = "JPEG") -> str:
    """
    Convert an image to base64 string.
    
    Args:
        image: PIL Image object or bytes of image data
        format: Image format (JPEG, PNG, etc.)
        
    Returns:
        Base64-encoded string representation of the image
    """
    if isinstance(image, Image.Image):
        # If it's a PIL Image, convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format)
        img_byte_arr = img_byte_arr.getvalue()
    else:
        # If it's already bytes, use as is
        img_byte_arr = image
    
    # Encode as base64
    encoded = base64.b64encode(img_byte_arr).decode('ascii')
    return encoded

def bytes_to_image(image_data: bytes) -> Optional[Image.Image]:
    """
    Convert image data bytes to a PIL Image.
    
    Args:
        image_data: Bytes containing image data
        
    Returns:
        PIL Image object or None if conversion fails
    """
    try:
        return Image.open(io.BytesIO(image_data))
    except UnidentifiedImageError:
        logger.error(f"Could not identify image format")
        return None
    except Exception as e:
        logger.error(f"Error converting bytes to image: {str(e)}")
        return None

def resize_image(image: Union[Image.Image, bytes], 
                width: Optional[int] = None, 
                height: Optional[int] = None,
                maintain_aspect_ratio: bool = True) -> Optional[Image.Image]:
    """
    Resize an image while optionally maintaining aspect ratio.
    
    Args:
        image: PIL Image object or bytes of image data
        width: Target width (if None, calculated from height)
        height: Target height (if None, calculated from width)
        maintain_aspect_ratio: Whether to maintain aspect ratio
        
    Returns:
        Resized PIL Image or None if resizing fails
    """
    try:
        # Convert to PIL Image if needed
        img = image if isinstance(image, Image.Image) else bytes_to_image(image)
        if img is None:
            return None
        
        # Calculate new dimensions
        original_width, original_height = img.size
        
        if width is None and height is None:
            # If neither width nor height is provided, return original
            return img
        
        if maintain_aspect_ratio:
            if width is not None and height is None:
                # Calculate height based on width
                ratio = width / original_width
                height = int(original_height * ratio)
            elif height is not None and width is None:
                # Calculate width based on height
                ratio = height / original_height
                width = int(original_width * ratio)
            elif width is not None and height is not None:
                # Both width and height provided, maintain aspect ratio by using smallest ratio
                width_ratio = width / original_width
                height_ratio = height / original_height
                ratio = min(width_ratio, height_ratio)
                width = int(original_width * ratio)
                height = int(original_height * ratio)
        else:
            # Use provided dimensions or original if not provided
            width = width if width is not None else original_width
            height = height if height is not None else original_height
        
        # Perform resizing
        return img.resize((width, height), Image.LANCZOS)
    
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return None

def add_watermark(image: Union[Image.Image, bytes], 
                 text: str, 
                 opacity: float = 0.5,
                 position: str = "center") -> Optional[Image.Image]:
    """
    Add a text watermark to an image.
    
    Args:
        image: PIL Image object or bytes of image data
        text: Watermark text
        opacity: Opacity of the watermark (0-1)
        position: Position of the watermark ("center", "top", "bottom", "top-left", etc.)
        
    Returns:
        PIL Image with watermark or None if process fails
    """
    try:
        # Convert to PIL Image if needed
        img = image if isinstance(image, Image.Image) else bytes_to_image(image)
        if img is None:
            return None
        
        # Create a transparent overlay for the watermark
        watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Try to get a font, use default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            font = ImageFont.load_default()
        
        # Calculate text size and position
        text_width, text_height = draw.textsize(text, font=font)
        
        # Calculate position based on specified parameter
        if position == "center":
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
        elif position == "top":
            x = (img.width - text_width) // 2
            y = 10
        elif position == "bottom":
            x = (img.width - text_width) // 2
            y = img.height - text_height - 10
        elif position == "top-left":
            x = 10
            y = 10
        elif position == "top-right":
            x = img.width - text_width - 10
            y = 10
        elif position == "bottom-left":
            x = 10
            y = img.height - text_height - 10
        elif position == "bottom-right":
            x = img.width - text_width - 10
            y = img.height - text_height - 10
        else:
            # Default to center
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
        
        # Draw text on the overlay with shadow for better visibility
        draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, int(255 * opacity)))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        
        # Convert the original image to RGBA if it's not already
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Composite the watermark onto the original image
        result = Image.alpha_composite(img, watermark)
        
        return result
    
    except Exception as e:
        logger.error(f"Error adding watermark: {str(e)}")
        return None

def crop_image(image: Union[Image.Image, bytes], 
             left: int, top: int, right: int, bottom: int) -> Optional[Image.Image]:
    """
    Crop an image to specified dimensions.
    
    Args:
        image: PIL Image object or bytes of image data
        left: Left coordinate for cropping
        top: Top coordinate for cropping
        right: Right coordinate for cropping
        bottom: Bottom coordinate for cropping
        
    Returns:
        Cropped PIL Image or None if cropping fails
    """
    try:
        # Convert to PIL Image if needed
        img = image if isinstance(image, Image.Image) else bytes_to_image(image)
        if img is None:
            return None
        
        # Ensure coordinates are within image bounds
        width, height = img.size
        left = max(0, min(left, width - 1))
        top = max(0, min(top, height - 1))
        right = max(left + 1, min(right, width))
        bottom = max(top + 1, min(bottom, height))
        
        # Crop the image
        return img.crop((left, top, right, bottom))
    
    except Exception as e:
        logger.error(f"Error cropping image: {str(e)}")
        return None

def rotate_image(image: Union[Image.Image, bytes], 
               angle: float, 
               expand: bool = True) -> Optional[Image.Image]:
    """
    Rotate an image by the specified angle.
    
    Args:
        image: PIL Image object or bytes of image data
        angle: Rotation angle in degrees (counter-clockwise)
        expand: Whether to expand the image to fit the rotated content
        
    Returns:
        Rotated PIL Image or None if rotation fails
    """
    try:
        # Convert to PIL Image if needed
        img = image if isinstance(image, Image.Image) else bytes_to_image(image)
        if img is None:
            return None
        
        # Rotate the image
        return img.rotate(angle, expand=expand, resample=Image.BICUBIC)
    
    except Exception as e:
        logger.error(f"Error rotating image: {str(e)}")
        return None

def create_thumbnail(file_path: str, 
                   width: int = 200, 
                   format: str = "JPEG") -> Optional[str]:
    """
    Create a thumbnail from an image file.
    
    Args:
        file_path: Path to the image file
        width: Width of the thumbnail
        format: Image format for the thumbnail
        
    Returns:
        Base64-encoded string of the thumbnail or None if creation fails
    """
    try:
        # Open the image file
        with Image.open(file_path) as img:
            # Create a copy to avoid modifying the original
            img_copy = img.copy()
            
            # Resize the image
            thumbnail = resize_image(img_copy, width=width)
            
            # Convert to base64
            if thumbnail:
                return image_to_base64(thumbnail, format=format)
            
            return None
    
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return None