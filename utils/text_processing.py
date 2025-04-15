"""
Text processing utilities for Book Knowledge AI.
Provides functions for working with text content.
"""

import re
import string
import unicodedata
from typing import Dict, List, Set, Tuple, Union, Optional, Any
from collections import Counter

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def cleanup_text(text: str) -> str:
    """
    Alias for clean_text function for backward compatibility.
    Cleans text by removing extra whitespace and normalizing unicode.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    return clean_text(text)

def analyze_word_frequency(text: str, min_length: int = 3, max_words: int = 20, 
                          exclude_stopwords: bool = True, custom_stopwords: List[str] = None) -> List[Tuple[str, int]]:
    """
    Analyze the frequency of words in a text.
    
    Args:
        text: The text to analyze
        min_length: Minimum word length to include in analysis
        max_words: Maximum number of words to return
        exclude_stopwords: Whether to exclude common stopwords
        custom_stopwords: Optional list of additional words to exclude
        
    Returns:
        List of (word, frequency) tuples, sorted by frequency (descending)
    """
    # Get word frequencies
    frequencies = calculate_word_frequencies(
        text=text,
        remove_stopwords_flag=exclude_stopwords,
        min_word_length=min_length,
        max_words=None  # We'll limit later
    )
    
    # Remove custom stopwords if provided
    if custom_stopwords:
        for word in custom_stopwords:
            if word in frequencies:
                del frequencies[word]
    
    # Sort by frequency (descending)
    sorted_frequencies = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    
    # Limit to max_words
    return sorted_frequencies[:max_words]

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing unicode.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Simple sentence splitter (handles common cases)
    # For more advanced splitting, consider using nltk.sent_tokenize
    text = text.replace('!', '.').replace('?', '.')
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    return sentences

def extract_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.
    
    Args:
        text: Input text
        
    Returns:
        List of paragraphs
    """
    if not text:
        return []
    
    # Split on double newlines (common paragraph delimiter)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
    return paragraphs

def tokenize(text: str) -> List[str]:
    """
    Split text into tokens (words).
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace punctuation with spaces
    for punct in string.punctuation:
        text = text.replace(punct, ' ')
    
    # Split on whitespace and filter out empty tokens
    tokens = [token.strip() for token in text.split() if token.strip()]
    
    return tokens

def remove_stopwords(tokens: List[str], stopwords: Optional[Set[str]] = None) -> List[str]:
    """
    Remove stopwords from a list of tokens.
    
    Args:
        tokens: List of tokens
        stopwords: Set of stopwords to remove (uses a basic set if None)
        
    Returns:
        List of tokens with stopwords removed
    """
    if not tokens:
        return []
    
    # Basic English stopwords if none provided
    if stopwords is None:
        stopwords = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'while', 'of', 'to', 'in', 'for', 'on', 'by', 'about', 'like', 'with',
            'from', 'at', 'this', 'that', 'these', 'those', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
        }
    
    # Filter out stopwords
    filtered_tokens = [token for token in tokens if token not in stopwords]
    
    return filtered_tokens

def calculate_word_frequencies(text: str, 
                             remove_stopwords_flag: bool = True, 
                             min_word_length: int = 2,
                             max_words: Optional[int] = None) -> Dict[str, int]:
    """
    Calculate word frequencies in a text.
    
    Args:
        text: Input text
        remove_stopwords_flag: Whether to remove stopwords
        min_word_length: Minimum word length to include
        max_words: Maximum number of words to include
        
    Returns:
        Dictionary mapping words to their frequencies
    """
    if not text:
        return {}
    
    # Tokenize the text
    tokens = tokenize(text)
    
    # Remove short words
    tokens = [token for token in tokens if len(token) >= min_word_length]
    
    # Remove stopwords if requested
    if remove_stopwords_flag:
        tokens = remove_stopwords(tokens)
    
    # Calculate frequencies
    frequencies = Counter(tokens)
    
    # Limit to top N words if specified
    if max_words and max_words > 0:
        frequencies = dict(frequencies.most_common(max_words))
    
    return frequencies

def extract_keywords(text: str, 
                   num_keywords: int = 10, 
                   min_word_length: int = 3,
                   remove_stopwords_flag: bool = True) -> List[str]:
    """
    Extract keywords from text based on frequency.
    
    Args:
        text: Input text
        num_keywords: Number of keywords to extract
        min_word_length: Minimum word length to include
        remove_stopwords_flag: Whether to remove stopwords
        
    Returns:
        List of keyword strings
    """
    if not text:
        return []
    
    # Calculate word frequencies
    frequencies = calculate_word_frequencies(
        text,
        remove_stopwords_flag=remove_stopwords_flag,
        min_word_length=min_word_length
    )
    
    # Get the top N keywords
    keywords = [word for word, _ in sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:num_keywords]]
    
    return keywords

def chunk_text(text: str, 
             chunk_size: int = 1000, 
             chunk_overlap: int = 200,
             split_by_paragraph: bool = True) -> List[str]:
    """
    Split text into overlapping chunks for processing.
    
    Args:
        text: Input text
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        split_by_paragraph: Whether to try to split at paragraph boundaries
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    
    if split_by_paragraph:
        # Split by paragraphs first
        paragraphs = extract_paragraphs(text)
        
        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the chunk size, store the current chunk and start a new one
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start a new chunk with overlap from the previous chunk
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + "\n\n" + paragraph
            else:
                # Add the paragraph to the current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
    else:
        # Simple character-based chunking
        start = 0
        while start < len(text):
            # Find the end of the chunk
            end = min(start + chunk_size, len(text))
            
            # Try to end at a sentence boundary if possible
            if end < len(text):
                # Look for sentence boundaries within the last 20% of the chunk
                last_period = text.rfind('.', start + int(chunk_size * 0.8), end)
                if last_period != -1:
                    end = last_period + 1  # Include the period
            
            # Add the chunk
            chunks.append(text[start:end].strip())
            
            # Move the start position for the next chunk, considering overlap
            start = end - chunk_overlap if end < len(text) else end
    
    return chunks

