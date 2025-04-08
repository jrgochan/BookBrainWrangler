import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import os
import tempfile
import docx
import mimetypes
import base64
import io
from PIL import Image

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
    
    def extract_content(self, file_path, include_images=True, progress_callback=None):
        """
        Extract text and optionally images from a document file (PDF or DOCX).
        
        Args:
            file_path: Path to the document file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        # Determine file type based on extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if progress_callback:
            progress_callback(0, 1, f"Detected file type: {file_ext}")
        
        # Process based on file type
        if file_ext == '.pdf':
            return self._process_pdf(file_path, include_images, progress_callback)
        elif file_ext == '.docx':
            return self._process_docx(file_path, include_images, progress_callback)
        else:
            if progress_callback:
                progress_callback(0, 1, f"Unsupported file type: {file_ext}")
            raise ValueError(f"Unsupported file type: {file_ext}. Only PDF and DOCX files are supported.")
    
    def extract_text(self, file_path, progress_callback=None):
        """
        Legacy method to extract only text from a document file.
        Maintained for backward compatibility.
        
        Args:
            file_path: Path to the document file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        content = self.extract_content(file_path, include_images=False, progress_callback=progress_callback)
        return content['text']
    
    def _process_pdf(self, pdf_path, include_images=True, progress_callback=None):
        """
        Process a PDF file and extract text and optionally images.
        
        Args:
            pdf_path: Path to the PDF file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        # Get total page count for progress tracking
        total_pages = self.get_page_count(pdf_path)
        
        # Helper to handle both string and dict message formats
        def send_progress(current, total, message):
            if progress_callback:
                if isinstance(message, str):
                    # Convert string messages to dict format for consistency
                    progress_callback(current, total, {"text": message})
                else:
                    # Already a dict, pass it through
                    progress_callback(current, total, message)
        
        # Update progress
        send_progress(0, total_pages, "Starting PDF content extraction")
        
        # First try direct text extraction
        send_progress(0, total_pages, "Attempting direct text extraction")
        
        extracted_text = self._extract_text_direct(pdf_path, send_progress)
        
        # If the PDF has little or no text, it might be a scanned document
        # In that case, use OCR to extract the text
        use_ocr = False
        if not extracted_text or len(extracted_text.strip()) < 100:  # Arbitrary threshold
            send_progress(0, total_pages, {
                "text": "Direct extraction yielded little text, switching to OCR",
                "action": "switching_to_ocr"
            })
            extracted_text = self._extract_text_ocr(pdf_path, progress_callback)
            use_ocr = True
        
        # Extract images if requested
        extracted_images = []
        if include_images:
            send_progress(0, total_pages, {
                "text": "Starting image extraction from PDF",
                "action": "extracting_images"
            })
            
            extracted_images = self._extract_images_from_pdf(pdf_path, total_pages, send_progress)
            
            send_progress(total_pages, total_pages, {
                "text": f"Extracted {len(extracted_images)} images",
                "action": "images_extracted",
                "image_count": len(extracted_images)
            })
        
        # Final progress update
        send_progress(total_pages, total_pages, {
            "text": "PDF content extraction complete",
            "action": "complete",
            "used_ocr": use_ocr,
            "image_count": len(extracted_images),
            "text_length": len(extracted_text)
        })
        
        return {
            'text': extracted_text,
            'images': extracted_images
        }
        
    def _process_docx(self, docx_path, include_images=True, progress_callback=None):
        """
        Process a DOCX file and extract text and optionally images.
        
        Args:
            docx_path: Path to the DOCX file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        if progress_callback:
            progress_callback(0, 4, "Opening DOCX document")
            
        try:
            # Open the docx file
            doc = docx.Document(docx_path)
            
            if progress_callback:
                progress_callback(1, 4, f"Processing DOCX with {len(doc.paragraphs)} paragraphs")
            
            # Extract text from paragraphs
            full_text = []
            for i, para in enumerate(doc.paragraphs):
                if para.text:
                    full_text.append(para.text)
                
                # Update progress periodically (every 10 paragraphs)
                if progress_callback and i % 10 == 0 and len(doc.paragraphs) > 0:
                    progress = min(1 + (i / len(doc.paragraphs)), 2)
                    progress_callback(progress, 4, f"Processed {i}/{len(doc.paragraphs)} paragraphs")
            
            if progress_callback:
                progress_callback(2, 4, "Processing tables")
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text:
                            row_text.append(cell.text)
                    if row_text:
                        full_text.append(" | ".join(row_text))
            
            # Extract images if requested
            extracted_images = []
            if include_images:
                if progress_callback:
                    progress_callback(3, 4, "Extracting images from DOCX")
                
                extracted_images = self._extract_images_from_docx(doc, progress_callback)
                
                if progress_callback:
                    progress_callback(3.5, 4, f"Extracted {len(extracted_images)} images")
            
            # Final progress update
            if progress_callback:
                progress_callback(4, 4, "DOCX content extraction complete")
            
            return {
                'text': "\n".join(full_text),
                'images': extracted_images
            }
            
        except Exception as e:
            print(f"Error extracting content from DOCX: {e}")
            if progress_callback:
                progress_callback(0, 4, f"Error in DOCX processing: {e}")
            return {'text': "", 'images': []}
    
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
                The callback can receive these additional parameters in the 'message' dict:
                - 'current_image': base64 string of the current image being processed
                - 'ocr_text': extracted text from the current image
                - 'confidence': estimated OCR confidence for the current page
                - 'action': what's happening ('extracting', 'processing', 'completed')
            
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
                    
                    # Convert current image to base64 for display in UI
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='JPEG', quality=85)
                    img_buffer.seek(0)
                    img_str = base64.b64encode(img_buffer.read()).decode('utf-8')
                    
                    # Update progress before OCR (which can be time-consuming)
                    if progress_callback:
                        progress_callback(i, total_images, {
                            "text": f"OCR: Processing page {i + 1}/{total_images}",
                            "current_image": img_str,
                            "action": "processing"
                        })
                    
                    # Extract text from the image with confidence data
                    ocr_data = pytesseract.image_to_data(image_path, output_type=pytesseract.Output.DICT)
                    
                    # Extract the plain text
                    page_text = pytesseract.image_to_string(image_path)
                    
                    # Calculate average confidence for this page
                    conf_values = [conf for conf in ocr_data.get('conf', []) if conf != -1]  # Filter out -1 values
                    avg_confidence = sum(conf_values) / len(conf_values) if conf_values else 0
                    
                    # Add the text to our full document text
                    text += page_text + "\n\n"
                    
                    # Update progress after OCR completion for this page with the OCR text and confidence
                    if progress_callback:
                        progress_callback(i + 1, total_images, {
                            "text": f"OCR: Completed page {i + 1}/{total_images}",
                            "current_image": img_str,
                            "ocr_text": page_text.strip(),
                            "confidence": avg_confidence,
                            "action": "completed"
                        })
            
            return text
            
        except Exception as e:
            print(f"Error extracting text with OCR: {e}")
            if progress_callback:
                progress_callback(0, 1, f"Error in OCR processing: {e}")
            return ""
    
    def _extract_images_from_pdf(self, pdf_path, total_pages, progress_callback=None):
        """
        Extract images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            total_pages: Total number of pages in the PDF
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of dictionaries with image data:
            [
                {
                    'page': page number,
                    'index': image index on page,
                    'description': brief description,
                    'data': base64-encoded image data
                },
                ...
            ]
        """
        extracted_images = []
        
        try:
            # Method 1: Extract images using pdf2image (converts pages to images)
            with tempfile.TemporaryDirectory() as path:
                if progress_callback:
                    progress_callback(0, total_pages, "Converting PDF pages to images")
                
                # Convert all pages to images
                page_images = convert_from_path(pdf_path)
                
                # Process each page image
                for i, image in enumerate(page_images):
                    if progress_callback:
                        progress_callback(i, total_pages, f"Processing image from page {i+1}/{len(page_images)}")
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='JPEG', quality=85)
                    img_buffer.seek(0)
                    
                    # Convert to base64
                    img_str = base64.b64encode(img_buffer.read()).decode('utf-8')
                    
                    # Add to extracted images
                    extracted_images.append({
                        'page': i + 1,
                        'index': 0,  # Main page image
                        'description': f"Page {i+1} content",
                        'data': img_str
                    })
            
            # Method 2 (Alternative): Try to extract embedded images using PyPDF2
            # This could get native images that might be of higher quality in some PDFs
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    
                    # Check each page for XObject images
                    for page_num, page in enumerate(reader.pages):
                        if '/XObject' in page['/Resources']:
                            xobjects = page['/Resources']['/XObject']
                            
                            # Skip if we already have progress callback reporting
                            if not progress_callback:
                                print(f"Processing embedded images on page {page_num+1}")
                                
                            # Extract each image on the page
                            for idx, (name, image) in enumerate(xobjects.items()):
                                if image['/Subtype'] == '/Image':
                                    # Extract the image data (this is a simplified approach)
                                    # In a real implementation, you'd handle different encodings properly
                                    if '/Filter' in image and '/DCTDecode' in image['/Filter']:
                                        # This is a JPEG image
                                        img_data = image._data
                                        img_str = base64.b64encode(img_data).decode('utf-8')
                                        
                                        extracted_images.append({
                                            'page': page_num + 1,
                                            'index': idx + 1,
                                            'description': f"Embedded image on page {page_num+1}",
                                            'data': img_str
                                        })
            except Exception as e:
                print(f"Error extracting embedded images (non-critical): {e}")
                # This is a best-effort extraction, so we continue even if it fails
            
            if progress_callback:
                progress_callback(total_pages, total_pages, f"Extracted {len(extracted_images)} images from PDF")
                
            return extracted_images
            
        except Exception as e:
            print(f"Error extracting images from PDF: {e}")
            if progress_callback:
                progress_callback(0, 1, f"Error extracting images: {e}")
            return []
    
    def _extract_images_from_docx(self, doc, progress_callback=None):
        """
        Extract images from a DOCX document.
        
        Args:
            doc: docx.Document object
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of dictionaries with image data similar to _extract_images_from_pdf
        """
        extracted_images = []
        
        try:
            # DOCX stores images as "relationships"
            rels = doc.part.rels
            
            total_rels = len(rels)
            processed = 0
            
            for rel_id, rel in rels.items():
                processed += 1
                
                # Only process image relationships
                if "image" in rel.target_ref:
                    if progress_callback:
                        progress_callback(3 + (processed / total_rels * 0.5), 4, 
                                         f"Extracting image {processed}/{total_rels}")
                    
                    # Get the image data
                    image_part = rel.target_part
                    image_data = image_part.blob
                    
                    # Convert to base64
                    img_str = base64.b64encode(image_data).decode('utf-8')
                    
                    # Add to extracted images
                    extracted_images.append({
                        'page': 1,  # DOCX doesn't have pages in the same way as PDF
                        'index': processed,
                        'description': f"Image {processed} from document",
                        'data': img_str
                    })
            
            return extracted_images
            
        except Exception as e:
            print(f"Error extracting images from DOCX: {e}")
            if progress_callback:
                progress_callback(3, 4, f"Error extracting images: {e}")
            return []
    
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
