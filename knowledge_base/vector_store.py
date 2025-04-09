"""
Vector store module for the Knowledge Base.
Handles interactions with FAISS for vector storage and retrieval.
"""

import os
import shutil
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from langchain_community.vectorstores import FAISS
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)

class VectorStore:
    """
    Handles vector storage and retrieval operations with FAISS.
    """
    def __init__(self, embedding_function, 
                 persist_directory=None, 
                 collection_name="book_knowledge_base",
                 distance_function="cosine"):
        """
        Initialize the vector store.
        
        Args:
            embedding_function: The embedding function to use
            persist_directory: Directory to persist the database (None for in-memory)
            collection_name: Name of the collection to use
            distance_function: Distance function for similarity search (cosine, l2, ip)
        """
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.distance_function = distance_function
        
        # Map distance function string to FAISS metric type
        self.metric_mapping = {
            "cosine": "cosine",  # Will be normalized before comparison
            "l2": "l2",          # Euclidean distance
            "ip": "inner_product", # Inner product (dot product)
        }
        
        # Validate distance function
        if self.distance_function not in self.metric_mapping:
            logger.warning(f"Unknown distance function: {self.distance_function}, defaulting to cosine")
            self.distance_function = "cosine"
        
        # Store metadata and index mapping separately since FAISS doesn't store metadata
        self.document_metadatas = {}  # id -> metadata
        self.document_contents = {}   # id -> text content
        
        # Initialize the vector store
        self._initialize_vector_store()
        
    def _get_writable_directory(self, base_dir="knowledge_base_data"):
        """
        Get a writable directory for the vector store data.
        
        Args:
            base_dir: Base directory name
            
        Returns:
            Path to the writable directory
        """
        # If a persist directory is already set, use that
        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            return self.persist_directory
        
        # Otherwise, create a default directory
        kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", base_dir)
        os.makedirs(kb_dir, exist_ok=True)
        
        # Create the faiss directory
        faiss_dir = os.path.join(kb_dir, "faiss_db")
        os.makedirs(faiss_dir, exist_ok=True)
        
        return faiss_dir
        
    def _initialize_vector_store(self):
        """Initialize the vector store with FAISS."""
        try:
            # Get a writable directory
            if self.persist_directory is None:
                self.persist_directory = self._get_writable_directory()
                
            logger.info(f"Initializing vector store at {self.persist_directory}")
            
            # Path to the FAISS index file and metadata
            index_path = os.path.join(self.persist_directory, f"{self.collection_name}.faiss")
            metadata_path = os.path.join(self.persist_directory, f"{self.collection_name}.pkl")
            
            # Check if a FAISS index already exists
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                logger.info(f"Loading existing FAISS index from {index_path}")
                
                # Load the index
                self.vector_store = FAISS.load_local(
                    folder_path=self.persist_directory,
                    index_name=self.collection_name,
                    embeddings=self.embedding_function
                )
                
                # Load our custom metadata
                with open(os.path.join(self.persist_directory, f"{self.collection_name}_meta.pkl"), 'rb') as file:
                    metadata_obj = pickle.load(file)
                    self.document_metadatas = metadata_obj.get('metadatas', {})
                    self.document_contents = metadata_obj.get('contents', {})
            else:
                logger.info(f"Creating new FAISS index at {self.persist_directory}")
                
                # Create a new empty FAISS index with specified distance function
                self.vector_store = FAISS.from_documents(
                    documents=[],  # Empty initially
                    embedding=self.embedding_function,
                    distance_strategy=self.metric_mapping[self.distance_function]
                )
                
                # Save the empty index
                self.vector_store.save_local(
                    folder_path=self.persist_directory,
                    index_name=self.collection_name
                )
                
                # Initialize and save our custom metadata
                self._save_metadata()
            
            logger.info(f"Vector store initialized with collection '{self.collection_name}'")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def _save_metadata(self):
        """Save document metadata to disk."""
        try:
            metadata_obj = {
                'metadatas': self.document_metadatas,
                'contents': self.document_contents
            }
            
            metadata_path = os.path.join(self.persist_directory, f"{self.collection_name}_meta.pkl")
            with open(metadata_path, 'wb') as file:
                pickle.dump(metadata_obj, file)
                
            logger.debug(f"Saved metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise
    
    def add_texts(self, texts, metadatas=None, ids=None):
        """
        Add texts to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: List of metadata dictionaries
            ids: List of IDs for the texts
            
        Returns:
            List of IDs of the added texts
        """
        try:
            if not texts:
                logger.warning("No texts provided to add_texts")
                return []
                
            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            # Use empty metadata if not provided
            if metadatas is None:
                metadatas = [{} for _ in range(len(texts))]
            
            # Create langchain document objects
            from langchain_core.documents import Document
            documents = [
                Document(page_content=text, metadata=metadata)
                for text, metadata in zip(texts, metadatas)
            ]
            
            # Add documents to the FAISS index
            self.vector_store.add_documents(documents)
            
            # Store metadata and contents in our dictionaries
            for doc_id, metadata, text in zip(ids, metadatas, texts):
                self.document_metadatas[doc_id] = metadata
                self.document_contents[doc_id] = text
            
            # Save the index and metadata
            self.vector_store.save_local(
                folder_path=self.persist_directory,
                index_name=self.collection_name
            )
            self._save_metadata()
            
            count = len(texts)
            logger.info(f"Added {count} documents to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {str(e)}")
            raise
    
    def similarity_search(self, query, k=5, filter=None):
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of documents
        """
        try:
            # Perform the similarity search with FAISS
            if filter:
                # FAISS doesn't have built-in filtering, so we'll need to post-filter results
                # First, we get more results than needed
                docs = self.vector_store.similarity_search(
                    query=query,
                    k=min(k * 3, 100)  # Get more results for filtering
                )
                
                # Then filter based on metadata
                filtered_docs = []
                for doc in docs:
                    if self._matches_filter(doc.metadata, filter):
                        filtered_docs.append(doc)
                        if len(filtered_docs) >= k:
                            break
                            
                docs = filtered_docs[:k]
            else:
                # No filter, use standard search
                docs = self.vector_store.similarity_search(
                    query=query,
                    k=k
                )
            
            logger.info(f"Retrieved {len(docs)} documents for query: {query[:50]}...")
            return docs
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
    
    def similarity_search_with_relevance_scores(self, query, k=5, filter=None):
        """
        Search for similar documents with relevance scores.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Use score_threshold=0 to get all results with scores
            if filter:
                # Need to implement manual filtering
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=min(k * 3, 100)  # Get more results for filtering
                )
                
                # Filter results
                filtered_results = []
                for doc, score in results:
                    if self._matches_filter(doc.metadata, filter):
                        # Convert distance score to similarity score (invert)
                        # FAISS returns L2 distance by default, so smaller is better
                        similarity = 1.0 / (1.0 + score)
                        filtered_results.append((doc, similarity))
                        if len(filtered_results) >= k:
                            break
                            
                results = filtered_results[:k]
            else:
                # No filter
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k
                )
                
                # Convert FAISS distance scores to similarity scores
                results = [(doc, 1.0 / (1.0 + score)) for doc, score in results]
            
            logger.info(f"Retrieved {len(results)} scored documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store with scores: {str(e)}")
            raise
    
    def _matches_filter(self, metadata, filter_dict):
        """Check if document metadata matches the filter criteria."""
        if not filter_dict:
            return True
            
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
                
        return True
    
    def delete(self, filter=None, ids=None):
        """
        Delete documents from the vector store.
        
        Args:
            filter: Dictionary of metadata field/value pairs to filter by
            ids: List of IDs to delete
            
        Returns:
            Success status
        """
        try:
            deleted_count = 0
            
            if ids:
                logger.info(f"Deleting {len(ids)} documents by ID from vector store")
                # FAISS doesn't support direct deletion by IDs, so we need to rebuild the index
                # First, get all document IDs that we want to keep
                keep_ids = [id for id in self.document_metadatas.keys() if id not in ids]
                
                # Rebuild the index with only the documents we want to keep
                self._rebuild_index_with_ids(keep_ids)
                deleted_count = len(ids)
                
            elif filter:
                logger.info(f"Deleting documents with filter {filter} from vector store")
                # Find document IDs that match the filter
                delete_ids = []
                for doc_id, metadata in self.document_metadatas.items():
                    if self._matches_filter(metadata, filter):
                        delete_ids.append(doc_id)
                
                # Remove these documents by rebuilding the index
                if delete_ids:
                    keep_ids = [id for id in self.document_metadatas.keys() if id not in delete_ids]
                    self._rebuild_index_with_ids(keep_ids)
                    deleted_count = len(delete_ids)
            else:
                logger.warning("No filter or IDs provided for deletion")
                return False
                
            logger.info(f"Deleted {deleted_count} documents from vector store")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting from vector store: {str(e)}")
            raise
    
    def _rebuild_index_with_ids(self, keep_ids):
        """Rebuild the index keeping only the specified IDs."""
        try:
            # Extract texts and metadatas for documents to keep
            texts = [self.document_contents[id] for id in keep_ids if id in self.document_contents]
            metadatas = [self.document_metadatas[id] for id in keep_ids if id in self.document_metadatas]
            
            # Create a new empty FAISS index with specified distance function
            new_index = FAISS.from_documents(
                documents=[],  # Empty initially
                embedding=self.embedding_function,
                distance_strategy=self.metric_mapping[self.distance_function]
            )
            
            # Add documents to keep
            if texts:
                from langchain_core.documents import Document
                documents = [
                    Document(page_content=text, metadata=metadata)
                    for text, metadata in zip(texts, metadatas)
                ]
                new_index.add_documents(documents)
            
            # Update our vector store
            self.vector_store = new_index
            
            # Update metadata dictionaries
            new_metadatas = {}
            new_contents = {}
            for id in keep_ids:
                if id in self.document_metadatas:
                    new_metadatas[id] = self.document_metadatas[id]
                if id in self.document_contents:
                    new_contents[id] = self.document_contents[id]
                    
            self.document_metadatas = new_metadatas
            self.document_contents = new_contents
            
            # Save the updated index and metadata
            self.vector_store.save_local(
                folder_path=self.persist_directory,
                index_name=self.collection_name
            )
            self._save_metadata()
            
            logger.info(f"Rebuilt index with {len(keep_ids)} documents")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            raise
    
    def clear(self):
        """
        Clear all documents from the vector store.
        
        Returns:
            Success status
        """
        try:
            # Count number of documents first
            doc_count = len(self.document_metadatas)
            
            # Create a new empty FAISS index
            self.vector_store = FAISS.from_documents(
                documents=[],  # Empty initially
                embedding=self.embedding_function,
                distance_strategy=self.metric_mapping[self.distance_function]
            )
            
            # Clear document metadata and content
            self.document_metadatas = {}
            self.document_contents = {}
            
            # Save the empty index and metadata
            self.vector_store.save_local(
                folder_path=self.persist_directory,
                index_name=self.collection_name
            )
            self._save_metadata()
            
            logger.info(f"Cleared {doc_count} documents from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            # Attempt to recreate the vector store if clearing fails
            try:
                logger.info("Attempting to recreate the vector store as fallback")
                
                # Try deleting the existing files
                index_path = os.path.join(self.persist_directory, f"{self.collection_name}.faiss")
                metadata_path = os.path.join(self.persist_directory, f"{self.collection_name}.pkl")
                custom_metadata_path = os.path.join(self.persist_directory, f"{self.collection_name}_meta.pkl")
                
                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                if os.path.exists(custom_metadata_path):
                    os.remove(custom_metadata_path)
                
                # Create a fresh empty index
                self.vector_store = FAISS.from_documents(
                    documents=[],  # Empty initially
                    embedding=self.embedding_function,
                    distance_strategy=self.metric_mapping[self.distance_function]
                )
                
                # Reset metadata
                self.document_metadatas = {}
                self.document_contents = {}
                
                # Save the empty index and metadata
                self.vector_store.save_local(
                    folder_path=self.persist_directory,
                    index_name=self.collection_name
                )
                self._save_metadata()
                
                logger.info("Successfully recreated vector store")
                return True
                
            except Exception as recreation_error:
                logger.error(f"Failed to recreate vector store: {str(recreation_error)}")
                raise
            
    def count(self):
        """
        Get the number of documents in the vector store.
        
        Returns:
            Document count
        """
        try:
            count = len(self.document_metadatas)
            logger.debug(f"Vector store contains {count} documents")
            return count
            
        except Exception as e:
            logger.error(f"Error counting documents in vector store: {str(e)}")
            raise
            
    def get_stats(self):
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary of statistics
        """
        try:
            count = len(self.document_metadatas)
            
            # Extract content types from collection if available
            content_types = set()
            for metadata in self.document_metadatas.values():
                if metadata and 'content_type' in metadata:
                    content_types.add(metadata['content_type'])
            
            # Default types if none found
            if not content_types:
                content_types = set(['text', 'image_caption'])
            
            stats = {
                'document_count': count,
                'document_types': list(content_types),
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory,
            }
            
            logger.debug(f"Retrieved vector store stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            raise
