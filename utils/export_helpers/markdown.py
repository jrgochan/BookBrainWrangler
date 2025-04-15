"""
Markdown export functionality for knowledge base data.
"""

import os
import datetime
from typing import Optional, Any, Callable, List

from database import get_connection
from utils.logger import get_logger
from .common import logger

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

def export_to_markdown(
    book_manager: Any, 
    knowledge_base: Any,
    include_metadata: bool = True,
    include_content: bool = True,
    include_embeddings: bool = False,  # Added parameter to match other export functions
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Export knowledge base to markdown format.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        include_metadata: Whether to include book metadata
        include_content: Whether to include chunk content
        include_embeddings: Whether to include embedding vectors (for consistency with other export formats)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Markdown string
    """
    # Get indexed books
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    total_books = len(kb_book_ids)
    
    if progress_callback:
        progress_callback(0.1, f"Exporting {total_books} books to Markdown")
    
    # Start building markdown
    now = datetime.datetime.now()
    markdown = []
    
    # Header
    markdown.append("# Knowledge Base Export")
    markdown.append(f"Generated on {now.strftime('%Y-%m-%d at %H:%M')}")
    markdown.append("")
    
    # Debug information about export options
    markdown.append("## Export Options")
    markdown.append(f"- **Include Metadata**: {'Yes' if include_metadata else 'No'}")
    markdown.append(f"- **Include Content**: {'Yes' if include_content else 'No'}")
    markdown.append(f"- **Include Embeddings**: {'Yes' if include_embeddings else 'No'}")
    markdown.append("")
    
    # Vector store information
    markdown.append("## Knowledge Base Information")
    kb_stats = knowledge_base.get_stats()
    markdown.append(f"- **Total Books**: {kb_stats.get('book_count', 0)}")
    markdown.append(f"- **Total Chunks**: {kb_stats.get('chunk_count', 0)}")
    markdown.append(f"- **Vector Dimensions**: {kb_stats.get('dimensions', 0)}")
    markdown.append(f"- **Vector Store Type**: {knowledge_base.vector_store_type}")
    markdown.append("")
    
    # Display book IDs found in the knowledge base
    markdown.append("## Book IDs in Knowledge Base")
    if kb_book_ids:
        for i, book_id in enumerate(kb_book_ids):
            markdown.append(f"- Book {i+1}: ID={book_id}")
    else:
        markdown.append("*No book IDs found in the knowledge base*")
    markdown.append("")
    
    # Books section
    markdown.append("## Books")
    
    # Flag to track if we found any books
    found_books = False
    
    # Process each book
    for i, book_id in enumerate(kb_book_ids):
        # Calculate progress percentage based on book index
        progress = 0.1 + (0.8 * (i / total_books)) if total_books > 0 else 0.5
        
        # Get book details
        try:
            # Try to get the book from the book manager
            book = book_manager.get_book(book_id)
            
            if book:
                found_books = True
                if progress_callback:
                    progress_callback(progress, f"Processing book {i+1}/{total_books}: {book['title']}")
                
                # Book header
                markdown.append(f"### {i+1}. {book['title']}")
                
                # Metadata
                if include_metadata:
                    markdown.append(f"- **Author**: {book['author']}")
                    markdown.append(f"- **Categories**: {', '.join(book['categories']) if 'categories' in book and book['categories'] else 'None'}")
                    markdown.append(f"- **ID**: {book['id']}")
                    markdown.append("")
                
                # Content
                if include_content:
                    # Get chunks for this book
                    chunks = knowledge_base.get_document_chunks(book_id)
                    
                    if chunks and len(chunks) > 0:
                        markdown.append("#### Content Excerpts")
                        
                        # Show first 5 chunks
                        for j, chunk in enumerate(chunks[:5]):
                            markdown.append(f"##### Excerpt {j+1}")
                            content = getattr(chunk, 'page_content', str(chunk))
                            markdown.append(content)
                            markdown.append("")
                        
                        if len(chunks) > 5:
                            markdown.append(f"*...plus {len(chunks) - 5} more excerpts*")
                    else:
                        markdown.append("*No content chunks available for this book*")
                
                # Add embeddings information if requested
                if include_embeddings:
                    markdown.append("#### Embedding Information")
                    chunks = knowledge_base.get_document_chunks(book_id)
                    
                    for chunk in chunks[:2]:  # Show at most 2 embeddings
                        if hasattr(chunk, 'embedding') and chunk.embedding:
                            embedding = chunk.embedding
                            # Show a truncated version of the embedding
                            embedding_preview = str(embedding[:5]) + "... [truncated, total dimensions: " + str(len(embedding)) + "]"
                            markdown.append("```")
                            markdown.append(embedding_preview)
                            markdown.append("```")
                            break
                    else:
                        markdown.append("*No embedding vectors available*")
                        
                markdown.append("---")
                markdown.append("")
            else:
                if progress_callback:
                    progress_callback(progress, f"Book ID {book_id} not found in book manager")
        except Exception as e:
            logger.error(f"Error processing book ID {book_id}: {str(e)}")
            if progress_callback:
                progress_callback(progress, f"Error processing book ID {book_id}: {str(e)}")
            
            # Add error information to the markdown
            markdown.append(f"### Error Processing Book (ID: {book_id})")
            markdown.append(f"*Error: {str(e)}*")
            markdown.append("---")
            markdown.append("")
    
    # If no books were found, display a message
    if not found_books:
        markdown.append("*No books found in the book manager matching the IDs from the knowledge base*")
        
        # Try to display some content anyway if we have chunks
        if include_content and kb_stats.get('chunk_count', 0) > 0:
            markdown.append("\n## Content Samples")
            markdown.append("*Since no books were found, here are some content samples from the knowledge base:*\n")
            
            # Get some sample chunks
            try:
                # Try different approaches to get some chunks
                samples = []
                
                # Approach 1: Try to get chunks from a specific book ID
                for book_id in kb_book_ids[:1]:  # Try with the first book ID
                    chunks = knowledge_base.get_document_chunks(book_id)
                    if chunks:
                        samples.extend(chunks[:5])
                
                # If we still don't have samples, add placeholder
                if not samples:
                    markdown.append("*Unable to retrieve content samples*")
                else:
                    for i, chunk in enumerate(samples[:5]):
                        markdown.append(f"### Content Sample {i+1}")
                        content = getattr(chunk, 'page_content', str(chunk))
                        markdown.append(content)
                        markdown.append("")
            except Exception as e:
                markdown.append(f"*Error retrieving content samples: {str(e)}*")
    
    if progress_callback:
        progress_callback(0.95, "Finalizing Markdown export")
    
    return "\n".join(markdown)
