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

def generate_knowledge_export(book_manager, knowledge_base, query=None, include_content=True, max_topics=5, max_books=None):
    """
    Generate a markdown export of insights from the knowledge base.
    
    Args:
        book_manager: BookManager instance to get book details
        knowledge_base: KnowledgeBase instance to retrieve content
        query: Optional query to focus the export on a specific topic
               If None, will generate insights about key topics
        include_content: Whether to include book content excerpts
        max_topics: Maximum number of topics/sections to include
        max_books: Maximum number of books to include (None for all)
        
    Returns:
        A string containing the markdown export
    """
    import datetime
    from database import get_connection
    
    # Get books in knowledge base
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    if not kb_book_ids:
        return "# Knowledge Base Export\n\nNo books in knowledge base."
    
    # Limit to max_books if specified
    if max_books is not None and max_books > 0:
        kb_book_ids = kb_book_ids[:max_books]
    
    # Get book details
    conn = get_connection()
    cursor = conn.cursor()
    
    books_info = []
    for book_id in kb_book_ids:
        cursor.execute('SELECT id, title, author, categories FROM books WHERE id = ?', (book_id,))
        book = cursor.fetchone()
        if book:
            book_id, title, author, categories_str = book
            categories = categories_str.split(',') if categories_str else []
            books_info.append({
                'id': book_id,
                'title': title,
                'author': author,
                'categories': categories
            })
    
    conn.close()
    
    # Start generating the markdown content
    now = datetime.datetime.now()
    markdown = []
    
    # Header
    markdown.append("# Knowledge Base Export")
    markdown.append(f"Generated on {now.strftime('%Y-%m-%d at %H:%M')}")
    markdown.append("")
    
    # Books included
    markdown.append("## Books Included")
    for book in books_info:
        markdown.append(f"- **{book['title']}** by *{book['author']}* ({', '.join(book['categories'])})")
    markdown.append("")
    
    # If query is provided, focus on that topic
    if query:
        markdown.append(f"## Insights on: {query}")
        context = knowledge_base.retrieve_relevant_context(query, num_results=10)
        
        # Format the context as markdown
        if context:
            # Split into paragraphs
            paragraphs = context.split('\n\n')
            for i, para in enumerate(paragraphs):
                if para.strip():
                    markdown.append(f"### Excerpt {i+1}")
                    markdown.append(para.strip())
                    markdown.append("")
        else:
            markdown.append("No relevant information found in the knowledge base.")
    else:
        # Generate insights on key topics/categories
        all_categories = set()
        for book in books_info:
            all_categories.update(book['categories'])
        
        # Take the most common categories
        categories_to_use = list(all_categories)[:max_topics]
        
        for category in categories_to_use:
            markdown.append(f"## Insights on: {category}")
            context = knowledge_base.retrieve_relevant_context(category, num_results=5)
            
            # Format the context as markdown
            if context:
                # Split into paragraphs
                paragraphs = context.split('\n\n')
                for i, para in enumerate(paragraphs[:3]):  # Limit to 3 paragraphs per category
                    if para.strip():
                        markdown.append(f"### Excerpt {i+1}")
                        markdown.append(para.strip())
                        markdown.append("")
            else:
                markdown.append("No specific insights found for this topic.")
            
            markdown.append("")
    
    # Include additional section with book-specific excerpts if requested
    if include_content:
        markdown.append("## Book Excerpts")
        for book in books_info:
            markdown.append(f"### From: {book['title']} by {book['author']}")
            
            # Get a representative excerpt from this book
            book_query = f"key points from {book['title']} by {book['author']}"
            context = knowledge_base.retrieve_relevant_context(book_query, num_results=1)
            
            if context:
                markdown.append(context.strip())
            else:
                markdown.append("No representative excerpt available.")
            
            markdown.append("")
    
    # Join all the markdown lines and return
    return "\n".join(markdown)

def save_markdown_to_file(markdown_content, file_path=None):
    """
    Save markdown content to a file.
    
    Args:
        markdown_content: The markdown content as a string
        file_path: Path where to save the file (if None, generates a default name)
        
    Returns:
        Path to the saved file
    """
    import tempfile
    import datetime
    import os
    
    if not file_path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"knowledge_export_{timestamp}.md"
        
        # If in a web context, save to a temp directory that's accessible
        if not os.access(os.path.dirname(file_path) or ".", os.W_OK):
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, file_path)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        return file_path
    except Exception as e:
        print(f"Error saving markdown file: {e}")
        return None

