"""
Book Management page for the Book Knowledge AI application.
"""

from taipy.gui import navigate, notify, Markdown

# Define the book management page template
book_management_template = """
<|container|class_name=page-container|
# 📄 Book Management

<|tabs|
<|tab|label=Upload New Book|
<|container|class_name=card|
## Upload New Book

Upload a PDF or DOCX file to add to your knowledge base.

<|{file_path}|file_selector|extensions=pdf,docx|label=Select a file to upload|>

<|layout|columns=1 1 1|
<|{title}|input|label=Title|>
<|{author}|input|label=Author|>
<|{categories}|input|label=Categories (comma separated)|>
|>

<|Process Book|button|on_action=on_process_book|>
|>
|>

<|tab|label=Manage Books|
<|container|class_name=card|
## Manage Books

<|{search_query}|input|label=Search books|on_change=on_search_books|>

<|{on_search_books}|button|label=Search|>

<|{render_book_list(books)}|raw|>
|>
|>
|>
"""

def get_template():
    """Get the book management page template."""
    return book_management_template

def on_process_book(state):
    """
    Process an uploaded book file.
    
    Args:
        state: The application state
    """
    if not state.file_path:
        notify(state, "Please select a file to upload", "error")
        return
    
    if not state.title:
        notify(state, "Please enter a title for the book", "error")
        return
    
    if not state.author:
        notify(state, "Please enter an author for the book", "error")
        return
    
    # Parse categories
    categories = [cat.strip() for cat in state.categories.split(",")] if state.categories else []
    
    # Log the processing
    notify(state, f"Processing book: {state.title}", "info")
    
    # In the real implementation, we would:
    # 1. Process the document with document_processor
    # 2. Add the book to book_manager
    # 3. Update the knowledge base
    
    # For now, we'll just simulate success
    notify(state, f"Book '{state.title}' processed successfully!", "success")
    
    # Clear the form
    state.file_path = None
    state.title = ""
    state.author = ""
    state.categories = ""
    
    # Refresh the book list
    on_search_books(state)

def on_search_books(state):
    """
    Search for books based on the query.
    
    Args:
        state: The application state
    """
    # In the real implementation, we would:
    # books = state.book_manager.search_books(query=state.search_query)
    # state.books = books
    
    # For now, we'll just simulate some books
    state.books = [
        {"id": 1, "title": "Sample Book 1", "author": "Author 1", "categories": ["Fiction", "Fantasy"]},
        {"id": 2, "title": "Sample Book 2", "author": "Author 2", "categories": ["Non-fiction", "Science"]},
        {"id": 3, "title": "Sample Book 3", "author": "Author 3", "categories": ["History", "Biography"]}
    ]
    
    # Filter books based on search query if provided
    if state.search_query:
        state.books = [
            book for book in state.books 
            if state.search_query.lower() in book["title"].lower() or 
               state.search_query.lower() in book["author"].lower()
        ]

def render_book_list(books):
    """
    Render the list of books.
    
    Args:
        books: List of book dictionaries
        
    Returns:
        HTML string for rendering the book list
    """
    if not books:
        return "<p>No books found.</p>"
    
    html = "<div class='book-list'>"
    
    for book in books:
        categories = ", ".join(book["categories"]) if book["categories"] else "No categories"
        
        html += f"""
        <div class='card' style='margin-bottom: 1rem;'>
            <h3>{book["title"]}</h3>
            <p><strong>Author:</strong> {book["author"]}</p>
            <p><strong>Categories:</strong> {categories}</p>
            <div>
                <button onclick="state.book_to_edit = {book['id']}">Edit</button>
                <button onclick="state.book_to_delete = {book['id']}">Delete</button>
                <button onclick="state.book_to_view = {book['id']}">View Details</button>
            </div>
        </div>
        """
    
    html += "</div>"
    return html

def init_state(state):
    """
    Initialize the state variables for this page.
    
    Args:
        state: The application state
    """
    # Form state
    if "file_path" not in state:
        state.file_path = None
    if "title" not in state:
        state.title = ""
    if "author" not in state:
        state.author = ""
    if "categories" not in state:
        state.categories = ""
    
    # Search state
    if "search_query" not in state:
        state.search_query = ""
    if "books" not in state:
        state.books = []
    
    # Action state
    if "book_to_edit" not in state:
        state.book_to_edit = None
    if "book_to_delete" not in state:
        state.book_to_delete = None
    if "book_to_view" not in state:
        state.book_to_view = None