def find_matching_text(query: str, 
                     document: str, 
                     context_window: int = 100) -> List[Tuple[str, int]]:
    """
    Find occurrences of query in document with surrounding context.
    
    Args:
        query: Search query
        document: Document text to search in
        context_window: Number of characters to include around match
        
    Returns:
        List of tuples containing (context_text, position)
    """
    if not query or not document:
        return []
    
    # Prepare query and document for case-insensitive search
    query_lower = query.lower()
    document_lower = document.lower()
    
    matches = []
    
    # Find all occurrences of the query
    start_pos = 0
    while True:
        # Find the next occurrence
        pos = document_lower.find(query_lower, start_pos)
        if pos == -1:
            break
        
        # Calculate context boundaries
        context_start = max(0, pos - context_window)
        context_end = min(len(document), pos + len(query) + context_window)
        
        # Extract context
        context = document[context_start:context_end]
        
        # Add to matches
        matches.append((context, pos))
        
        # Move past this occurrence
        start_pos = pos + 1
    
    return matches

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate a simple similarity score between two texts.
    Based on Jaccard similarity of token sets.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize texts
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))
    
    # Remove stopwords
    tokens1 = remove_stopwords(list(tokens1))
    tokens2 = remove_stopwords(list(tokens2))
    
    # Convert back to sets
    tokens1 = set(tokens1)
    tokens2 = set(tokens2)
    
    # Calculate Jaccard similarity
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    return intersection / union if union > 0 else 0.0

def detect_language(text: str) -> str:
    """
    Detect the language of a text based on common words.
    This is a simple implementation and not as accurate as specialized libraries.
    
    Args:
        text: Text to analyze
        
    Returns:
        ISO language code (e.g., 'en', 'es', 'fr', etc.)
    """
    if not text or len(text.strip()) < 20:
        return 'unknown'
    
    # Simple language detection based on common words
    common_words = {
        'en': {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'that', 'on'},
        'es': {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'no', 'por'},
        'fr': {'le', 'la', 'de', 'et', 'est', 'en', 'un', 'que', 'qui', 'dans'},
        'de': {'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich'},
        'it': {'il', 'di', 'e', 'che', 'la', 'in', 'un', 'per', 'è', 'con'},
    }
    
    # Tokenize text
    tokens = set(tokenize(text))
    
    # Calculate scores for each language
    scores = {}
    for lang, words in common_words.items():
        # Count how many common words are in the text
        matches = tokens.intersection(words)
        scores[lang] = len(matches) / len(words) if words else 0
    
    # Return the language with the highest score, or 'unknown' if all scores are 0
    max_lang = max(scores.items(), key=lambda x: x[1])
    return max_lang[0] if max_lang[1] > 0.2 else 'unknown'