def generate_word_cloud(text, max_words=200, width=800, height=400, background_color='white', 
                      colormap='viridis', stopwords=None, mask=None, min_font_size=10,
                      max_font_size=None, include_numbers=False):
    """
    Generate a word cloud image from text content.
    
    Args:
        text: Text content to generate word cloud from
        max_words: Maximum number of words to include
        width: Width of the output image
        height: Height of the output image
        background_color: Background color name or hex code
        colormap: Matplotlib colormap name
        stopwords: Additional stopwords to exclude (list of strings)
        mask: Optional numpy array mask for custom shape (if None, uses rectangle)
        min_font_size: Minimum font size
        max_font_size: Maximum font size (if None, auto-calculated)
        include_numbers: Whether to include numbers in the word cloud
        
    Returns:
        Base64 encoded string of the word cloud image
    """
    import io
    import base64
    import numpy as np
    from wordcloud import WordCloud, STOPWORDS
    import matplotlib.pyplot as plt
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords as nltk_stopwords
    
    # Guard against empty text
    if not text or len(text.strip()) == 0:
        return None
        
    # Combine NLTK and WordCloud stopwords
    combined_stopwords = set(STOPWORDS)
    try:
        # Add NLTK English stopwords
        combined_stopwords.update(nltk_stopwords.words('english'))
    except:
        # If NLTK data not available, continue with default stopwords
        pass
        
    # Add custom stopwords if provided
    if stopwords:
        combined_stopwords.update(set(stopwords))
    
    # Preprocess text - filter out numbers if not including them
    if not include_numbers:
        # Tokenize and filter tokens
        try:
            tokens = word_tokenize(text)
            # Remove tokens that are just numbers
            tokens = [token for token in tokens if not token.isdigit()]
            text = ' '.join(tokens)
        except:
            # If NLTK tokenization fails, use simple regex to remove standalone numbers
            import re
            text = re.sub(r'\b\d+\b', '', text)
    
    # Create the WordCloud object
    wc = WordCloud(
        background_color=background_color,
        max_words=max_words,
        width=width,
        height=height,
        colormap=colormap,
        stopwords=combined_stopwords,
        min_font_size=min_font_size,
        max_font_size=max_font_size,
        random_state=42  # For reproducibility
    )
    
    # Generate the word cloud
    wc.generate(text)
    
    # Convert to image
    plt.figure(figsize=(width/100, height/100), dpi=100)
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    
    # Save to a byte buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
    plt.close()
    buffer.seek(0)
    
    # Convert to base64
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

def analyze_word_frequency(text, max_words=100, stopwords=None, include_numbers=False):
    """
    Analyze word frequency in text content.
    
    Args:
        text: Text content to analyze
        max_words: Maximum number of words to include in results
        stopwords: Additional stopwords to exclude (list of strings)
        include_numbers: Whether to include numbers in analysis
        
    Returns:
        List of (word, count) tuples sorted by frequency
    """
    from collections import Counter
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords as nltk_stopwords
    import re
    
    # Guard against empty text
    if not text or len(text.strip()) == 0:
        return []
    
    # Combine NLTK stopwords with custom stopwords
    combined_stopwords = set()
    try:
        # Add NLTK English stopwords
        combined_stopwords.update(nltk_stopwords.words('english'))
    except:
        # If NLTK data not available, continue with empty stopwords
        pass
        
    # Add custom stopwords if provided
    if stopwords:
        combined_stopwords.update(set(stopwords))
    
    # Preprocess text
    text = text.lower()  # Convert to lowercase
    
    # Tokenize words
    try:
        words = word_tokenize(text)
    except:
        # Fallback to simple word splitting if NLTK fails
        words = re.findall(r'\b\w+\b', text)
    
    # Filter words
    filtered_words = []
    for word in words:
        # Skip short words (likely not meaningful)
        if len(word) <= 1:
            continue
            
        # Skip numbers if not including them
        if not include_numbers and word.isdigit():
            continue
            
        # Skip stopwords
        if word.lower() in combined_stopwords:
            continue
            
        filtered_words.append(word)
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Return most common words up to max_words
    return word_counts.most_common(max_words)
