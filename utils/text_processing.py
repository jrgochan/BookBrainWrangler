"""
Text processing utilities for word frequency analysis and cleaning.
"""

import re
import string
import json
import collections
from typing import List, Dict, Tuple, Any, Optional

# NLP libraries for text processing
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

def cleanup_text(text: str) -> str:
    """
    Clean up text by removing extra whitespace, normalizing line breaks, etc.
    
    Args:
        text: Input text string
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Convert to string if not already
    if not isinstance(text, str):
        try:
            text = str(text)
        except:
            return ""
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize line breaks
    text = re.sub(r'[\r\n]+', '\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def analyze_word_frequency(
    text: str, 
    min_word_length: int = 3, 
    max_words: int = 200,
    exclude_stopwords: bool = True,
    custom_stopwords: List[str] = None
) -> List[Tuple[str, int]]:
    """
    Analyze word frequency in a text.
    
    Args:
        text: Text to analyze
        min_word_length: Minimum word length to include
        max_words: Maximum number of words to return
        exclude_stopwords: Whether to exclude common stopwords
        custom_stopwords: Optional list of additional stopwords to exclude
        
    Returns:
        List of (word, frequency) tuples sorted by frequency
    """
    if not text:
        return []
    
    # Tokenize the text
    tokens = word_tokenize(text.lower())
    
    # Remove punctuation
    tokens = [word for word in tokens if word not in string.punctuation]
    
    # Remove short words
    tokens = [word for word in tokens if len(word) >= min_word_length]
    
    # Remove stopwords if requested
    if exclude_stopwords:
        # Get English stopwords
        stop_words = set(stopwords.words('english'))
        
        # Add custom stopwords if provided
        if custom_stopwords:
            stop_words.update(custom_stopwords)
        
        # Filter out stopwords
        tokens = [word for word in tokens if word not in stop_words]
    
    # Count word frequencies
    word_freq = collections.Counter(tokens)
    
    # Get the most common words
    most_common = word_freq.most_common(max_words)
    
    return most_common