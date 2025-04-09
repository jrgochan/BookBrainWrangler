"""
Text processing utilities for document content.
"""

import re
import string
from typing import List, Dict, Any, Optional, Set, Tuple

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def ensure_nltk_resources():
    """
    Ensure that necessary NLTK resources are downloaded.
    This function is called when NLTK functionality is needed.
    """
    try:
        import nltk
        
        # List of resources to check and download if needed
        resources = [
            ('punkt', 'tokenizers/punkt'),
            ('stopwords', 'corpora/stopwords')
        ]
        
        # Check and download each resource
        for resource_name, resource_path in resources:
            try:
                nltk.data.find(resource_path)
                logger.debug(f"NLTK resource '{resource_name}' already available")
            except LookupError:
                logger.info(f"Downloading NLTK resource: {resource_name}")
                nltk.download(resource_name, quiet=True)
                
        logger.info("NLTK resources check completed")
        return True
    
    except Exception as e:
        logger.error(f"Error ensuring NLTK resources: {str(e)}")
        raise

def cleanup_text(text: str) -> str:
    """
    Clean up text by normalizing whitespace and removing control characters.
    
    Args:
        text: The text to clean up
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with a single space
    clean_text = re.sub(r'\s+', ' ', text)
    
    # Replace common Unicode whitespace chars with standard space
    clean_text = clean_text.replace('\xa0', ' ')
    clean_text = clean_text.replace('\u2002', ' ')
    clean_text = clean_text.replace('\u2003', ' ')
    
    # Remove control characters (except newlines and tabs)
    clean_text = ''.join(ch for ch in clean_text if ch == '\n' or ch == '\t' or ch >= ' ')
    
    # Fix common OCR errors
    clean_text = clean_text.replace('|', 'I')  # Pipe character often mistaken for letter I
    
    return clean_text.strip()

def extract_keywords(text: str, min_length: int = 3, max_length: int = 25,
                    stop_words: Optional[Set[str]] = None) -> List[str]:
    """
    Extract potential keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum length of keywords
        max_length: Maximum length of keywords
        stop_words: Set of stop words to exclude
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # Default set of english stop words
    default_stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
        'when', 'where', 'how', 'which', 'who', 'whom', 'then', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'does', 'did', 'do',
        'doing', 'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'all', 'any', 'both', 'each',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should',
        'now', 'with', 'for', 'this', 'that'
    }
    
    # Use provided stop words or default set
    stop_words = stop_words or default_stop_words
    
    # Clean text
    clean_text = cleanup_text(text)
    
    # Split into words
    words = re.findall(r'\b[A-Za-z][\w-]*[A-Za-z0-9]\b', clean_text)
    
    # Filter words
    filtered_words = []
    for word in words:
        # Skip short words
        if len(word) < min_length:
            continue
            
        # Skip long words
        if len(word) > max_length:
            continue
            
        # Skip stop words
        if word.lower() in stop_words:
            continue
            
        filtered_words.append(word)
    
    return filtered_words

def count_word_frequency(text: str, min_length: int = 3, 
                         stop_words: Optional[Set[str]] = None) -> Dict[str, int]:
    """
    Count word frequency in text.
    
    Args:
        text: Text to analyze
        min_length: Minimum length of words to count
        stop_words: Set of stop words to exclude
        
    Returns:
        Dictionary mapping words to their frequency
    """
    if not text:
        return {}
    
    # Extract words
    words = extract_keywords(text, min_length=min_length, stop_words=stop_words)
    
    # Count frequency
    frequency = {}
    for word in words:
        word_lower = word.lower()
        if word_lower in frequency:
            frequency[word_lower] += 1
        else:
            frequency[word_lower] = 1
    
    return frequency

def calculate_text_density(text: str) -> float:
    """
    Calculate text density - the ratio of alphanumeric characters to total characters.
    A higher number indicates more textual content vs. whitespace/punctuation.
    
    Args:
        text: Text to analyze
        
    Returns:
        Text density as a float between 0 and 1
    """
    if not text:
        return 0
    
    # Count alphanumeric characters
    alpha_count = sum(c.isalnum() for c in text)
    
    # Total length
    total_length = len(text)
    
    # Calculate density
    if total_length > 0:
        return alpha_count / total_length
    else:
        return 0

