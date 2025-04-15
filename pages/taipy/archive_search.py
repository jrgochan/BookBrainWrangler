"""
Archive Search page for the Book Knowledge AI application.
"""

from taipy.gui import navigate, notify, Markdown
import time
from datetime import datetime

# Define the archive search page template
archive_search_template = """
<|container|class_name=page-container|
# 🔍 Internet Archive Book Search

<|container|class_name=card|
<|expander|label=About Internet Archive|
The [Internet Archive](https://archive.org) is a non-profit digital library offering free universal access to books,
movies, music, and billions of archived web pages.

Use this page to search for books and add them directly to your knowledge base.
|>

<|container|class_name=search-form|
## Search for Books

<|{search_query}|input|label=Search query|placeholder=Enter title, author, subject...|>

<|layout|columns=1 1 1|
<|{max_results}|slider|min=10|max=100|step=6|label=Maximum results|>
<|{media_type}|selector|lov={media_types}|label=Media type|>
<|{sort_by}|selector|lov={sort_options}|label=Sort by|>
|>

<|Search Internet Archive|button|on_action=on_search_archive|>
|>
|>

<|container|class_name=search-results|
{search_results_heading}

<|layout|columns=3 1|render={has_results}|
<|{results_count_text}|text|>
<|Download All|button|on_action=on_download_all|>
|>

<|container|class_name=book-grid|render={has_results}|
{book_grid_content}
|>
|>

<|container|class_name=card|render={has_logs}|
## Processing Log
<|container|class_name=console|
{processing_logs_content}
|>

<|Clear Logs|button|on_action=on_clear_logs|>
|>
|>
"""

def get_template():
    """Get the archive search page template."""
    return archive_search_template

def on_search_archive(state):
    """
    Search the Internet Archive for books.
    
    Args:
        state: The application state
    """
    if not state.search_query:
        notify(state, "Please enter a search query", "warning")
        return
    
    notify(state, f"Searching Internet Archive for '{state.search_query}'...", "info")
    
    # In a real implementation, we would:
    # sort_mapping = {
    #     "Most Popular": "downloads desc",
    #     "Relevance": "",
    #     "Date Added": "addeddate desc",
    #     "Title": "title asc"
    # }
    # sort_param = sort_mapping[state.sort_by]
    # 
    # results = state.archive_client.search_books(
    #     state.search_query,
    #     max_results=state.max_results,
    #     media_type=state.media_type,
    #     sort=sort_param
    # )
    
    # For now, simulate search results
    time.sleep(1)  # Simulate search time
    
    # Simulated results
    state.search_results = [
        {
            "identifier": "book1",
            "title": "Sample Book 1",
            "author": "Author 1",
            "date": "2020",
            "subjects": ["Fiction", "Fantasy"],
            "downloads": 1250,
            "cover_url": "https://archive.org/images/notfound.png"
        },
        {
            "identifier": "book2",
            "title": "Sample Book 2",
            "author": "Author 2",
            "date": "2018",
            "subjects": ["Non-fiction", "Science"],
            "downloads": 980,
            "cover_url": "https://archive.org/images/notfound.png"
        },
        {
            "identifier": "book3",
            "title": "Sample Book 3",
            "author": "Author 3",
            "date": "2021",
            "subjects": ["History", "Biography"],
            "downloads": 765,
            "cover_url": "https://archive.org/images/notfound.png"
        },
        {
            "identifier": "book4",
            "title": "Sample Book 4",
            "author": "Author 4",
            "date": "2019",
            "subjects": ["Fiction", "Mystery"],
            "downloads": 1520,
            "cover_url": "https://archive.org/images/notfound.png"
        },
        {
            "identifier": "book5",
            "title": "Sample Book 5",
            "author": "Author 5",
            "date": "2017",
            "subjects": ["Fiction", "Science Fiction"],
            "downloads": 2100,
            "cover_url": "https://archive.org/images/notfound.png"
        },
        {
            "identifier": "book6",
            "title": "Sample Book 6",
            "author": "Author 6",
            "date": "2022",
            "subjects": ["Non-fiction", "Technology"],
            "downloads": 890,
            "cover_url": "https://archive.org/images/notfound.png"
        }
    ]
    
    # Update state
    state.has_results = True
    state.results_count_text = f"Showing {len(state.search_results)} results"
    state.search_results_heading = f"## Search Results for '{state.search_query}'"
    
    # Generate book grid content
    state.book_grid_content = render_book_grid(state.search_results)
    
    # Add log entry
    add_log(state, f"Found {len(state.search_results)} results for '{state.search_query}'", "SUCCESS")

