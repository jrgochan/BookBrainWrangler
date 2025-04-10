import os
from pathlib import Path
from database import get_connection
from book_manager.manager import BookManager
from knowledge_base import KnowledgeBase
from document_processing.processor import DocumentProcessor

def check_and_fix_book(book_id):
    """Check and fix a book with missing content."""
    print(f"Checking book ID {book_id}...")
    
    # Get book manager
    book_manager = BookManager()
    
    # Get book details
    book = book_manager.get_book(book_id)
    if not book:
        print(f"Error: Book ID {book_id} not found in database")
        return
    
    print(f"Book found: {book['title']} by {book['author']}")
    
    # Check book content
    content = book_manager.get_book_content(book_id)
    if content:
        print(f"Book already has content ({len(content)} characters)")
        return
    
    print("Book has no content in database")
    
    # Check if file exists
    file_path = book.get('file_path')
    if not file_path:
        print("Error: Book has no file path")
        print("Deleting book with missing file path")
        book_manager.delete_book(book_id)
        print(f"Book ID {book_id} deleted from database")
        return
    
    print(f"File path: {file_path}")
    
    # Initialize flag to track if we successfully processed the content
    content_processed = False
    
    if os.path.exists(file_path):
        print(f"File exists at: {file_path}")
        
        # Process the file and add content
        print("Processing file to extract content...")
        
        try:
            # Get document processor
            document_processor = DocumentProcessor()
            
            # Extract content
            extracted_content = document_processor.extract_content(file_path)
            
            if not extracted_content:
                print("Error: Failed to extract content from file")
            else:
                # Add content to database
                conn = get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT OR REPLACE INTO book_contents (book_id, content) VALUES (?, ?)",
                    (book_id, extracted_content.get('text') if isinstance(extracted_content, dict) else extracted_content)
                )
                
                conn.commit()
                conn.close()
                
                print(f"Successfully added content to book ID {book_id}")
                
                # Verify content was added
                content = book_manager.get_book_content(book_id)
                if content:
                    content_sample = content[:200] + '...' if len(content) > 200 else content
                    print(f"Content added successfully ({len(content)} characters)")
                    print(f"Sample: {content_sample}")
                    content_processed = True
                else:
                    print("Error: Content still not found after adding")
                
        except Exception as e:
            print(f"Error processing file: {str(e)}")
    else:
        print(f"Error: File not found at path: {file_path}")
    
    # If the process didn't complete successfully, delete the book
    if not content_processed:
        print(f"Deleting book ID {book_id} since content couldn't be processed")
        book_manager.delete_book(book_id)
        print(f"Book ID {book_id} deleted from database")
    else:
        print("Processing completed successfully")

if __name__ == "__main__":
    import sys
    
    # Default book ID is 10 (Popular Mechanics)
    book_id = 10
    
    # Use command-line argument if provided
    if len(sys.argv) > 1:
        try:
            book_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid book ID: {sys.argv[1]}")
            sys.exit(1)
    
    check_and_fix_book(book_id)