def extract_sentences(text: str, min_length: int = 10, max_length: int = 500) -> List[str]:
    """
    Extract sentences from text.
    
    Args:
        text: Text to extract sentences from
        min_length: Minimum length of sentences to include
        max_length: Maximum length of sentences to include
        
    Returns:
        List of extracted sentences
    """
    if not text:
        return []
    
    # Clean text
    clean_text = cleanup_text(text)
    
    # Split into sentences using regex
    # This handles common sentence endings (., !, ?) followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean_text)
    
    # Filter sentences
    filtered_sentences = []
    for sentence in sentences:
        # Skip short sentences
        if len(sentence) < min_length:
            continue
            
        # Truncate or skip long sentences
        if len(sentence) > max_length:
            # Either truncate
            # sentence = sentence[:max_length] + "..."
            # Or skip
            continue
            
        filtered_sentences.append(sentence.strip())
    
    return filtered_sentences

def analyze_word_frequency(text: str, min_word_length: int = 3, 
                          max_words: int = 100,
                          stop_words: Optional[Set[str]] = None,
                          exclude_stopwords: bool = True,
                          custom_stopwords: Optional[List[str]] = None) -> List[Tuple[str, int]]:
    """
    Analyze word frequency in text and return most common words.
    
    Args:
        text: Text to analyze
        min_word_length: Minimum length of words to count
        max_words: Maximum number of words to return
        stop_words: Set of stop words to exclude
        exclude_stopwords: Whether to exclude common stop words
        custom_stopwords: Additional custom stopwords to exclude
        
    Returns:
        List of (word, frequency) tuples, sorted by frequency (descending)
    """
    # Build stop words set
    if exclude_stopwords:
        try:
            # Try to use NLTK's comprehensive stopwords
            ensure_nltk_resources()
            from nltk.corpus import stopwords
            nltk_stopwords = set(stopwords.words('english'))
            
            # If custom stopwords are provided, add them
            if custom_stopwords:
                for word in custom_stopwords:
                    nltk_stopwords.add(word.lower())
                    
            stop_words = nltk_stopwords
            logger.debug(f"Using NLTK stopwords (total: {len(stop_words)})")
            
        except Exception as e:
            logger.warning(f"Could not use NLTK stopwords, falling back to basic set: {str(e)}")
            # Fallback to basic stop words if NLTK is not available
            if stop_words is None:
                stop_words = set([
                    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                    'when', 'where', 'how', 'which', 'who', 'whom', 'then', 'is', 'are', 'was',
                    'were', 'be', 'been', 'being', 'have', 'has', 'had', 'does', 'did', 'do',
                    'doing', 'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again'
                ])
                
                # Add custom stopwords if provided
                if custom_stopwords:
                    for word in custom_stopwords:
                        stop_words.add(word.lower())
    elif custom_stopwords:
        # If we're not excluding default stopwords but have custom ones
        stop_words = set(word.lower() for word in custom_stopwords)
    
    # Get word frequency
    freq_dict = count_word_frequency(text, min_length=min_word_length, stop_words=stop_words)
    
    # Convert to list of tuples and sort by frequency (descending)
    freq_list = [(word, freq) for word, freq in freq_dict.items()]
    freq_list.sort(key=lambda x: x[1], reverse=True)
    
    # Limit to max_words
    return freq_list[:max_words]

def chunk_large_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """
    Split very large text into manageable chunks for processing.
    
    Args:
        text: The large text to chunk
        max_chunk_size: Maximum size per chunk
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
        
    chunks = []
    
    # Try to split at paragraph boundaries
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            # If the current chunk has content, add it to chunks
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Start a new chunk
            current_chunk = para + "\n\n"
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If any chunk is still too large, use a more aggressive splitting
    result = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            result.append(chunk)
        else:
            # Split at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_chunk_size:
                    current_chunk += sentence + " "
                else:
                    # Add the current chunk if it has content
                    if current_chunk:
                        result.append(current_chunk.strip())
                    
                    # If a single sentence is too long, split it by words
                    if len(sentence) > max_chunk_size:
                        words = sentence.split()
                        current_chunk = ""
                        
                        for word in words:
                            if len(current_chunk) + len(word) <= max_chunk_size:
                                current_chunk += word + " "
                            else:
                                result.append(current_chunk.strip())
                                current_chunk = word + " "
                    else:
                        current_chunk = sentence + " "
            
            # Add the last part if it has content
            if current_chunk:
                result.append(current_chunk.strip())
    
    return result