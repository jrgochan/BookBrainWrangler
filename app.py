import streamlit as st
import os
import time
from book_manager import BookManager
from document_processor import DocumentProcessor
from knowledge_base import KnowledgeBase
from ollama_client import OllamaClient
from database import get_connection
from utils import (
    cleanup_text, 
    generate_thumbnail, 
    generate_placeholder_thumbnail, 
    generate_knowledge_export, 
    save_markdown_to_file
)

# Initialize the components
@st.cache_resource
def initialize_components():
    book_manager = BookManager()
    document_processor = DocumentProcessor()
    knowledge_base = KnowledgeBase()
    
    # Initialize Ollama client with settings from session state if available
    if 'ollama_host' in st.session_state and 'ollama_model' in st.session_state:
        ollama_client = OllamaClient(
            host=st.session_state.ollama_host,
            model=st.session_state.ollama_model
        )
    else:
        ollama_client = OllamaClient()
        
    return book_manager, document_processor, knowledge_base, ollama_client

# Set up the page
st.set_page_config(
    page_title="Book Knowledge AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_books' not in st.session_state:
    st.session_state.selected_books = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'filter_category' not in st.session_state:
    st.session_state.filter_category = "All"
    
# Ollama settings
if 'ollama_host' not in st.session_state:
    st.session_state.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
if 'ollama_model' not in st.session_state:
    st.session_state.ollama_model = os.environ.get("OLLAMA_MODEL", "llama2")
    
# Thumbnail settings
if 'thumbnail_size' not in st.session_state:
    st.session_state.thumbnail_size = (200, 280)
if 'thumbnail_bg_color' not in st.session_state:
    st.session_state.thumbnail_bg_color = (240, 240, 240)
if 'thumbnail_text_color' not in st.session_state:
    st.session_state.thumbnail_text_color = (70, 70, 70)

# OCR process settings
if "ocr_display_interval" not in st.session_state:
    st.session_state.ocr_display_interval = 1  # Display every Nth image
if "ocr_confidence_threshold" not in st.session_state:
    st.session_state.ocr_confidence_threshold = 70  # Minimum confidence %
if "ocr_show_current_image" not in st.session_state:
    st.session_state.ocr_show_current_image = True  # Show current image
if "ocr_show_extracted_text" not in st.session_state:
    st.session_state.ocr_show_extracted_text = True  # Show extracted text
if "ocr_current_image" not in st.session_state:
    st.session_state.ocr_current_image = None  # Current image
if "ocr_current_text" not in st.session_state:
    st.session_state.ocr_current_text = None  # Current text
if "ocr_current_confidence" not in st.session_state:
    st.session_state.ocr_current_confidence = None  # Current confidence

# Initialize components
book_manager, document_processor, knowledge_base, ollama_client = initialize_components()

# Sidebar for application navigation
st.sidebar.title("Book Knowledge AI")
app_mode = st.sidebar.selectbox(
    "Select Mode",
    ["Book Management", "Knowledge Base", "Chat with AI", "Settings"]
)

# Book Management section
if app_mode == "Book Management":
    st.title("Book Management")
    
    # Upload new book
    st.header("Upload New Book")
    uploaded_file = st.file_uploader("Upload a PDF or DOCX file from your CZUR ET24 Pro scanner or other sources", type=["pdf", "docx"])
    
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("Book Title")
    with col2:
        book_author = st.text_input("Book Author")
    
    book_category = st.text_input("Category (comma-separated for multiple categories)")
    
    if uploaded_file and st.button("Process Book"):
        # Create a collapsible container for progress information
        with st.expander("Processing Status", expanded=True):
            # Create placeholder elements for progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            last_update_container = st.empty()
            
            # Save the uploaded file temporarily
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            temp_path = f"temp_{int(time.time())}{file_ext}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # Initialize processing stage info
                file_type = "PDF" if file_ext == '.pdf' else "DOCX" if file_ext == '.docx' else f"Document ({file_ext})"
                status_text.text(f"Initializing {file_type} processing...")
                
                # Define progress callback function with condensed updates
                # Store only the latest message in session state to avoid flooding the UI
                if 'latest_status_updates' not in st.session_state:
                    st.session_state.latest_status_updates = []
                
                # Create containers for OCR visualization
                ocr_image_container = st.empty()
                ocr_text_container = st.empty()
                ocr_confidence_container = st.empty()
                
                # Define progress callback function with enhanced OCR visualization
                def update_progress(current, total, message):
                    if total > 0:
                        progress_value = min(current / total, 1.0)
                        progress_bar.progress(progress_value)
                    else:
                        progress_bar.progress(0)
                    
                    # Handle both string and dictionary message formats
                    if isinstance(message, dict):
                        # For structured messages (especially from OCR)
                        status_msg = message.get("text", "Processing...")
                        action = message.get("action", "")
                        
                        # Update status text
                        status_text.text(status_msg)
                        
                        # Add to latest updates list (keep only last 3)
                        st.session_state.latest_status_updates.append(status_msg)
                        if len(st.session_state.latest_status_updates) > 3:
                            st.session_state.latest_status_updates.pop(0)
                        
                        # Show the most recent updates
                        last_update_container.info("\n".join(st.session_state.latest_status_updates))
                        
                        # Handle OCR-specific updates with image and text display
                        if "current_image" in message and st.session_state.ocr_show_current_image:
                            # Only update the display based on the configured interval
                            page_num = current + 1  # 1-based page number for display
                            if page_num % st.session_state.ocr_display_interval == 0 or page_num == 1 or page_num == total:
                                # Store the current OCR state
                                st.session_state.ocr_current_image = message["current_image"]
                                
                                # Display the current image being processed
                                ocr_image_container.image(
                                    f"data:image/jpeg;base64,{message['current_image']}", 
                                    caption=f"Page {page_num}/{total}", 
                                    use_column_width=True
                                )
                        
                        # Display the extracted OCR text if available
                        if "ocr_text" in message and st.session_state.ocr_show_extracted_text:
                            st.session_state.ocr_current_text = message["ocr_text"]
                            if action == "completed":  # Only show completed OCR text
                                ocr_text_container.text_area(
                                    "Extracted Text", 
                                    message["ocr_text"], 
                                    height=150
                                )
                        
                        # Display OCR confidence if available
                        if "confidence" in message:
                            confidence = message["confidence"]
                            st.session_state.ocr_current_confidence = confidence
                            
                            # Format confidence as percentage
                            conf_text = f"OCR Confidence: {confidence:.1f}%"
                            
                            # Determine color based on threshold
                            if confidence < st.session_state.ocr_confidence_threshold:
                                conf_text = f"⚠️ {conf_text} (Low Quality)"
                                ocr_confidence_container.error(conf_text)
                            else:
                                ocr_confidence_container.success(conf_text)
                    else:
                        # Legacy string message format
                        status_text.text(message)
                        
                        # Add to latest updates list (keep only last 3)
                        st.session_state.latest_status_updates.append(message)
                        if len(st.session_state.latest_status_updates) > 3:
                            st.session_state.latest_status_updates.pop(0)
                        
                        # Show the most recent updates
                        last_update_container.info("\n".join(st.session_state.latest_status_updates))
                
                # Display initial info for PDFs
                if file_ext == '.pdf':
                    page_count = document_processor.get_page_count(temp_path)
                    update_progress(0, 1, f"PDF has {page_count} pages to process")
                
                # Process the file with progress updates
                update_progress(0, 1, "Starting content extraction...")
                extracted_content = document_processor.extract_content(
                    temp_path, 
                    include_images=True, 
                    progress_callback=update_progress
                )
                
                # Update progress for text cleanup
                update_progress(0, 1, "Cleaning up extracted text...")
                progress_bar.progress(0.9)  # 90% complete
                
                # Clean up the extracted text
                if isinstance(extracted_content, dict):
                    # New format with text and images
                    cleaned_text = cleanup_text(extracted_content['text'])
                    extracted_content['text'] = cleaned_text
                    image_count = len(extracted_content.get('images', []))
                    
                    update_progress(0, 1, f"Processed {len(cleaned_text)} characters of text and {image_count} images")
                else:
                    # Legacy format (text only)
                    cleaned_text = cleanup_text(extracted_content)
                    extracted_content = {'text': cleaned_text, 'images': []}
                
                # Update progress for database addition
                update_progress(0, 1, "Adding book to database...")
                progress_bar.progress(0.95)  # 95% complete
                
                # Add book to the database
                categories = [cat.strip() for cat in book_category.split(",") if cat.strip()]
                book_id = book_manager.add_book(
                    title=book_title,
                    author=book_author,
                    categories=categories,
                    file_path=temp_path,
                    content=extracted_content['text']  # Store just the text in the books table
                )
                
                # Complete the progress
                progress_bar.progress(1.0)
                update_progress(1, 1, "Processing complete!")
                
                st.success(f"Book '{book_title}' successfully processed and added to your library!")
                
            except Exception as e:
                status_text.text(f"Error: {str(e)}")
                st.error(f"Error processing book: {e}")
            finally:
                # Clear the session state updates for next run
                if 'latest_status_updates' in st.session_state:
                    st.session_state.latest_status_updates = []
                
                # Clean up the temporary file if needed
                if os.path.exists(temp_path) and temp_path.startswith("temp_"):
                    os.remove(temp_path)
    
    # List and manage existing books
    st.header("Your Book Library")
    
    # Search and filter
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("Search books", st.session_state.search_query)
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
    
    with col2:
        categories = book_manager.get_all_categories()
        filter_options = ["All"] + categories
        filter_category = st.selectbox("Filter by category", filter_options, 
                                      index=filter_options.index(st.session_state.filter_category) if st.session_state.filter_category in filter_options else 0)
        if filter_category != st.session_state.filter_category:
            st.session_state.filter_category = filter_category
    
    # Get filtered books
    if filter_category == "All":
        books = book_manager.search_books(search_query)
    else:
        books = book_manager.search_books(search_query, category=filter_category)
    
    if not books:
        st.info("No books found in your library. Upload some books to get started!")
    else:
        # Initialize thumbnail cache in session state if not already present
        if 'thumbnail_cache' not in st.session_state:
            st.session_state.thumbnail_cache = {}
        
        # Display book cards in a grid layout
        book_columns = st.columns(3)  # Display books in 3 columns
        
        for i, book in enumerate(books):
            with book_columns[i % 3]:
                with st.container(border=True):
                    # Generate or retrieve thumbnail from cache
                    if book['id'] in st.session_state.thumbnail_cache:
                        thumbnail = st.session_state.thumbnail_cache[book['id']]
                    elif 'file_path' in book and book['file_path'] and os.path.exists(book['file_path']):
                        thumbnail = generate_thumbnail(
                            book['file_path'],
                            max_size=st.session_state.thumbnail_size
                        )
                        st.session_state.thumbnail_cache[book['id']] = thumbnail
                    else:
                        # Create a placeholder with book title if file not found
                        thumbnail = generate_placeholder_thumbnail(
                            book['title'],
                            size=st.session_state.thumbnail_size,
                            bg_color=st.session_state.thumbnail_bg_color,
                            text_color=st.session_state.thumbnail_text_color
                        )
                        st.session_state.thumbnail_cache[book['id']] = thumbnail
                    
                    # Center the thumbnail and make it clickable
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col2:
                        st.image(thumbnail, use_column_width=True)
                    
                    # Book title and author
                    st.markdown(f"### {book['title']}")
                    st.markdown(f"*by {book['author']}*")
                    
                    # Categories and date added
                    st.markdown(f"**Categories:** {', '.join(book['categories'])}")
                    st.markdown(f"**Added:** {book['date_added']}")
                    
                    # Book actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Edit", key=f"edit_{book['id']}"):
                            st.session_state.book_to_edit = book['id']
                            st.rerun()
                    
                    with col2:
                        if st.button(f"Delete", key=f"delete_{book['id']}"):
                            book_manager.delete_book(book['id'])
                            # Remove from thumbnail cache if it exists
                            if book['id'] in st.session_state.thumbnail_cache:
                                del st.session_state.thumbnail_cache[book['id']]
                            st.success(f"Book '{book['title']}' deleted successfully!")
                            st.rerun()
    
    # Book editing modal
    if hasattr(st.session_state, 'book_to_edit'):
        book = book_manager.get_book(st.session_state.book_to_edit)
        if book:
            st.header(f"Edit Book: {book['title']}")
            
            new_title = st.text_input("Book Title", book['title'])
            new_author = st.text_input("Book Author", book['author'])
            new_categories = st.text_input("Categories (comma-separated)", ", ".join(book['categories']))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    categories = [cat.strip() for cat in new_categories.split(",") if cat.strip()]
                    book_manager.update_book(
                        book_id=book['id'],
                        title=new_title,
                        author=new_author,
                        categories=categories
                    )
                    st.success("Book updated successfully!")
                    del st.session_state.book_to_edit
                    st.rerun()
            
            with col2:
                if st.button("Cancel"):
                    del st.session_state.book_to_edit
                    st.rerun()

# Knowledge Base Management
elif app_mode == "Knowledge Base":
    st.title("Knowledge Base Management")
    st.write("Select which books to include in your AI's knowledge base.")
    
    # Get all books
    all_books = book_manager.get_all_books()
    
    if not all_books:
        st.info("No books found in your library. Add some books first!")
    else:
        # Get books that are already in the knowledge base
        kb_book_ids = knowledge_base.get_indexed_book_ids()
        
        st.header("Books in Knowledge Base")
        
        # Add a container for progress tracking that will be shown when toggling books
        progress_container = st.container()
        
        # Helper function to toggle a book with progress tracking
        def toggle_book_with_progress(book_id, is_in_kb):
            with progress_container:
                # Create a collapsible container for progress information
                with st.expander("Knowledge Base Update Status", expanded=True):
                    # Create progress tracking elements
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    last_update_container = st.empty()
                
                    # Store status updates in session state to keep them brief
                    if 'kb_status_updates' not in st.session_state:
                        st.session_state.kb_status_updates = []
                
                    # Define progress callback function
                    def update_progress(current, total, message):
                        if total > 0:
                            progress_value = min(current / total, 1.0)
                            progress_bar.progress(progress_value)
                        else:
                            progress_bar.progress(0)
                            
                        # Update status text
                        status_text.text(message)
                        
                        # Add to latest updates list (keep only last 3)
                        st.session_state.kb_status_updates.append(message)
                        if len(st.session_state.kb_status_updates) > 3:
                            st.session_state.kb_status_updates.pop(0)
                        
                        # Show the most recent updates
                        last_update_container.info("\n".join(st.session_state.kb_status_updates))
                
                    try:
                        # Get book content text
                        book_text = book_manager.get_book_content(book_id)
                        
                        # Get book file path for image extraction if needed
                        book_details = book_manager.get_book(book_id)
                        file_path = book_details.get('file_path') if book_details else None
                        
                        # If adding to knowledge base and file exists, extract images too
                        if not is_in_kb and file_path and os.path.exists(file_path):
                            update_progress(0, 1, "Processing complete book content including images...")
                            
                            # Extract both text and images from the book file
                            try:
                                extracted_content = document_processor.extract_content(
                                    file_path, 
                                    include_images=True, 
                                    progress_callback=update_progress
                                )
                                
                                if isinstance(extracted_content, dict):
                                    # If we got a dict back, it's the new format with images
                                    # We'll use our existing clean text but add the images
                                    book_content = {
                                        'text': book_text,
                                        'images': extracted_content.get('images', [])
                                    }
                                    
                                    img_count = len(book_content['images'])
                                    update_progress(0.5, 1, f"Adding book with {img_count} images to knowledge base...")
                                else:
                                    # Fallback to text-only if we got just a string
                                    book_content = book_text
                            except Exception as e:
                                # If image extraction fails, fall back to text only
                                print(f"Warning: Image extraction failed, using text only: {e}")
                                update_progress(0.5, 1, "Image extraction failed, using text only")
                                book_content = book_text
                        else:
                            # If removing or file not available, just use the text
                            book_content = book_text
                        
                        # Toggle the book with progress tracking
                        knowledge_base.toggle_book_in_knowledge_base(
                            book_id, 
                            book_content,
                            add_to_kb=not is_in_kb,
                            progress_callback=update_progress
                        )
                        
                        # Clear the session state updates for next run
                        if 'kb_status_updates' in st.session_state:
                            st.session_state.kb_status_updates = []
                        
                        # Force page refresh to update the UI
                        st.rerun()
                        
                    except Exception as e:
                        status_text.text(f"Error: {str(e)}")
                        st.error(f"Error: {e}")
                        
                        # Clear the session state updates for next run
                        if 'kb_status_updates' in st.session_state:
                            st.session_state.kb_status_updates = []
        
        # Initialize thumbnail cache if needed
        if 'kb_thumbnail_cache' not in st.session_state:
            st.session_state.kb_thumbnail_cache = {}
    
        # Display book cards in a grid layout
        book_columns = st.columns(3)  # Display books in 3 columns
        
        for i, book in enumerate(all_books):
            with book_columns[i % 3]:
                with st.container(border=True):
                    # Generate or retrieve thumbnail from cache
                    if book['id'] in st.session_state.kb_thumbnail_cache:
                        thumbnail = st.session_state.kb_thumbnail_cache[book['id']]
                    elif 'file_path' in book and book['file_path'] and os.path.exists(book['file_path']):
                        thumbnail = generate_thumbnail(
                            book['file_path'],
                            max_size=st.session_state.thumbnail_size
                        )
                        st.session_state.kb_thumbnail_cache[book['id']] = thumbnail
                    else:
                        # Create a placeholder with book title if file not found
                        thumbnail = generate_placeholder_thumbnail(
                            book['title'],
                            size=st.session_state.thumbnail_size,
                            bg_color=st.session_state.thumbnail_bg_color,
                            text_color=st.session_state.thumbnail_text_color
                        )
                        st.session_state.kb_thumbnail_cache[book['id']] = thumbnail
                    
                    # Display thumbnail
                    st.image(thumbnail, use_column_width=True)
                    
                    # Book title and author
                    st.markdown(f"### {book['title']}")
                    st.markdown(f"*by {book['author']}*")
                    
                    # Knowledge base status and toggle
                    is_in_kb = book['id'] in kb_book_ids
                    if is_in_kb:
                        st.markdown("**Status:** ✅ In Knowledge Base")
                    else:
                        st.markdown("**Status:** ❌ Not Included")
                    
                    # Toggle button
                    if st.button(
                        "Remove from KB" if is_in_kb else "Add to KB",
                        key=f"kb_toggle_{book['id']}"
                    ):
                        toggle_book_with_progress(book['id'], is_in_kb)
        
        # Button to rebuild the entire knowledge base
        if st.button("Rebuild Complete Knowledge Base"):
            # Create a collapsible container for progress information
            with st.expander("Knowledge Base Rebuild Status", expanded=True):
                # Create progress tracking elements
                progress_bar = st.progress(0)
                status_text = st.empty()
                last_update_container = st.empty()
                
                # Store status updates in session state to keep them brief
                if 'kb_rebuild_updates' not in st.session_state:
                    st.session_state.kb_rebuild_updates = []
                
                # Define progress callback function
                def update_progress(current, total, message):
                    if total > 0:
                        progress_value = min(current / total, 1.0)
                        progress_bar.progress(progress_value)
                    else:
                        progress_bar.progress(0)
                    
                    # Update status text
                    status_text.text(message)
                    
                    # Add to latest updates list (keep only last 3)
                    st.session_state.kb_rebuild_updates.append(message)
                    if len(st.session_state.kb_rebuild_updates) > 3:
                        st.session_state.kb_rebuild_updates.pop(0)
                    
                    # Show the most recent updates
                    last_update_container.info("\n".join(st.session_state.kb_rebuild_updates))
                
                try:
                    # Initialize with starting message
                    update_progress(0, 1, "Starting knowledge base rebuild...")
                    
                    # Rebuild the knowledge base with progress tracking
                    knowledge_base.rebuild_knowledge_base(book_manager, progress_callback=update_progress)
                    
                    # Complete the progress
                    progress_bar.progress(1.0)
                    update_progress(1, 1, "Rebuild complete!")
                    st.success("Knowledge base rebuilt successfully!")
                    
                    # Clear the session state updates for next run
                    if 'kb_rebuild_updates' in st.session_state:
                        st.session_state.kb_rebuild_updates = []
                    
                except Exception as e:
                    status_text.text(f"Error: {str(e)}")
                    st.error(f"Error rebuilding knowledge base: {e}")
                    
                    # Clear the session state updates for next run
                    if 'kb_rebuild_updates' in st.session_state:
                        st.session_state.kb_rebuild_updates = []

# Chat with AI
elif app_mode == "Chat with AI":
    st.title("Chat with Your Book-Powered AI")
    
    # Check if we have any books in the knowledge base
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    if not kb_book_ids:
        st.warning("Your AI doesn't have any knowledge yet! Please add books to the knowledge base first.")
        st.stop()
    
    # Initialize debug mode in session state if not present
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    # Add a debug toggle and export options in the sidebar
    with st.sidebar:
        st.write("### Chat Settings")
        st.session_state.debug_mode = st.toggle("Show retrieved context", st.session_state.debug_mode)
        
        # Add Knowledge Export section
        st.write("### Knowledge Export")
        export_container = st.container()
        
        with export_container:
            # Export options
            export_type = st.radio(
                "Export type:", 
                ["Topic-based", "Query-based", "All books"],
                help="Topic-based: Organize by book categories. Query-based: Focus on a specific query. All books: Include excerpts from all books."
            )
            
            if export_type == "Query-based":
                export_query = st.text_input(
                    "Export query:", 
                    placeholder="Enter a topic or question",
                    help="The export will focus on this specific topic or question"
                )
            else:
                export_query = None
                
            # Advanced export options in an expander
            with st.expander("Advanced export options"):
                include_content = st.checkbox("Include book excerpts", value=True)
                max_topics = st.slider("Max topics/categories", 1, 10, 5)
                
                max_books_option = st.checkbox("Limit number of books", value=False)
                max_books = None
                if max_books_option:
                    max_books = st.slider("Max books to include", 1, len(kb_book_ids), min(5, len(kb_book_ids)))
            
            # Export button
            if st.button("📄 Export to Markdown"):
                with st.spinner("Generating knowledge export..."):
                    # Generate the markdown content
                    markdown_content = generate_knowledge_export(
                        book_manager=book_manager,
                        knowledge_base=knowledge_base,
                        query=export_query if export_type == "Query-based" else None,
                        include_content=(export_type == "All books") or include_content,
                        max_topics=max_topics,
                        max_books=max_books
                    )
                    
                    # Save to file
                    file_path = save_markdown_to_file(markdown_content)
                    
                    if file_path:
                        # Create a download link
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        st.success(f"Export generated successfully!")
                        st.download_button(
                            label="Download Markdown File",
                            data=file_content,
                            file_name=os.path.basename(file_path),
                            mime="text/markdown"
                        )
                        
                        # Preview the content
                        with st.expander("Preview Export", expanded=True):
                            st.markdown(markdown_content)
                    else:
                        st.error("Failed to generate export file")
    
    # Get book titles for books in KB
    conn = get_connection()
    cursor = conn.cursor()
    books_in_kb = []
    for book_id in kb_book_ids:
        cursor.execute('SELECT title, author FROM books WHERE id = ?', (book_id,))
        result = cursor.fetchone()
        if result:
            title, author = result
            books_in_kb.append(f"• {title} by {author}")
    conn.close()
    
    # Display books in knowledge base
    with st.expander("Books in Knowledge Base", expanded=False):
        if books_in_kb:
            st.markdown("\n".join(books_in_kb))
        else:
            st.warning("Books are in knowledge base but titles could not be retrieved.")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("assistant").write(message["content"])
        elif message["role"] == "system" and st.session_state.debug_mode:
            st.chat_message("system").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your books..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Generate AI response with context from knowledge base
        with st.spinner(f"Thinking with {st.session_state.ollama_model}..."):
            # Retrieve context from knowledge base
            context = knowledge_base.retrieve_relevant_context(prompt)
            
            # In debug mode, show the retrieved context
            if st.session_state.debug_mode:
                st.session_state.chat_history.append({"role": "system", "content": f"**Retrieved Context:**\n\n{context}"})
                st.chat_message("system").write(f"**Retrieved Context:**\n\n{context}")
            
            # Generate response
            response = ollama_client.generate_response(prompt, context)
        
        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

# Settings page
elif app_mode == "Settings":
    st.title("Settings")
    
    # Tabs for different settings categories
    settings_tab1, settings_tab2, settings_tab3 = st.tabs(["Ollama AI Settings", "Thumbnail Settings", "OCR Settings"])
    
    # Ollama Settings Tab
    with settings_tab1:
        st.header("Ollama AI Settings")
        
        # Connection Status
        connection_status = ollama_client.check_connection()
        if connection_status:
            st.success("✅ Connected to Ollama server")
        else:
            st.error("❌ Not connected to Ollama server. Please check that Ollama is running.")
        
        # Host settings
        ollama_host = st.text_input("Ollama Host URL", value=st.session_state.ollama_host)
        
        # Model selection
        st.subheader("AI Model Selection")
        
        # Get available models
        available_models = []
        model_details = {}
        
        if connection_status:
            with st.spinner("Loading available models..."):
                available_models = ollama_client.list_models()
                
                if available_models:
                    st.success(f"Found {len(available_models)} available models")
                    # Create a dictionary of model names for the selectbox
                    model_options = [model.get("name", "unknown") for model in available_models]
                    
                    # Get the current index if the current model is in the list
                    current_index = 0
                    if st.session_state.ollama_model in model_options:
                        current_index = model_options.index(st.session_state.ollama_model)
                    
                    # Model selection dropdown
                    selected_model = st.selectbox(
                        "Select AI Model", 
                        options=model_options,
                        index=current_index
                    )
                    
                    # Get and display model details
                    if st.button("Show Model Details"):
                        with st.spinner(f"Loading details for {selected_model}..."):
                            model_details = ollama_client.get_model_details(selected_model)
                            if model_details:
                                st.subheader(f"{selected_model} Details")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Model:** {model_details.get('model', 'unknown')}")
                                    st.write(f"**Size:** {model_details.get('size', 'unknown')}")
                                with col2:
                                    st.write(f"**Modified:** {model_details.get('modified_at', 'unknown')}")
                                    st.write(f"**Format:** {model_details.get('format', 'unknown')}")
                            else:
                                st.warning(f"Could not retrieve details for {selected_model}")
                    
                    # Save button for settings
                    if st.button("Save Ollama Settings"):
                        # Update the ollama client and session state
                        update_success = ollama_client.update_settings(
                            host=ollama_host,
                            model=selected_model
                        )
                        
                        if update_success:
                            st.session_state.ollama_host = ollama_host
                            st.session_state.ollama_model = selected_model
                            st.success("Ollama settings saved successfully!")
                        else:
                            st.error("Could not connect to the specified Ollama host. Settings not saved.")
                else:
                    st.warning("No models found. Make sure Ollama is running and you have models installed.")
                    st.info("You can install models with the Ollama CLI: `ollama pull llama2`")
        else:
            st.info("Connect to Ollama server to view available models.")
            # Save button for just the host
            if st.button("Save Host Settings"):
                # Try connecting to the new host
                old_host = ollama_client.host
                ollama_client.host = ollama_host
                ollama_client.api_endpoint = f"{ollama_host}/api"
                
                if ollama_client.check_connection():
                    st.session_state.ollama_host = ollama_host
                    st.success("Host settings saved successfully!")
                    st.rerun()  # Refresh to show models
                else:
                    # Revert to the old host
                    ollama_client.host = old_host
                    ollama_client.api_endpoint = f"{old_host}/api"
                    st.error("Could not connect to the specified Ollama host. Settings not saved.")
    
    # Thumbnail Settings Tab
    with settings_tab2:
        st.header("Document Thumbnail Settings")
        
        st.write("Customize how document thumbnails appear in your library")
        
        # Create a placeholder for the preview
        preview_container = st.container(height=350)
        
        # Settings columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Thumbnail size settings
            st.subheader("Thumbnail Size")
            width = st.slider("Width (px)", 100, 300, st.session_state.thumbnail_size[0])
            height = st.slider("Height (px)", 150, 400, st.session_state.thumbnail_size[1])
            
        with col2:
            # Thumbnail color settings
            st.subheader("Thumbnail Colors")
            
            # Background color picker
            bg_color_picker = st.color_picker(
                "Background Color", 
                f"rgb({st.session_state.thumbnail_bg_color[0]}, {st.session_state.thumbnail_bg_color[1]}, {st.session_state.thumbnail_bg_color[2]})"
            )
            
            # Extract RGB values from the color picker
            bg_color = bg_color_picker.strip("rgb()").split(",")
            bg_color = [int(c.strip()) for c in bg_color]
            
            # Text color picker
            text_color_picker = st.color_picker(
                "Text Color", 
                f"rgb({st.session_state.thumbnail_text_color[0]}, {st.session_state.thumbnail_text_color[1]}, {st.session_state.thumbnail_text_color[2]})"
            )
            
            # Extract RGB values from the color picker
            text_color = text_color_picker.strip("rgb()").split(",")
            text_color = [int(c.strip()) for c in text_color]
        
        # Generate a live preview
        with preview_container:
            st.subheader("Preview")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Generate a placeholder with current settings
                preview = generate_placeholder_thumbnail(
                    "Sample Book Title",
                    size=(width, height),
                    bg_color=tuple(bg_color),
                    text_color=tuple(text_color)
                )
                st.image(preview, caption="Thumbnail Preview", use_column_width=True)
        
        # Save button
        if st.button("Save Thumbnail Settings"):
            # Update session state
            st.session_state.thumbnail_size = (width, height)
            st.session_state.thumbnail_bg_color = tuple(bg_color)
            st.session_state.thumbnail_text_color = tuple(text_color)
            
            # Clear thumbnail caches to regenerate with new settings
            if 'thumbnail_cache' in st.session_state:
                st.session_state.thumbnail_cache = {}
            if 'kb_thumbnail_cache' in st.session_state:
                st.session_state.kb_thumbnail_cache = {}
                
            st.success("Thumbnail settings saved successfully!")
            st.info("Thumbnails will be regenerated with your new settings.")
    
    # OCR Settings Tab
    with settings_tab3:
        st.header("OCR Processing Settings")
        
        st.write("Configure how the OCR (Optical Character Recognition) process works and what information is displayed during processing.")
        
        # Create columns for settings
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Display Settings")
            
            # Toggle for showing current image
            show_current_image = st.toggle(
                "Show current image being processed", 
                value=st.session_state.ocr_show_current_image
            )
            
            # Toggle for showing extracted text
            show_extracted_text = st.toggle(
                "Show extracted text", 
                value=st.session_state.ocr_show_extracted_text
            )
            
            # Display interval (for skipping images)
            display_interval = st.slider(
                "Display every nth image", 
                min_value=1, 
                max_value=10, 
                value=st.session_state.ocr_display_interval,
                help="Higher values will show fewer images during processing, which may improve performance."
            )
        
        with col2:
            st.subheader("OCR Quality Settings")
            
            # Confidence threshold slider
            confidence_threshold = st.slider(
                "Confidence threshold (%)", 
                min_value=0, 
                max_value=100, 
                value=st.session_state.ocr_confidence_threshold,
                help="Pages with confidence below this percentage will be flagged as potentially low quality."
            )
            
            # Example confidence display
            if confidence_threshold > 0:
                # Show example of low and high confidence
                st.write("**Sample confidence indicators:**")
                
                if confidence_threshold > 80:
                    st.info("Most pages will be flagged as low quality with this high threshold")
                
                # High confidence example
                st.success(f"OCR Confidence: 92.5% (Good Quality)")
                
                # Low confidence example
                st.error(f"⚠️ OCR Confidence: {confidence_threshold - 10:.1f}% (Low Quality)")
        
        # Last processed OCR image preview
        if st.session_state.ocr_current_image:
            st.subheader("Last Processed Image Preview")
            
            # Show the image and extracted text side by side
            preview_col1, preview_col2 = st.columns(2)
            
            with preview_col1:
                st.image(
                    f"data:image/jpeg;base64,{st.session_state.ocr_current_image}", 
                    caption="Last Processed Image", 
                    use_column_width=True
                )
            
            with preview_col2:
                if st.session_state.ocr_current_text:
                    st.text_area(
                        "Extracted Text", 
                        st.session_state.ocr_current_text, 
                        height=200
                    )
                    
                    if st.session_state.ocr_current_confidence:
                        conf_text = f"OCR Confidence: {st.session_state.ocr_current_confidence:.1f}%"
                        if st.session_state.ocr_current_confidence < confidence_threshold:
                            st.error(f"⚠️ {conf_text} (Low Quality)")
                        else:
                            st.success(conf_text)
                else:
                    st.info("No text has been extracted yet")
        else:
            st.info("No images have been processed yet. Upload a PDF to see OCR results.")
        
        # Save button
        if st.button("Save OCR Settings"):
            # Update session state
            st.session_state.ocr_show_current_image = show_current_image
            st.session_state.ocr_show_extracted_text = show_extracted_text
            st.session_state.ocr_display_interval = display_interval
            st.session_state.ocr_confidence_threshold = confidence_threshold
            
            st.success("OCR settings saved successfully!")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Book Knowledge AI v1.0")
