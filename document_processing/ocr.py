"""
OCR utilities for document processing.
"""

import os
import numpy as np
from typing import Tuple, Dict, List, Any, Optional
from PIL import Image

# Import PyTesseract for OCR
import pytesseract

# Import EasyOCR conditionally to handle environments where it might not be available
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

# OCR Engine options
OCR_ENGINES = {
    "pytesseract": "PyTesseract",
    "easyocr": "EasyOCR"
}

def detect_tesseract_path(settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Auto-detect Tesseract executable path based on platform.
    
    Args:
        settings: Dictionary containing OCR settings
        
    Returns:
        String path to Tesseract executable or None if not found
    """
    # First check if user provided a path in settings
    if settings and 'tesseract_path' in settings:
        user_path = settings['tesseract_path']
        if os.path.exists(user_path):
            logger.info(f"Using user-provided Tesseract path: {user_path}")
            return user_path
    
    # Detect operating system
    import platform
    system = platform.system().lower()
    
    # Define common Tesseract installation paths by platform
    common_paths = {
        'windows': [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ],
        'linux': [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ],
        'darwin': [  # macOS
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            '/opt/local/bin/tesseract',
        ]
    }
    
    # Get list of paths to check for current platform
    paths_to_check = common_paths.get(system, [])
    
    # Check if Tesseract is in the system PATH
    try:
        import shutil
        system_path = shutil.which('tesseract')
        if system_path:
            logger.info(f"Found Tesseract in system PATH: {system_path}")
            return system_path
    except Exception as e:
        logger.warning(f"Error checking system PATH for Tesseract: {str(e)}")
    
    # Check common installation locations
    for path in paths_to_check:
        if os.path.exists(path):
            logger.info(f"Found Tesseract at common location: {path}")
            return path
    
    # If we get here, we couldn't find Tesseract
    logger.warning(f"Could not find Tesseract executable on {system}")
    return None

def initialize_ocr_engine(ocr_engine: str, ocr_settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize the specified OCR engine with the provided settings.
    
    Args:
        ocr_engine: Name of the OCR engine to initialize
        ocr_settings: Dictionary of OCR-specific settings
    """
    ocr_settings = ocr_settings or {}
    
    if ocr_engine == "pytesseract":
        # Set the path to the Tesseract executable if it exists in settings
        tesseract_path = detect_tesseract_path(ocr_settings)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Using Tesseract executable at: {tesseract_path}")
        else:
            logger.warning("Tesseract path not found. Using system default, which may not work.")

def perform_ocr(image: Image.Image, ocr_engine: str, ocr_settings: Optional[Dict[str, Any]] = None) -> Tuple[str, float]:
    """
    Perform OCR on an image using the selected OCR engine.
    
    Args:
        image: PIL Image object to perform OCR on
        ocr_engine: The OCR engine to use ('pytesseract' or 'easyocr')
        ocr_settings: Dictionary of OCR-specific settings
        
    Returns:
        Tuple of (extracted_text, confidence)
    """
    extracted_text = ""
    confidence = 0.0
    ocr_settings = ocr_settings or {}
    
    try:
        if ocr_engine == "pytesseract":
            # Use PyTesseract for OCR
            extracted_text = pytesseract.image_to_string(image)
            # Get confidence score
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
            confidence = sum(confidences) / len(confidences) if confidences else 0.0
            logger.debug(f"PyTesseract OCR: {len(extracted_text)} chars, confidence: {confidence:.2f}%")
            
        elif ocr_engine == "easyocr" and EASYOCR_AVAILABLE:
            # Use EasyOCR for OCR
            languages = ocr_settings.get('languages', ['en'])
            
            # Create a global variable to store the reader
            global easyocr_reader
            
            # Initialize reader if not already done
            if not globals().get('easyocr_reader'):
                easyocr_reader = easyocr.Reader(languages)
                logger.info(f"Initialized EasyOCR with languages: {languages}")
            elif not all(lang in easyocr_reader.lang_list for lang in languages):
                # Reinitialize if languages changed
                easyocr_reader = easyocr.Reader(languages)
                logger.info(f"Reinitialized EasyOCR with languages: {languages}")
            
            # Convert PIL image to numpy array for EasyOCR
            img_array = np.array(image)
            
            # Perform OCR
            results = easyocr_reader.readtext(img_array)
            
            # Extract text and confidence from results
            if results:
                texts = []
                confidences = []
                for detection in results:
                    bbox, text, conf = detection
                    texts.append(text)
                    confidences.append(conf)
                
                extracted_text = " ".join(texts)
                confidence = sum(confidences) / len(confidences) * 100 if confidences else 0.0
                logger.debug(f"EasyOCR: {len(extracted_text)} chars, confidence: {confidence:.2f}%")
            else:
                logger.warning("EasyOCR returned no results")
        else:
            # Fallback to PyTesseract if EasyOCR is unavailable or unknown engine specified
            extracted_text = pytesseract.image_to_string(image)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
            confidence = sum(confidences) / len(confidences) if confidences else 0.0
            logger.warning(f"Fallback to PyTesseract due to unavailability of {ocr_engine}")
        
    except Exception as e:
        logger.error(f"Error in OCR processing: {str(e)}")
        # Return empty text and zero confidence on error
        return "", 0.0
        
    return extracted_text, confidence

# Define a global variable for the EasyOCR reader
# This will be initialized on first use
easyocr_reader = None