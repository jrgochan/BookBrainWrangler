"""
Analytics module for Book Knowledge AI.
Provides analytics for knowledge base content.
"""

import re
import string
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple, Set

from utils.logger import get_logger
from knowledge_base.config import (
    DEFAULT_KEYWORD_MIN_COUNT, DEFAULT_KEYWORD_MAX_WORDS,
    DEFAULT_STOPWORDS_LANGUAGE
)

# Get a logger for this module
logger = get_logger(__name__)

# Common English stopwords
STOPWORDS = {
    "english": set([
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
        "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", 
        "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", 
        "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", 
        "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
        "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", 
        "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", 
        "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", 
        "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", 
        "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", 
        "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", 
        "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", 
        "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", 
        "your", "yours", "yourself", "yourselves"
    ])
}

def extract_keywords(
    text: str,
    min_count: int = DEFAULT_KEYWORD_MIN_COUNT,
    max_words: int = DEFAULT_KEYWORD_MAX_WORDS,
    language: str = DEFAULT_STOPWORDS_LANGUAGE,
    custom_stopwords: Optional[Set[str]] = None
) -> Dict[str, int]:
    """
    Extract keywords from text.
    
    Args:
        text: Text to analyze
        min_count: Minimum count for a keyword to be included
        max_words: Maximum words in a keyword phrase
        language: Language of stopwords to use
        custom_stopwords: Additional stopwords to exclude
        
    Returns:
        Dictionary of keywords and their counts
    """
    if not text:
        return {}
    
    # Get stopwords for the specified language
    stopwords = STOPWORDS.get(language.lower(), set())
    
    # Add custom stopwords if provided
    if custom_stopwords:
        stopwords.update(custom_stopwords)
    
    # Clean and normalize text
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
    text = re.sub(r'\s+', ' ', text)      # Replace multiple spaces with a single space
    
    # Split into words
    words = text.split()
    
    # Remove stopwords and short words
    words = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Count single words
    word_counts = Counter(words)
    
    # Extract multi-word phrases if max_words > 1
    phrase_counts = {}
    if max_words > 1:
        for n in range(2, min(max_words + 1, len(words))):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                if phrase not in phrase_counts:
                    phrase_counts[phrase] = 0
                phrase_counts[phrase] += 1
    
    # Combine single words and phrases
    all_counts = {**word_counts, **phrase_counts}
    
    # Filter by minimum count
    keywords = {k: v for k, v in all_counts.items() if v >= min_count}
    
    return keywords

def get_word_frequencies(
    text: str,
    language: str = DEFAULT_STOPWORDS_LANGUAGE,
    custom_stopwords: Optional[Set[str]] = None,
    min_length: int = 3
) -> Dict[str, int]:
    """
    Get word frequencies from text.
    
    Args:
        text: Text to analyze
        language: Language of stopwords to use
        custom_stopwords: Additional stopwords to exclude
        min_length: Minimum word length to include
        
    Returns:
        Dictionary of words and their frequencies
    """
    if not text:
        return {}
    
    # Get stopwords for the specified language
    stopwords = STOPWORDS.get(language.lower(), set())
    
    # Add custom stopwords if provided
    if custom_stopwords:
        stopwords.update(custom_stopwords)
    
    # Clean and normalize text
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
    text = re.sub(r'\s+', ' ', text)      # Replace multiple spaces with a single space
    
    # Split into words
    words = text.split()
    
    # Remove stopwords and short words
    words = [word for word in words if word not in stopwords and len(word) >= min_length]
    
    # Count words
    word_counts = Counter(words)
    
    return dict(word_counts)

def compute_document_statistics(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute statistics for a document.
    
    Args:
        document: Document to analyze
        
    Returns:
        Dictionary of document statistics
    """
    stats = {}
    
    # Check if document has text
    if not document or "text" not in document:
        return stats
    
    text = document["text"]
    
    # Basic statistics
    stats["char_count"] = len(text)
    stats["word_count"] = len(text.split())
    stats["line_count"] = text.count("\n") + 1
    stats["paragraph_count"] = text.count("\n\n") + 1
    
    # Word frequencies
    word_frequencies = get_word_frequencies(text)
    stats["word_frequencies"] = word_frequencies
    
    # Keywords
    keywords = extract_keywords(text)
    stats["keywords"] = keywords
    
    # Most common words
    most_common = dict(Counter(word_frequencies).most_common(20))
    stats["most_common_words"] = most_common
    
    return stats