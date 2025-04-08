import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import os
import tempfile
import docx
import mimetypes

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with default settings."""
        # Configure pytesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Uncomment and modify if needed
        
        # Register the DOCX MIME type if it's not already registered
        if not mimetypes.inited:
            mimetypes.init()
        if '.docx' not in mimetypes.types_map:
            mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
    
    def extract_text(self, file_path, progress_callback=None):
        """
        Extract text from a document file (PDF or DOCX).
        For PDFs: First tries direct text extraction, then falls back to OCR if needed.
        For DOCX: Uses python-docx to extract text.
        
        Args:
            file_path: Path to the document file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        # Determine file type based on extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if progress_callback:
            progress_callback(0, 1, f"Detected file type: {file_ext}")
        
        # Process based on file type
        if file_ext == '.pdf':
            return self._process_pdf(file_path, progress_callback)
        elif file_ext == '.docx':
            return self._process_docx(file_path, progress_callback)
        else:
            if progress_callback:
                progress_callback(0, 1, f"Unsupported file type: {file_ext}")
            raise ValueError(f"Unsupported file type: {file_ext}. Only PDF and DOCX files are supported.")
    
    def _process_pdf(self, pdf_path, progress_callback=None):
        """
        Process a PDF file and extract text.
        
        Args:
            pdf_path: Path to the PDF file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        # Get total page count for progress tracking
        total_pages = self.get_page_count(pdf_path)
        
        # Update progress
        if progress_callback:
            progress_callback(0, total_pages, "Starting PDF text extraction")
        
        # First try direct text extraction
        if progress_callback:
            progress_callback(0, total_pages, "Attempting direct text extraction")
        
        extracted_text = self._extract_text_direct(pdf_path, progress_callback)
        
        # If the PDF has little or no text, it might be a scanned document
        # In that case, use OCR to extract the text
        if not extracted_text or len(extracted_text.strip()) < 100:  # Arbitrary threshold
            if progress_callback:
                progress_callback(0, total_pages, "Direct extraction yielded little text, switching to OCR")
            extracted_text = self._extract_text_ocr(pdf_path, progress_callback)
        
        # Final progress update
        if progress_callback:
            progress_callback(total_pages, total_pages, "Text extraction complete")
        
        return extracted_text
        
    def _process_docx(self, docx_path, progress_callback=None):
        """
        Process a DOCX file and extract text.
        
        Args:
            docx_path: Path to the DOCX file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        if progress_callback:
            progress_callback(0, 3, "Opening DOCX document")
            
        try:
            # Open the docx file
            doc = docx.Document(docx_path)
            
            if progress_callback:
                progress_callback(1, 3, f"Processing DOCX with {len(doc.paragraphs)} paragraphs")
            
            # Extract text from paragraphs
            full_text = []
            for i, para in enumerate(doc.paragraphs):
                if para.text:
                    full_text.append(para.text)
                
                # Update progress periodically (every 10 paragraphs)
                if progress_callback and i % 10 == 0 and len(doc.paragraphs) > 0:
                    progress = min(1 + (i / len(doc.paragraphs)), 2)
                    progress_callback(progress, 3, f"Processed {i}/{len(doc.paragraphs)} paragraphs")
            
            if progress_callback:
                progress_callback(2, 3, "Processing tables")
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text:
                            row_text.append(cell.text)
                    if row_text:
                        full_text.append(" | ".join(row_text))
            
            # Final progress update
            if progress_callback:
                progress_callback(3, 3, "DOCX text extraction complete")
                
            return "\n".join(full_text)
            
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            if progress_callback:
                progress_callback(0, 3, f"Error in DOCX processing: {e}")
            return ""
    
    def _extract_text_direct(self, pdf_path, progress_callback=None):
        """
        Attempt to extract text directly from the PDF without OCR.
        
        Args:
            pdf_path: Path to the PDF file
            progress_callback: Optional callback function for progress updates
            
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
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(page_num + 1, num_pages, f"Direct extraction: Processing page {page_num + 1}/{num_pages}")
            
            return text
            
        except Exception as e:
            print(f"Error extracting text directly: {e}")
            if progress_callback:
                progress_callback(0, 1, f"Error in direct extraction: {e}")
            return ""
    
    def _extract_text_ocr(self, pdf_path, progress_callback=None):
        """
        Extract text from a PDF using OCR.
        
        Args:
            pdf_path: Path to the PDF file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        try:
            text = ""
            
            # Create a temporary directory to store the image files
            with tempfile.TemporaryDirectory() as path:
                # Update progress
                if progress_callback:
                    progress_callback(0, 1, "Converting PDF pages to images for OCR")
                
                # Convert PDF pages to images
                images = convert_from_path(pdf_path)
                total_images = len(images)
                
                if progress_callback:
                    progress_callback(0, total_images, f"Starting OCR on {total_images} pages")
                
                # Process each page image with OCR
                for i, image in enumerate(images):
                    # Save the image temporarily
                    image_path = os.path.join(path, f'page_{i}.png')
                    image.save(image_path, 'PNG')
                    
                    # Update progress before OCR (which can be time-consuming)
                    if progress_callback:
                        progress_callback(i, total_images, f"OCR: Processing page {i + 1}/{total_images}")
                    
                    # Extract text from the image
                    page_text = pytesseract.image_to_string(image_path)
                    text += page_text + "\n\n"
                    
                    # Update progress after OCR completion for this page
                    if progress_callback:
                        progress_callback(i + 1, total_images, f"OCR: Completed page {i + 1}/{total_images}")
            
            return text
            
        except Exception as e:
            print(f"Error extracting text with OCR: {e}")
            if progress_callback:
                progress_callback(0, 1, f"Error in OCR processing: {e}")
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
