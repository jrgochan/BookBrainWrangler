import os
import json
import time
import uuid
import shutil
import tempfile
import importlib.util
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from database import get_connection

# Try to import Chroma from langchain_chroma (new package)
# Fall back to langchain_community.vectorstores if not available
try:
    from langchain_chroma import Chroma
    print("Using langchain_chroma.Chroma")
except ImportError:
    # Fall back to the old import path
    print("langchain_chroma not found, falling back to langchain_community.vectorstores")
    from langchain_community.vectorstores import Chroma

class KnowledgeBase:
    def __init__(self):
        """Initialize the knowledge base."""
        # Create a writable data directory
        self.data_dir = self._get_writable_data_dir()
        
        # Create the database file if it doesn't exist
        self._init_database()
        
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Try to use HuggingFaceEmbeddings, fall back to FakeEmbeddings if not available
        try:
            # Use all-MiniLM-L6-v2 model which is small but performs well for semantic search
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                cache_folder=self.data_dir
            )
            print("Using HuggingFaceEmbeddings with all-MiniLM-L6-v2 model")
        except Exception as e:
            print(f"Could not initialize HuggingFaceEmbeddings: {e}")
            print("Falling back to FakeEmbeddings - NOTE: This will not provide meaningful search results!")
            # Use dimension of 768 as that seems to be already in use in the collection
            self.embeddings = FakeEmbeddings(size=768)
        
        # Initialize the vector store with safety checks
        chroma_dir = os.path.join(self.data_dir, "chroma_db")
        
        # Check if the directory exists and is valid
        try:
            # Try to initialize with existing directory
            if os.path.exists(chroma_dir):
                try:
                    self.vector_store = Chroma(
                        persist_directory=chroma_dir,
                        embedding_function=self.embeddings
                    )
                    # Test if it works
                    self.vector_store.get()
                except Exception as e:
                    print(f"Error loading existing Chroma DB: {e}")
                    print("Creating a new database...")
                    # If there's an error, create a new database
                    if os.path.exists(chroma_dir):
                        try:
                            # Backup the old database
                            backup_dir = chroma_dir + "_backup_" + str(int(time.time()))
                            shutil.move(chroma_dir, backup_dir)
                            print(f"Backed up problematic database to {backup_dir}")
                        except Exception as backup_error:
                            print(f"Could not backup old database: {backup_error}")
                            # Try to delete it instead
                            try:
                                shutil.rmtree(chroma_dir)
                            except Exception as delete_error:
                                print(f"Could not delete old database: {delete_error}")
                    
                    # Create new directory and initialize fresh database
                    os.makedirs(chroma_dir, exist_ok=True)
                    self.vector_store = Chroma(
                        persist_directory=chroma_dir,
                        embedding_function=self.embeddings
                    )
            else:
                # Directory doesn't exist, create new
                os.makedirs(chroma_dir, exist_ok=True)
                self.vector_store = Chroma(
                    persist_directory=chroma_dir,
                    embedding_function=self.embeddings
                )
        except Exception as init_error:
            print(f"Fatal error initializing Chroma: {init_error}")
            # Last resort fallback to in-memory database
            print("Falling back to in-memory database (temporary only)")
            self.vector_store = Chroma(
                embedding_function=self.embeddings
            )
    
    def _get_writable_data_dir(self):
        """
        Get a writable directory for knowledge base data.
        Uses Python's tempfile module to create a directory that is guaranteed to be writable
        in the current environment.
        
        Returns:
            Path to a writable directory
        """
        try:
            # First, use the standard directory if it's writable
            standard_dir = os.path.abspath("knowledge_base_data")
            os.makedirs(standard_dir, exist_ok=True)
            
            # Check if it's writable with a simple test
            test_file = os.path.join(standard_dir, "test_write.txt")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"Using standard directory for knowledge base: {standard_dir}")
                return standard_dir
            except (IOError, PermissionError) as e:
                print(f"Cannot write to {standard_dir}: {str(e)}")
                
            # Use Python's tempfile to create a directory that's guaranteed to be writable
            # Get a unique temporary directory that persists until manually deleted
            temp_base = tempfile.gettempdir()  # Gets the system's temp directory
            kb_dir = os.path.join(temp_base, 'book_knowledge_base')
            os.makedirs(kb_dir, exist_ok=True)
            
            print(f"Using temporary directory for knowledge base: {kb_dir}")
            return kb_dir
            
        except Exception as e:
            # If all else fails, create a directory in the current working directory
            fallback_dir = os.path.join(os.getcwd(), "kb_data")
            os.makedirs(fallback_dir, exist_ok=True)
            print(f"Using fallback directory for knowledge base: {fallback_dir}")
            return fallback_dir
    
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
            
        # Create a completely new vector store to avoid compatibility issues
        import shutil
        
        # Generate a unique directory name to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        new_chroma_dir = os.path.join(self.data_dir, f"chroma_db_{unique_id}")
        os.makedirs(new_chroma_dir, exist_ok=True)
        
        if not book_ids:
            # If no books, just create an empty vector store
            if progress_callback:
                progress_callback(0, 1, "No books selected. Creating empty knowledge base.")
            
            # Create a new empty vector store
            try:
                new_vector_store = Chroma(
                    persist_directory=new_chroma_dir,
                    embedding_function=self.embeddings
                )
                # Test it works by adding and removing a dummy document
                new_vector_store.add_texts(texts=["Test document"], metadatas=[{"test": True}])
                new_vector_store.persist()
                
                # If successful, replace the old vector store
                self.vector_store = new_vector_store
                
                # Clean up old directory if it exists
                old_chroma_dir = os.path.join(self.data_dir, "chroma_db")
                if os.path.exists(old_chroma_dir) and old_chroma_dir != new_chroma_dir:
                    try:
                        shutil.rmtree(old_chroma_dir)
                    except Exception as e:
                        print(f"Warning: Could not remove old directory: {e}")
                
                # Rename the new directory to the standard name
                try:
                    if os.path.exists(old_chroma_dir):
                        os.rename(new_chroma_dir, old_chroma_dir + "_new")
                        self.vector_store = Chroma(
                            persist_directory=old_chroma_dir + "_new",
                            embedding_function=self.embeddings
                        )
                    else:
                        os.rename(new_chroma_dir, old_chroma_dir)
                        self.vector_store = Chroma(
                            persist_directory=old_chroma_dir,
                            embedding_function=self.embeddings
                        )
                except Exception as e:
                    print(f"Warning: Could not rename directory: {e}")
                    # Just keep using the temporary directory
                    self.vector_store = Chroma(
                        persist_directory=new_chroma_dir,
                        embedding_function=self.embeddings
                    )
                
                if progress_callback:
                    progress_callback(1, 1, "Knowledge base cleared successfully")
                return
            except Exception as e:
                print(f"Error creating new vector store: {e}")
                if progress_callback:
                    progress_callback(0, 1, f"Error: {str(e)}")
                raise e
        
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
        
        # Create a new vector store
        if progress_callback:
            progress_callback(len(book_ids), len(book_ids) + 2, "Creating new knowledge base")
            
        try:
            # Create new vector store in the temporary directory
            new_vector_store = Chroma(
                persist_directory=new_chroma_dir,
                embedding_function=self.embeddings
            )
            
            # Add all documents to the new vector store
            if all_texts:
                if progress_callback:
                    progress_callback(len(book_ids) + 1, len(book_ids) + 2, 
                                    f"Adding {len(all_texts)} text chunks to knowledge base")
                
                new_vector_store.add_texts(texts=all_texts, metadatas=all_metadatas)
                new_vector_store.persist()
                
                # If successful, replace the old vector store
                self.vector_store = new_vector_store
                
                # Clean up old directory if it exists
                old_chroma_dir = os.path.join(self.data_dir, "chroma_db")
                if os.path.exists(old_chroma_dir) and old_chroma_dir != new_chroma_dir:
                    try:
                        shutil.rmtree(old_chroma_dir)
                    except Exception as e:
                        print(f"Warning: Could not remove old directory: {e}")
                
                # Rename the new directory to the standard name
                try:
                    if os.path.exists(old_chroma_dir):
                        os.rename(new_chroma_dir, old_chroma_dir + "_new")
                        self.vector_store = Chroma(
                            persist_directory=old_chroma_dir + "_new",
                            embedding_function=self.embeddings
                        )
                    else:
                        os.rename(new_chroma_dir, old_chroma_dir)
                        self.vector_store = Chroma(
                            persist_directory=old_chroma_dir,
                            embedding_function=self.embeddings
                        )
                except Exception as e:
                    print(f"Warning: Could not rename directory: {e}")
                    # Just keep using the temporary directory
                    self.vector_store = Chroma(
                        persist_directory=new_chroma_dir,
                        embedding_function=self.embeddings
                    )
                
                if progress_callback:
                    progress_callback(len(book_ids) + 2, len(book_ids) + 2, "Knowledge base rebuild complete")
            elif progress_callback:
                progress_callback(len(book_ids) + 2, len(book_ids) + 2, "No text to add to knowledge base")
                
        except Exception as e:
            print(f"Error creating new vector store: {e}")
            if progress_callback:
                progress_callback(len(book_ids), len(book_ids) + 2, f"Error: {str(e)}")
            raise e
    
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
            
            # Get book titles for the retrieved chunks to provide better context
            if docs:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Prepare formatted context with book information
                formatted_chunks = []
                
                for i, doc in enumerate(docs):
                    # Get the book ID from the document metadata
                    try:
                        book_id = doc.metadata.get("book_id")
                        
                        # Look up the book title and author
                        if book_id:
                            cursor.execute('''
                                SELECT title, author 
                                FROM books 
                                WHERE id = ?
                            ''', (book_id,))
                            
                            book_info = cursor.fetchone()
                            
                            if book_info:
                                title, author = book_info
                                formatted_chunks.append(
                                    f"--- EXCERPT {i+1} (from '{title}' by {author}) ---\n"
                                    f"{doc.page_content}\n"
                                )
                            else:
                                # Fallback if book info not found
                                formatted_chunks.append(
                                    f"--- EXCERPT {i+1} ---\n"
                                    f"{doc.page_content}\n"
                                )
                        else:
                            # No book_id in metadata
                            formatted_chunks.append(
                                f"--- EXCERPT {i+1} ---\n"
                                f"{doc.page_content}\n"
                            )
                    except Exception as e:
                        print(f"Error formatting context chunk: {e}")
                        # Add the raw chunk if there's an error
                        formatted_chunks.append(doc.page_content)
                
                conn.close()
                return "\n\n".join(formatted_chunks)
            else:
                return "No relevant information found in the knowledge base."
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return f"Error retrieving context from knowledge base: {str(e)}"
