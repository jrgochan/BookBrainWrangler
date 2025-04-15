"""
Knowledge Base page for the Book Knowledge AI application.
"""

from taipy.gui import navigate, notify, Markdown

# Define the knowledge base page template
knowledge_base_template = """
<|container|class_name=page-container|
# 🧠 Knowledge Base

<|tabs|
<|tab|label=Search Knowledge Base|
<|container|class_name=card|
## Search Knowledge Base

<|{search_query}|input|label=Search your knowledge base|>
<|{on_search_knowledge_base}|button|label=Search|>

<|container|class_name=search-results|
{search_results_content}
|>
|>
|>

<|tab|label=Explore Documents|
<|container|class_name=card|
## Explore Documents

<|{document_filter}|selector|lov={document_categories}|label=Filter by category|>
<|{on_filter_documents}|button|label=Apply Filter|>

<|container|class_name=document-list|
{document_list_content}
|>
|>
|>

<|tab|label=Vector Store Analytics|
<|container|class_name=card|
## Vector Store Analytics

<|chart|type=bar|x=labels|y=values|data={vector_store_stats}|>

<|container|class_name=analytics-stats|
<|layout|columns=1 1 1 1|
<|card|
### {total_vectors}
Total Vectors
|>

<|card|
### {total_documents}
Documents
|>

<|card|
### {avg_chunks_per_doc}
Avg. Chunks/Doc
|>

<|card|
### {index_size}
Index Size
|>
|>
|>
|>
|>
|>
"""

def get_template():
    """Get the knowledge base page template."""
    return knowledge_base_template

def on_search_knowledge_base(state):
    """
    Search the knowledge base for the given query.
    
    Args:
        state: The application state
    """
    if not state.search_query:
        notify(state, "Please enter a search query", "warning")
        return
    
    # In a real implementation, we would:
    # results = state.knowledge_base.search(state.search_query, limit=10)
    
    # For now, simulate some results
    state.search_results = [
        {
            "text": "This is a sample result that matches the query. It contains information about the search topic.",
            "metadata": {
                "title": "Sample Document 1",
                "author": "Author 1",
                "score": 0.92
            }
        },
        {
            "text": "Another sample result that is relevant to the search. It provides additional details about the topic.",
            "metadata": {
                "title": "Sample Document 2",
                "author": "Author 2",
                "score": 0.85
            }
        },
        {
            "text": "A third sample result with less relevance, but still containing useful information about the search topic.",
            "metadata": {
                "title": "Sample Document 3",
                "author": "Author 3",
                "score": 0.78
            }
        }
    ]
    
    # Update the UI content
    state.search_results_content = render_search_results(state.search_results)

def on_filter_documents(state):
    """
    Filter documents by category.
    
    Args:
        state: The application state
    """
    # In a real implementation, we would:
    # if state.document_filter == "All":
    #     documents = state.knowledge_base.get_all_documents()
    # else:
    #     documents = state.knowledge_base.get_documents_by_category(state.document_filter)
    
    # For now, simulate some documents
    state.documents = [
        {
            "id": "doc1",
            "title": "Sample Document 1",
            "author": "Author 1",
            "categories": ["Fiction", "Fantasy"],
            "chunk_count": 15,
            "word_count": 5000
        },
        {
            "id": "doc2",
            "title": "Sample Document 2",
            "author": "Author 2",
            "categories": ["Non-fiction", "Science"],
            "chunk_count": 22,
            "word_count": 7500
        },
        {
            "id": "doc3",
            "title": "Sample Document 3",
            "author": "Author 3",
            "categories": ["History", "Biography"],
            "chunk_count": 18,
            "word_count": 6200
        }
    ]
    
    # Filter if needed
    if state.document_filter and state.document_filter != "All":
        state.documents = [
            doc for doc in state.documents 
            if state.document_filter in doc["categories"]
        ]
    
    # Update the UI content
    state.document_list_content = render_document_list(state.documents)

def render_search_results(results):
    """
    Render search results.
    
    Args:
        results: List of search result dictionaries
        
    Returns:
        HTML string for rendering the search results
    """
    if not results:
        return "<p>No results found.</p>"
    
    html = "<div class='search-results-list'>"
    
    for i, result in enumerate(results):
        score_percentage = int(result["metadata"]["score"] * 100)
        
        html += f"""
        <div class='card' style='margin-bottom: 1rem;'>
            <div style='display: flex; justify-content: space-between;'>
                <h3>{result["metadata"]["title"]}</h3>
                <span style='background-color: #e3f2fd; color: #1565c0; padding: 0.25rem 0.5rem; border-radius: 4px;'>
                    {score_percentage}% match
                </span>
            </div>
            <p><strong>Author:</strong> {result["metadata"]["author"]}</p>
            <p>{result["text"]}</p>
            <button onclick="state.result_to_view = {i}">View in Context</button>
        </div>
        """
    
    html += "</div>"
    return html

def render_document_list(documents):
    """
    Render document list.
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        HTML string for rendering the document list
    """
    if not documents:
        return "<p>No documents found.</p>"
    
    html = "<div class='document-list'>"
    
    for doc in documents:
        categories = ", ".join(doc["categories"]) if doc["categories"] else "No categories"
        
        html += f"""
        <div class='card' style='margin-bottom: 1rem;'>
            <h3>{doc["title"]}</h3>
            <p><strong>Author:</strong> {doc["author"]}</p>
            <p><strong>Categories:</strong> {categories}</p>
            <p><strong>Chunks:</strong> {doc["chunk_count"]} | <strong>Words:</strong> {doc["word_count"]}</p>
            <div>
                <button onclick="state.document_to_view = '{doc['id']}'">View Details</button>
                <button onclick="state.document_to_explore = '{doc['id']}'">Explore Chunks</button>
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
    # Search state
    if "search_query" not in state:
        state.search_query = ""
    if "search_results" not in state:
        state.search_results = []
    if "search_results_content" not in state:
        state.search_results_content = "<p>Enter a search query to see results.</p>"
    
    # Document exploration state
    if "document_filter" not in state:
        state.document_filter = "All"
    if "document_categories" not in state:
        state.document_categories = ["All", "Fiction", "Non-fiction", "Science", "History", "Biography", "Fantasy"]
    if "documents" not in state:
        state.documents = []
    if "document_list_content" not in state:
        state.document_list_content = "<p>Select a filter to view documents.</p>"
    
    # Analytics state
    if "vector_store_stats" not in state:
        state.vector_store_stats = {
            "labels": ["Documents", "Vectors", "Categories", "Books"],
            "values": [25, 1250, 15, 25]
        }
    if "total_vectors" not in state:
        state.total_vectors = "1,250"
    if "total_documents" not in state:
        state.total_documents = "25"
    if "avg_chunks_per_doc" not in state:
        state.avg_chunks_per_doc = "50"
    if "index_size" not in state:
        state.index_size = "42 MB"
    
    # Action state
    if "result_to_view" not in state:
        state.result_to_view = None
    if "document_to_view" not in state:
        state.document_to_view = None
    if "document_to_explore" not in state:
        state.document_to_explore = None