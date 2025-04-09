"""
Embedding model implementation for the Knowledge Base.
Handles various embedding models and provides error handling.
"""

from langchain_community.embeddings import SentenceTransformerEmbeddings
from utils.logger import get_logger
import numpy as np

# Get logger
logger = get_logger(__name__)

class EmbeddingModel:
    """
    Encapsulates embedding model functionality with better error handling.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2", use_fallback=True, **kwargs):
        """
        Initialize an embedding model with fallback options.
        
        Args:
            model_name: Name of the primary embedding model to use
            use_fallback: Whether to try fallback models if the primary fails
            **kwargs: Additional keyword arguments to pass to the embedding model
        """
        self.model_name = model_name
        self.model_kwargs = kwargs
        self.use_fallback = use_fallback
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the embedding model with error handling and fallbacks."""
        try:
            # Primary approach: Use SentenceTransformerEmbeddings from langchain
            logger.info(f"Initializing SentenceTransformerEmbeddings with model: {self.model_name}")
            self.model = SentenceTransformerEmbeddings(model_name=self.model_name, **self.model_kwargs)
            logger.info("Successfully initialized SentenceTransformerEmbeddings model")
            return
        except Exception as primary_error:
            logger.warning(f"Error initializing primary embedding model: {primary_error}")
            
            if not self.use_fallback:
                logger.error("Fallback disabled, raising error")
                raise
            
            # First fallback: Try direct SentenceTransformer approach
            try:
                from sentence_transformers import SentenceTransformer
                
                class DirectSentenceTransformerEmbeddings:
                    def __init__(self, model_name):
                        self.model = SentenceTransformer(model_name)
                        self.model_name = model_name
                        
                    def embed_documents(self, texts):
                        return self.model.encode(texts, convert_to_numpy=True)
                        
                    def embed_query(self, text):
                        return self.model.encode(text, convert_to_numpy=True)
                
                logger.info("Attempting fallback to direct SentenceTransformer")
                self.model = DirectSentenceTransformerEmbeddings(self.model_name)
                logger.info("Successfully initialized direct SentenceTransformer model")
                return
            except Exception as st_error:
                logger.warning(f"Error initializing direct SentenceTransformer: {st_error}")
                
                # Second fallback: FakeEmbeddings for development/testing
                try:
                    from langchain_community.embeddings.fake import FakeEmbeddings
                    
                    logger.info("Using FakeEmbeddings fallback for development/testing")
                    dimension = 384  # Same as all-MiniLM-L6-v2
                    self.model = FakeEmbeddings(size=dimension)
                    self.model_name = "fake-embeddings"
                    logger.warning("Using fake embeddings model - FOR TESTING ONLY!")
                    return
                except Exception as fake_error:
                    logger.warning(f"Error creating fake embeddings: {fake_error}")
                    
                    # Final fallback: Basic embedding implementation
                    try:
                        import nltk
                        from nltk.tokenize import word_tokenize
                        
                        # Ensure nltk data is available
                        nltk.download('punkt', quiet=True)
                        
                        # Create a very basic embedding approach
                        class BasicEmbeddings:
                            def __init__(self, dimension=384):
                                self.dimension = dimension
                                self.model_name = "basic-embeddings"
                                
                            def embed_documents(self, texts):
                                results = []
                                for text in texts:
                                    # Create a simple embedding by hashing words
                                    tokens = word_tokenize(text.lower())
                                    embedding = np.zeros(self.dimension)
                                    
                                    for i, token in enumerate(tokens):
                                        # Use a simple hashing technique to generate values
                                        hash_val = hash(token) % 1000000
                                        idx = hash_val % self.dimension
                                        val = (hash_val / 1000000) * 2 - 1  # Value between -1 and 1
                                        embedding[idx] = val
                                    
                                    # Normalize
                                    norm = np.linalg.norm(embedding)
                                    if norm > 0:
                                        embedding = embedding / norm
                                    
                                    results.append(embedding)
                                return results
                                
                            def embed_query(self, text):
                                return self.embed_documents([text])[0]
                        
                        logger.warning("Using BasicEmbeddings fallback - NOT RECOMMENDED FOR PRODUCTION")
                        self.model = BasicEmbeddings(dimension=384)
                        self.model_name = "basic-embeddings"
                        return
                    
                    except Exception as basic_error:
                        logger.error(f"Error creating basic embeddings: {basic_error}")
                        raise RuntimeError("All embedding model initialization attempts failed")
    
    def embed_documents(self, texts):
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embeddings as numpy arrays
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        return self.model.embed_documents(texts)
    
    def embed_query(self, text):
        """
        Generate an embedding for a single query text.
        
        Args:
            text: String to embed
            
        Returns:
            Embedding as a numpy array
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        return self.model.embed_query(text)
