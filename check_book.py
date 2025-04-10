from database import get_connection
from loguru import logger

def check_book(book_id):
    """Check book details and content in database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check book details
    cursor.execute("SELECT id, title, author, file_path FROM books WHERE id=?", (book_id,))
    book = cursor.fetchone()
    
    if book:
        book_id, title, author, file_path = book
        print(f"Book found: ID={book_id}, Title='{title}', Author='{author}', File Path='{file_path}'")
        
        # Check book content
        cursor.execute("SELECT content FROM book_contents WHERE book_id=?", (book_id,))
        content_row = cursor.fetchone()
        
        if content_row:
            content = content_row[0]
            content_length = len(content) if content else 0
            print(f"Content found: {content_length} characters")
            print(f"Content sample: {content[:200]}..." if content_length > 200 else content)
        else:
            print(f"ERROR: No content found for book ID {book_id}")
            
        # Check categories
        cursor.execute("""
            SELECT categories.name
            FROM categories
            JOIN book_categories ON categories.id = book_categories.category_id
            WHERE book_categories.book_id = ?
        """, (book_id,))
        
        categories = [row[0] for row in cursor.fetchall()]
        print(f"Categories: {', '.join(categories) if categories else 'None'}")
        
    else:
        print(f"Book with ID {book_id} not found")

if __name__ == "__main__":
    target_book_id = 10
    print(f"Checking book ID {target_book_id}:")
    check_book(target_book_id)