def on_download_book(state, book_id):
    """
    Download a specific book from the Internet Archive.
    
    Args:
        state: The application state
        book_id: The identifier of the book to download
    """
    # Find the book
    book = next((b for b in state.search_results if b["identifier"] == book_id), None)
    
    if not book:
        notify(state, "Book not found", "error")
        return
    
    notify(state, f"Downloading '{book['title']}'...", "info")
    add_log(state, f"Starting download of '{book['title']}'", "INFO")
    
    # In a real implementation, we would:
    # format_info = state.archive_client.get_available_formats(book_id)[0]
    # local_path = state.archive_client.download_book(
    #     book_id,
    #     format_info['url'],
    #     book['title'],
    #     book['author']
    # )
    # 
    # result = state.document_processor.process_document(
    #     local_path,
    #     include_images=True,
    #     ocr_enabled=False
    # )
    # 
    # book_id = state.book_manager.add_book(
    #     book['title'],
    #     book['author'],
    #     book['subjects'][:5],
    #     file_path=local_path,
    #     content=result.get("text", "")
    # )
    # 
    # metadata = {
    #     "title": book['title'],
    #     "author": book['author'],
    #     "source": "Internet Archive",
    #     "identifier": book_id,
    #     "categories": book['subjects'][:5],
    #     "book_id": book_id
    # }
    # 
    # doc_id = state.knowledge_base.generate_id()
    # state.knowledge_base.add_document(
    #     doc_id,
    #     result.get("text", ""),
    #     metadata
    # )
    
    # Simulate download and processing
    for i in range(5):
        # Simulate steps: download, extract, add to db, index
        step_messages = [
            "Downloading file...",
            "Extracting text content...",
            "Adding to book database...",
            "Indexing in knowledge base...",
            "Finalizing..."
        ]
        add_log(state, step_messages[i], "INFO")
        time.sleep(0.5)  # Simulate processing time
    
    add_log(state, f"Successfully added '{book['title']}' to knowledge base", "SUCCESS")
    notify(state, f"Successfully added '{book['title']}' to knowledge base", "success")

def on_download_all(state):
    """
    Download all books in the search results.
    
    Args:
        state: The application state
    """
    if not state.search_results:
        notify(state, "No books to download", "warning")
        return
    
    notify(state, f"Starting bulk download of {len(state.search_results)} books...", "info")
    add_log(state, f"Starting bulk download of {len(state.search_results)} books", "INFO")
    
    # In a real implementation, we would download and process each book
    # For now, simulate the process
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, book in enumerate(state.search_results):
        add_log(state, f"Processing {i+1}/{len(state.search_results)}: {book['title']}", "INFO")
        
        # Simulate success/error/skip (with mostly success)
        result = "success" if i % 5 != 0 else ("error" if i % 5 == 0 and i > 0 else "skip")
        
        if result == "success":
            add_log(state, f"Successfully added '{book['title']}' to knowledge base", "SUCCESS")
            success_count += 1
        elif result == "error":
            add_log(state, f"Error processing '{book['title']}'", "ERROR")
            error_count += 1
        else:
            add_log(state, f"Skipped existing book: '{book['title']}'", "INFO")
            skipped_count += 1
        
        time.sleep(0.3)  # Simulate processing time
    
    add_log(state, f"Bulk download complete: {success_count} added, {skipped_count} skipped, {error_count} failed", "SUCCESS")
    notify(state, f"Bulk download complete: {success_count} added, {skipped_count} skipped, {error_count} failed", "success")

