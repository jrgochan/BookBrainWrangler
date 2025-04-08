import os
import json
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings
from database import get_connection

class KnowledgeBase:
    def __init__(self):
        """Initialize the knowledge base."""
        # Create data directory if it doesn't exist
        self.data_dir = "knowledge_base_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create the database file if it doesn't exist
        self._init_database()
        
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Initialize with a simple embedding model for demonstration
        # In a production environment, you would use a proper embedding model
        self.embeddings = FakeEmbeddings(size=768)
        
        # Initialize the vector store
        self.vector_store = Chroma(
            persist_directory=os.path.join(self.data_dir, "chroma_db"),
            embedding_function=self.embeddings
        )
    
    def _init_database(self):
        """Initialize the knowledge base database tables if they don't exist."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create knowledge_base_books table to track which books are in the knowledge base
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base_books (
                book_id INTEGER PRIMARY KEY,
                added_at TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def toggle_book_in_knowledge_base(self, book_id, book_content, add_to_kb=True, progress_callback=None):
        """
        Add or remove a book from the knowledge base.
        
        Args:
            book_id: The ID of the book
            book_content: The text content of the book
            add_to_kb: If True, add to KB; if False, remove from KB
            progress_callback: Optional callback function for progress updates
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        if progress_callback:
            action = "Adding to" if add_to_kb else "Removing from"
            progress_callback(0, 3, f"{action} knowledge base...")
        
        try:
            if add_to_kb:
                # Check if the book is already in the knowledge base
                cursor.execute('SELECT 1 FROM knowledge_base_books WHERE book_id = ?', (book_id,))
                if cursor.fetchone():
                    # Book is already in KB, nothing to do
                    if progress_callback:
                        progress_callback(3, 3, "Book is already in knowledge base")
                    return
                
                if progress_callback:
                    progress_callback(1, 3, "Processing book content...")
                
                # Process and add the book to the vector store
                self._add_to_vector_store(book_id, book_content)
                
                if progress_callback:
                    progress_callback(2, 3, "Updating database...")
                
                # Record the addition in the database
                cursor.execute(
                    'INSERT INTO knowledge_base_books (book_id, added_at) VALUES (?, ?)',
                    (book_id, time.time())
                )
                
                if progress_callback:
                    progress_callback(3, 3, "Book successfully added to knowledge base")
                
            else:
                # Check if the book is in the knowledge base
                cursor.execute('SELECT 1 FROM knowledge_base_books WHERE book_id = ?', (book_id,))
                if not cursor.fetchone():
                    # Book is not in KB, nothing to do
                    if progress_callback:
                        progress_callback(3, 3, "Book is not in knowledge base")
                    return
                
                if progress_callback:
                    progress_callback(1, 3, "Removing book from vector store...")
                
                # Remove the book from the vector store
                self._remove_from_vector_store(book_id)
                
                if progress_callback:
                    progress_callback(2, 3, "Updating database...")
                
                # Remove the record from the database
                cursor.execute('DELETE FROM knowledge_base_books WHERE book_id = ?', (book_id,))
                
                if progress_callback:
                    progress_callback(3, 3, "Book successfully removed from knowledge base")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            if progress_callback:
                progress_callback(0, 3, f"Error: {str(e)}")
            raise e
        finally:
            conn.close()
    
    def _add_to_vector_store(self, book_id, content):
        """
        Add a book's content to the vector store.
        
        Args:
            book_id: The ID of the book
            content: The text content to add
        """
        # Split the text into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Add metadata to each chunk to identify the source book
        texts_with_metadata = [
            {
                "text": chunk,
                "metadata": {"book_id": book_id}
            }
            for chunk in chunks
        ]
        
        # Add documents to vector store
        texts = [item["text"] for item in texts_with_metadata]
        metadatas = [item["metadata"] for item in texts_with_metadata]
        
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
        self.vector_store.persist()
    
    def _remove_from_vector_store(self, book_id):
        """
        Remove a book's content from the vector store.
        
        Args:
            book_id: The ID of the book to remove
        """
        # Currently, Chroma doesn't have a clean way to delete documents by metadata
        # We need to rebuild the knowledge base without the removed book
        # This is inefficient but ensures proper cleanup
        
        # Get all book IDs in the knowledge base
        book_ids = self.get_indexed_book_ids()
        
        # If the book is in the list, remove it
        if book_id in book_ids:
            book_ids.remove(book_id)
            
            # We need to rebuild the knowledge base with the remaining books
            self._rebuild_vector_store(book_ids)
    
    def _rebuild_vector_store(self, book_ids, progress_callback=None):
        """
        Rebuild the vector store with only the specified books.
        
        Args:
            book_ids: List of book IDs to include
            progress_callback: Optional callback function for progress updates
        """
        if progress_callback:
            progress_callback(0, len(book_ids) + 2, "Initializing knowledge base rebuild")
            
        if not book_ids:
            # If no books, just clear the vector store
            # Chroma doesn't have a clean way to reset, so we'll recreate it
            if progress_callback:
                progress_callback(0, 1, "No books selected. Clearing knowledge base.")
                
            import shutil
            chroma_dir = os.path.join(self.data_dir, "chroma_db")
            if os.path.exists(chroma_dir):
                shutil.rmtree(chroma_dir)
            
            # Reinitialize the vector store
            self.vector_store = Chroma(
                persist_directory=chroma_dir,
                embedding_function=self.embeddings
            )
            
            if progress_callback:
                progress_callback(1, 1, "Knowledge base cleared successfully")
            return
        
        # Get content for each book
        conn = get_connection()
        cursor = conn.cursor()
        
        all_texts = []
        all_metadatas = []
        
        # Process each book
        for i, book_id in enumerate(book_ids):
            if progress_callback:
                progress_callback(i, len(book_ids) + 2, f"Processing book {i+1} of {len(book_ids)}")
                
            try:
                cursor.execute('SELECT content FROM book_content WHERE book_id = ?', (book_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    content = result[0]
                    
                    # Split the text into chunks
                    if progress_callback:
                        progress_callback(i, len(book_ids) + 2, f"Splitting book {i+1} into chunks")
                    chunks = self.text_splitter.split_text(content)
                    
                    # Add each chunk with metadata
                    all_texts.extend(chunks)
                    all_metadatas.extend([{"book_id": book_id} for _ in chunks])
                    
                    if progress_callback:
                        progress_callback(i + 0.5, len(book_ids) + 2, f"Added {len(chunks)} chunks from book {i+1}")
            except Exception as e:
                print(f"Error processing book {book_id}: {e}")
                if progress_callback:
                    progress_callback(i, len(book_ids) + 2, f"Error processing book {i+1}: {e}")
        
        conn.close()
        
        # Clear the vector store
        if progress_callback:
            progress_callback(len(book_ids), len(book_ids) + 2, "Clearing previous knowledge base")
            
        import shutil
        chroma_dir = os.path.join(self.data_dir, "chroma_db")
        if os.path.exists(chroma_dir):
            shutil.rmtree(chroma_dir)
        
        # Reinitialize the vector store
        self.vector_store = Chroma(
            persist_directory=chroma_dir,
            embedding_function=self.embeddings
        )
        
        # Add all documents to the vector store
        if all_texts:
            if progress_callback:
                progress_callback(len(book_ids) + 1, len(book_ids) + 2, 
                                 f"Adding {len(all_texts)} text chunks to knowledge base")
            
            self.vector_store.add_texts(texts=all_texts, metadatas=all_metadatas)
            self.vector_store.persist()
            
            if progress_callback:
                progress_callback(len(book_ids) + 2, len(book_ids) + 2, "Knowledge base rebuild complete")
        elif progress_callback:
            progress_callback(len(book_ids) + 2, len(book_ids) + 2, "No text to add to knowledge base")
    
    def get_indexed_book_ids(self):
        """
        Get the IDs of all books in the knowledge base.
        
        Returns:
            List of book IDs
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT book_id FROM knowledge_base_books')
            return [row[0] for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def rebuild_knowledge_base(self, book_manager, progress_callback=None):
        """
        Rebuild the entire knowledge base from the books in the database.
        
        Args:
            book_manager: An instance of BookManager to get book content
            progress_callback: Optional callback function for progress updates
        """
        # Get all book IDs in the knowledge base
        book_ids = self.get_indexed_book_ids()
        
        if progress_callback:
            progress_callback(0, 1, f"Found {len(book_ids)} books in knowledge base")
        
        # Rebuild the vector store
        self._rebuild_vector_store(book_ids, progress_callback)
    
    def retrieve_relevant_context(self, query, num_results=5):
        """
        Retrieve relevant context from the knowledge base for a query.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            
        Returns:
            A string with the combined relevant text passages
        """
        try:
            # Query the vector store for similar documents
            docs = self.vector_store.similarity_search(query, k=num_results)
            
            # Combine the text from the results
            if docs:
                return "\n\n".join([doc.page_content for doc in docs])
            else:
                return "No relevant information found in the knowledge base."
                
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return "Error retrieving information from the knowledge base."
