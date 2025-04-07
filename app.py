import streamlit as st
import os
import time
from book_manager import BookManager
from pdf_processor import PDFProcessor
from knowledge_base import KnowledgeBase
from ollama_client import OllamaClient
from utils import cleanup_text

# Initialize the components
@st.cache_resource
def initialize_components():
    book_manager = BookManager()
    pdf_processor = PDFProcessor()
    knowledge_base = KnowledgeBase()
    ollama_client = OllamaClient()
    return book_manager, pdf_processor, knowledge_base, ollama_client

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

# Initialize components
book_manager, pdf_processor, knowledge_base, ollama_client = initialize_components()

# Sidebar for application navigation
st.sidebar.title("Book Knowledge AI")
app_mode = st.sidebar.selectbox(
    "Select Mode",
    ["Book Management", "Knowledge Base", "Chat with AI"]
)

# Book Management section
if app_mode == "Book Management":
    st.title("Book Management")
    
    # Upload new book
    st.header("Upload New Book")
    uploaded_file = st.file_uploader("Upload a PDF file from your CZUR ET24 Pro scanner", type="pdf")
    
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("Book Title")
    with col2:
        book_author = st.text_input("Book Author")
    
    book_category = st.text_input("Category (comma-separated for multiple categories)")
    
    if uploaded_file and st.button("Process Book"):
        with st.spinner("Processing your book..."):
            # Save the uploaded file temporarily
            temp_path = f"temp_{int(time.time())}.pdf"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process the PDF file
            try:
                extracted_text = pdf_processor.extract_text(temp_path)
                
                # Clean up the extracted text
                cleaned_text = cleanup_text(extracted_text)
                
                # Add book to the database
                categories = [cat.strip() for cat in book_category.split(",") if cat.strip()]
                book_id = book_manager.add_book(
                    title=book_title,
                    author=book_author,
                    categories=categories,
                    file_path=temp_path,
                    content=cleaned_text
                )
                
                st.success(f"Book '{book_title}' successfully processed and added to your library!")
                
            except Exception as e:
                st.error(f"Error processing book: {e}")
            finally:
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
        for book in books:
            with st.expander(f"{book['title']} by {book['author']}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**Categories:** {', '.join(book['categories'])}")
                    st.write(f"**Added on:** {book['date_added']}")
                
                with col2:
                    if st.button(f"Edit", key=f"edit_{book['id']}"):
                        st.session_state.book_to_edit = book['id']
                        st.rerun()
                
                with col3:
                    if st.button(f"Delete", key=f"delete_{book['id']}"):
                        book_manager.delete_book(book['id'])
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
        
        for book in all_books:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                is_in_kb = book['id'] in kb_book_ids
                st.checkbox(
                    f"{book['title']} by {book['author']}",
                    value=is_in_kb,
                    key=f"kb_{book['id']}",
                    on_change=lambda book_id=book['id'], is_checked=not is_in_kb: 
                        knowledge_base.toggle_book_in_knowledge_base(
                            book_id, 
                            book_manager.get_book_content(book_id),
                            add_to_kb=not is_in_kb
                        )
                )
            
            with col2:
                if book['id'] in kb_book_ids:
                    st.write("✅ In Knowledge Base")
                else:
                    st.write("❌ Not Included")
        
        # Button to rebuild the entire knowledge base
        if st.button("Rebuild Complete Knowledge Base"):
            with st.spinner("Rebuilding knowledge base... This may take some time."):
                knowledge_base.rebuild_knowledge_base(book_manager)
                st.success("Knowledge base rebuilt successfully!")

# Chat with AI
elif app_mode == "Chat with AI":
    st.title("Chat with Your Book-Powered AI")
    
    # Check if we have any books in the knowledge base
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    if not kb_book_ids:
        st.warning("Your AI doesn't have any knowledge yet! Please add books to the knowledge base first.")
        st.stop()
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your books..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Generate AI response with context from knowledge base
        with st.spinner("Thinking..."):
            context = knowledge_base.retrieve_relevant_context(prompt)
            response = ollama_client.generate_response(prompt, context)
        
        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Book Knowledge AI v1.0")