def on_clear_logs(state):
    """
    Clear the processing logs.
    
    Args:
        state: The application state
    """
    state.processing_logs = []
    state.processing_logs_content = "<p>No logs yet.</p>"
    state.has_logs = False
    notify(state, "Logs cleared", "info")

def add_log(state, message, level="INFO"):
    """
    Add a log entry to the processing logs.
    
    Args:
        state: The application state
        message: The log message
        level: The log level
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    state.processing_logs.append({
        "timestamp": timestamp,
        "level": level,
        "message": message
    })
    
    state.has_logs = True
    state.processing_logs_content = render_logs(state.processing_logs)

def render_book_grid(books):
    """
    Render the book grid.
    
    Args:
        books: List of book dictionaries
        
    Returns:
        HTML string for rendering the book grid
    """
    if not books:
        return "<p>No books found.</p>"
    
    html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px;'>"
    
    for book in books:
        book_id = book["identifier"]
        title = book["title"]
        author = book["author"]
        date = book.get("date", "Unknown date")
        downloads = book.get("downloads", 0)
        cover_url = book.get("cover_url", "https://archive.org/images/notfound.png")
        
        html += f"""
        <div class='card' style='height: 100%; display: flex; flex-direction: column;'>
            <div style='text-align: center; padding: 10px; background-color: #f5f8fa;'>
                <img src="{cover_url}" style='max-height: 150px; max-width: 100%;'>
            </div>
            <div style='padding: 12px; flex-grow: 1;'>
                <h3 style='font-size: 16px; margin-bottom: 5px;'>{title}</h3>
                <p style='font-size: 14px; color: #546e7a; margin-bottom: 5px;'>{author}</p>
                <p style='font-size: 12px; color: #78909c;'>{date} • {f'{downloads:,} downloads' if downloads else ''}</p>
            </div>
            <div style='padding: 12px; border-top: 1px solid #f1f1f1; display: flex; justify-content: space-between;'>
                <a href="https://archive.org/details/{book_id}" target="_blank" style="text-decoration:none; font-size:13px;">Preview ↗</a>
                <button onclick="on_download_book('{book_id}')">Download</button>
            </div>
        </div>
        """
    
    html += "</div>"
    return html

def render_logs(logs):
    """
    Render the processing logs.
    
    Args:
        logs: List of log dictionaries
        
    Returns:
        HTML string for rendering the logs
    """
    if not logs:
        return "<p>No logs yet.</p>"
    
    html = "<div class='logs-container'>"
    
    for log in logs:
        timestamp = log["timestamp"]
        level = log["level"]
        message = log["message"]
        
        # Determine class based on level
        level_class = "console-info"
        if level == "SUCCESS":
            level_class = "console-success"
        elif level == "WARNING":
            level_class = "console-warning"
        elif level == "ERROR":
            level_class = "console-error"
        
        html += f"""
        <div class='console-message {level_class}'>
            <span class='console-timestamp'>[{timestamp}]</span>
            <span class='console-level'>[{level}]</span>
            <span class='console-content'>{message}</span>
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
    # Search form state
    if "search_query" not in state:
        state.search_query = ""
    if "max_results" not in state:
        state.max_results = 24
    if "media_type" not in state:
        state.media_type = "texts"
    if "media_types" not in state:
        state.media_types = ["texts", "audio", "movies"]
    if "sort_by" not in state:
        state.sort_by = "Most Popular"
    if "sort_options" not in state:
        state.sort_options = ["Most Popular", "Relevance", "Date Added", "Title"]
    
    # Search results state
    if "search_results" not in state:
        state.search_results = []
    if "has_results" not in state:
        state.has_results = False
    if "search_results_heading" not in state:
        state.search_results_heading = ""
    if "results_count_text" not in state:
        state.results_count_text = ""
    if "book_grid_content" not in state:
        state.book_grid_content = ""
    
    # Processing logs state
    if "processing_logs" not in state:
        state.processing_logs = []
    if "has_logs" not in state:
        state.has_logs = False
    if "processing_logs_content" not in state:
        state.processing_logs_content = "<p>No logs yet.</p>"