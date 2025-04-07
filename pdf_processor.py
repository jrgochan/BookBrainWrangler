import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import os
import tempfile

class PDFProcessor:
    def __init__(self):
        """Initialize the PDF processor with default settings."""
        # Configure pytesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Uncomment and modify if needed
        pass
    
    def extract_text(self, pdf_path):
        """
        Extract text from a PDF file.
        First tries direct text extraction, then falls back to OCR if needed.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        # First try direct text extraction
        extracted_text = self._extract_text_direct(pdf_path)
        
        # If the PDF has little or no text, it might be a scanned document
        # In that case, use OCR to extract the text
        if not extracted_text or len(extracted_text.strip()) < 100:  # Arbitrary threshold
            extracted_text = self._extract_text_ocr(pdf_path)
        
        return extracted_text
    
    def _extract_text_direct(self, pdf_path):
        """
        Attempt to extract text directly from the PDF without OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    text += page.extract_text() or ""
            
            return text
            
        except Exception as e:
            print(f"Error extracting text directly: {e}")
            return ""
    
    def _extract_text_ocr(self, pdf_path):
        """
        Extract text from a PDF using OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            text = ""
            
            # Create a temporary directory to store the image files
            with tempfile.TemporaryDirectory() as path:
                # Convert PDF pages to images
                images = convert_from_path(pdf_path)
                
                # Process each page image with OCR
                for i, image in enumerate(images):
                    # Save the image temporarily
                    image_path = os.path.join(path, f'page_{i}.png')
                    image.save(image_path, 'PNG')
                    
                    # Extract text from the image
                    page_text = pytesseract.image_to_string(image_path)
                    text += page_text + "\n\n"
            
            return text
            
        except Exception as e:
            print(f"Error extracting text with OCR: {e}")
            return ""
    
    def get_page_count(self, pdf_path):
        """
        Get the number of pages in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages as an integer
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return len(reader.pages)
                
        except Exception as e:
            print(f"Error getting page count: {e}")
            return 0
