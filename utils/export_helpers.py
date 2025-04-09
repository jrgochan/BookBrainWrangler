"""
Export utilities for generating content from the knowledge base.
"""

import os
import datetime
from typing import Optional, Dict, List, Any, Union

from database import get_connection
from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def generate_knowledge_export(book_manager: Any, knowledge_base: Any, 
                           query: Optional[str] = None, 
                           include_content: bool = True, 
                           max_topics: int = 5, 
                           max_books: Optional[int] = None) -> str:
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
                markdown.append("No relevant information found for this category.")
                markdown.append("")
    
    return "\n".join(markdown)

def save_markdown_to_file(markdown_content: str, file_path: Optional[str] = None) -> str:
    """
    Save markdown content to a file.
    
    Args:
        markdown_content: The markdown content as a string
        file_path: Path where to save the file (if None, generates a default name)
        
    Returns:
        Path to the saved file
    """
    if not file_path:
        # Generate a default filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join("exports", f"knowledge_export_{timestamp}.md")
    
    # Create directory if it doesn't exist
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    # Write the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    logger.info(f"Saved markdown export to {file_path}")
    return file_path