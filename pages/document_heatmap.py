"""
Document Heatmap - Visualize document insights and key information
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from PIL import Image
import io
import base64
from typing import Dict, List, Tuple, Any, Optional

# For text processing
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist

# Import project modules
from knowledge_base import KnowledgeBase
from book_manager.manager import BookManager
from utils.logger import get_logger
from utils.text_processing import clean_text

# Define functions that may not be imported properly
def extract_page_as_image(pdf_path, page_number):
    """
    Extract a specific page from a PDF as a PIL Image.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: Page number to extract (0-indexed)
        
    Returns:
        PIL Image object or None if extraction fails
    """
    try:
        from pdf2image import convert_from_path
        # Convert the specific page
        images = convert_from_path(
            pdf_path, 
            first_page=page_number + 1,  # pdf2image uses 1-indexed pages
            last_page=page_number + 1
        )
        
        if images and len(images) > 0:
            return images[0]
        return None
    except Exception as e:
        logger.error(f"Error extracting page {page_number} as image: {str(e)}")
        return None

def image_to_base64(image, format='PNG'):
    """
    Convert a PIL Image to a base64 encoded string.
    
    Args:
        image: PIL Image object
        format: Output image format (default: PNG)
        
    Returns:
        Base64 encoded string representation of the image
    """
    try:
        import io
        import base64
        # Save image to a bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        
        # Encode as base64
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/{format.lower()};base64,{img_str}"
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return ""

# Get logger
logger = get_logger(__name__)

# Download nltk data if needed
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Constants
SCORE_THRESHOLDS = {
    "high": 0.7,
    "medium": 0.4,
    "low": 0.0
}

HEATMAP_COLORS = {
    "high": "rgba(255, 0, 0, 0.7)",     # Red
    "medium": "rgba(255, 165, 0, 0.5)", # Orange
    "low": "rgba(255, 255, 0, 0.3)"     # Yellow
}

def render():
    """Render the document heatmap page."""
    st.title("Document Heatmap")
    st.write("Visualize key insights and important information in your documents")
    
    # Initialize components
    book_manager = BookManager()
    knowledge_base = KnowledgeBase()
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Heatmap Controls")
        
        # Book selection
        books = book_manager.get_all_books()
        if not books:
            st.warning("No books in your library. Add books in the Book Management page.")
            return
            
        book_options = {f"{book['title']} by {book['author']}": book['id'] for book in books}
        selected_book_title = st.selectbox("Select Document", options=list(book_options.keys()))
        selected_book_id = book_options[selected_book_title]
        
        # Heatmap type selection
        heatmap_type = st.radio(
            "Heatmap Type",
            ["Keyword Density", "Key Concepts", "Sentiment Analysis", "Information Density"]
        )
        
        # Threshold control
        threshold = st.slider("Highlight Threshold", 0.0, 1.0, 0.4, 0.05, 
                             help="Lower values show more highlights, higher values show only the most significant areas")
        
        # Keyword input for custom search
        if heatmap_type == "Keyword Density":
            custom_keywords = st.text_input("Custom Keywords (comma separated)",
                                          help="Add specific words to highlight in the document")
            
        # Settings for information density
        if heatmap_type == "Information Density":
            window_size = st.slider("Analysis Window Size", 3, 20, 10,
                                  help="Number of sentences to analyze together")
            overlap = st.slider("Window Overlap", 0, 5, 2,
                             help="Number of sentences to overlap between windows")
    
    # Get the book data
    book = book_manager.get_book(selected_book_id)
    if not book:
        st.error(f"Could not retrieve book with ID {selected_book_id}")
        return
    
    # Get book content
    content = book_manager.get_book_content(selected_book_id)
    if not content:
        st.error("Could not retrieve book content")
        return
    
    # Display book info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{book['title']}")
        st.caption(f"by {book['author']}")
        if book['categories']:
            st.caption(f"Categories: {', '.join(book['categories'])}")
    
    with col2:
        # Attempt to get a thumbnail if available
        if 'thumbnail_cache' in st.session_state and selected_book_id in st.session_state.thumbnail_cache:
            thumbnail = st.session_state.thumbnail_cache[selected_book_id]
            st.image(thumbnail, width=150)
    
    # Process based on heatmap type
    if heatmap_type == "Keyword Density":
        if 'custom_keywords' in locals() and custom_keywords:
            keywords = [k.strip() for k in custom_keywords.split(',')]
            st.write(f"Highlighting keywords: {', '.join(keywords)}")
        else:
            # Use top keywords from the document
            keywords = extract_top_keywords(content, 10)
            st.write("Highlighting top keywords (extracted automatically):")
            for kw, freq in keywords:
                st.write(f"- {kw} ({freq} occurrences)")
            keywords = [kw for kw, _ in keywords]
        
        # Create keyword heatmap
        create_keyword_heatmap(content, keywords, threshold)
        
    elif heatmap_type == "Key Concepts":
        # Extract concepts using knowledge base
        concepts = extract_key_concepts(content, knowledge_base)
        create_concept_heatmap(content, concepts, threshold)
        
    elif heatmap_type == "Sentiment Analysis":
        # Create sentiment heatmap
        create_sentiment_heatmap(content, threshold)
        
    elif heatmap_type == "Information Density":
        # Create information density heatmap
        window = window_size if 'window_size' in locals() else 10
        overlap_size = overlap if 'overlap' in locals() else 2
        create_information_density_heatmap(content, window, overlap_size, threshold)

def extract_top_keywords(text: str, limit: int = 10) -> List[Tuple[str, int]]:
    """
    Extract top keywords from text.
    
    Args:
        text: The text to analyze
        limit: Maximum number of keywords to return
        
    Returns:
        List of tuples (keyword, frequency)
    """
    # Tokenize text
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords and non-alphabetic tokens
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word.isalpha() and word not in stop_words and len(word) > 3]
    
    # Get frequency distribution
    fdist = FreqDist(filtered_tokens)
    
    # Return top keywords
    return fdist.most_common(limit)

def extract_key_concepts(text: str, knowledge_base: KnowledgeBase) -> List[Tuple[str, float]]:
    """
    Extract key concepts from text using vector database.
    
    Args:
        text: The text to analyze
        knowledge_base: KnowledgeBase instance
        
    Returns:
        List of tuples (concept, relevance_score)
    """
    # Split text into chunks
    sentences = sent_tokenize(text)
    chunks = []
    
    # Group sentences into chunks of ~200 words for analysis
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        words = len(sentence.split())
        if current_length + words > 200:
            # Save current chunk and start a new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = words
        else:
            current_chunk.append(sentence)
            current_length += words
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    # Extract concepts for each chunk
    concepts = []
    
    for chunk in chunks:
        # Use knowledge base search to find related concepts
        try:
            similar_chunks = knowledge_base.search(chunk, limit=3)
            
            # Extract key phrases from similar chunks
            for similar in similar_chunks:
                # Get the document title or snippet as concept
                concept = similar.get('document', {}).get('title', '')
                if not concept:
                    # Fall back to first 50 chars of content
                    content = similar.get('document', {}).get('content', '')
                    concept = content[:50] + '...' if len(content) > 50 else content
                
                # Add concept with score
                concepts.append((concept, similar.get('score', 0.0)))
        except Exception as e:
            logger.error(f"Error extracting concepts: {e}")
    
    # Deduplicate and sort concepts by score
    unique_concepts = {}
    for concept, score in concepts:
        if concept in unique_concepts:
            unique_concepts[concept] = max(unique_concepts[concept], score)
        else:
            unique_concepts[concept] = score
    
    # Sort by score
    sorted_concepts = sorted(unique_concepts.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_concepts[:10]  # Return top 10 concepts

def create_keyword_heatmap(text: str, keywords: List[str], threshold: float = 0.4):
    """
    Create a heatmap visualization of keyword density.
    
    Args:
        text: Document text
        keywords: List of keywords to highlight
        threshold: Minimum score to include in highlights
    """
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    
    # Calculate keyword density for each paragraph
    scores = []
    for para in paragraphs:
        para_lower = para.lower()
        
        # Count keyword occurrences
        keyword_count = sum(para_lower.count(kw.lower()) for kw in keywords)
        
        # Normalize by paragraph length
        word_count = len(para.split())
        if word_count > 0:
            density = min(1.0, keyword_count / (word_count * 0.1))  # Cap at 1.0
        else:
            density = 0.0
            
        scores.append(density)
    
    # Create visualization
    create_heatmap_visualization(paragraphs, scores, "Keyword Density", 
                               threshold, "Keyword density across document")

def create_concept_heatmap(text: str, concepts: List[Tuple[str, float]], threshold: float = 0.4):
    """
    Create a heatmap visualization of key concepts.
    
    Args:
        text: Document text
        concepts: List of (concept, score) tuples
        threshold: Minimum score to include in highlights
    """
    # Extract concept texts only
    concept_texts = [concept for concept, _ in concepts]
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    
    # Calculate concept relevance for each paragraph
    scores = []
    for para in paragraphs:
        para_lower = para.lower()
        
        # Check for concept mentions
        relevance = 0.0
        for concept, score in concepts:
            if concept.lower() in para_lower:
                relevance = max(relevance, score)
        
        scores.append(relevance)
    
    # Create visualization
    concept_list = ", ".join([c for c, _ in concepts[:5]])
    create_heatmap_visualization(paragraphs, scores, "Key Concepts", 
                               threshold, f"Top concepts: {concept_list}...")

def create_sentiment_heatmap(text: str, threshold: float = 0.4):
    """
    Create a heatmap visualization of sentiment.
    
    Args:
        text: Document text
        threshold: Minimum score to include in highlights
    """
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    
    # Simple sentiment analysis based on keyword matching
    # This is a placeholder for a more sophisticated sentiment analysis
    positive_words = ['good', 'great', 'excellent', 'positive', 'beautiful', 'happy', 
                     'love', 'best', 'wonderful', 'amazing', 'perfect', 'success']
    negative_words = ['bad', 'worst', 'terrible', 'negative', 'ugly', 'sad', 
                     'hate', 'poor', 'awful', 'horrible', 'failure', 'problem']
    
    scores = []
    for para in paragraphs:
        para_lower = para.lower()
        
        # Count positive and negative words
        pos_count = sum(para_lower.count(word) for word in positive_words)
        neg_count = sum(para_lower.count(word) for word in negative_words)
        
        total = pos_count + neg_count
        if total > 0:
            # Map to range [-1, 1] then to [0, 1]
            sentiment = (pos_count - neg_count) / total
            score = (sentiment + 1) / 2  # Map to [0, 1]
        else:
            score = 0.5  # Neutral
            
        scores.append(score)
    
    # Create visualization
    create_heatmap_visualization(paragraphs, scores, "Sentiment Analysis", 
                               threshold, "Sentiment across document (higher = more positive)")

def create_information_density_heatmap(text: str, window_size: int = 10, 
                                     overlap: int = 2, threshold: float = 0.4):
    """
    Create a heatmap visualization of information density.
    
    Args:
        text: Document text
        window_size: Number of sentences per analysis window
        overlap: Number of sentences to overlap between windows
        threshold: Minimum score to include in highlights
    """
    # Split text into sentences
    sentences = sent_tokenize(text)
    
    # Create windows of sentences with overlap
    windows = []
    for i in range(0, len(sentences), window_size - overlap):
        end = min(i + window_size, len(sentences))
        if end - i >= 3:  # Only include windows with at least 3 sentences
            windows.append(' '.join(sentences[i:end]))
    
    # Analyze information density for each window
    scores = []
    for window in windows:
        # Calculate metrics for information density
        word_count = len(window.split())
        avg_word_length = sum(len(word) for word in window.split()) / max(1, word_count)
        unique_ratio = len(set(window.lower().split())) / max(1, word_count)
        
        # Combine metrics into an information density score
        info_density = (0.4 * avg_word_length / 10) + (0.6 * unique_ratio)
        scores.append(min(1.0, info_density * 2))  # Scale and cap at 1.0
    
    # Create visualization
    create_heatmap_visualization(windows, scores, "Information Density", 
                               threshold, "Information density across document")

def create_heatmap_visualization(text_blocks: List[str], scores: List[float], 
                               title: str, threshold: float, description: str):
    """
    Create the visual heatmap display.
    
    Args:
        text_blocks: List of text paragraphs/chunks
        scores: Corresponding scores for each text block
        title: Title for the visualization
        threshold: Minimum score to include in highlights
        description: Description text for the visualization
    """
    st.subheader(title)
    st.caption(description)
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Text View", "Chart View"])
    
    with tab1:
        # Create highlighted text display
        for i, (block, score) in enumerate(zip(text_blocks, scores)):
            if score >= threshold:
                # Determine highlight intensity based on score
                if score >= SCORE_THRESHOLDS["high"]:
                    color = HEATMAP_COLORS["high"]
                    emoji = "🔥"  # Fire emoji for high scores
                elif score >= SCORE_THRESHOLDS["medium"]:
                    color = HEATMAP_COLORS["medium"]
                    emoji = "⚡"  # Lightning emoji for medium scores
                else:
                    color = HEATMAP_COLORS["low"]
                    emoji = "✨"  # Sparkle emoji for low scores
                
                # Display highlighted text
                st.markdown(f"""
                <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <span style="float: right; font-weight: bold;">{emoji} {score:.2f}</span>
                    <p>{block}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Display regular text (lower opacity)
                st.markdown(f"""
                <div style="opacity: 0.7; margin-bottom: 10px;">
                    <p>{block}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        # Create chart visualization
        create_heatmap_chart(text_blocks, scores, title, threshold)

def create_heatmap_chart(text_blocks: List[str], scores: List[float], 
                       title: str, threshold: float):
    """
    Create a chart visualization of the heatmap data.
    
    Args:
        text_blocks: List of text paragraphs/chunks
        scores: Corresponding scores for each text block
        title: Title for the visualization
        threshold: Minimum score to include in highlights
    """
    # Prepare data for chart
    df = pd.DataFrame({
        'Block': [f"Block {i+1} ({min(10, len(block.split()))} words...)" 
                for i, block in enumerate(text_blocks)],
        'Score': scores
    })
    
    # Create bar chart
    fig = px.bar(df, x='Block', y='Score', 
                color='Score',
                color_continuous_scale=[(0, 'lightgrey'), 
                                       (threshold, 'yellow'), 
                                       (SCORE_THRESHOLDS["medium"], 'orange'), 
                                       (SCORE_THRESHOLDS["high"], 'red')],
                title=f"{title} Distribution",
                labels={'Block': 'Document Sections', 'Score': 'Relevance Score'})
    
    # Add threshold line
    fig.add_shape(type="line",
                xref="paper", yref="y",
                x0=0, y0=threshold,
                x1=1, y1=threshold,
                line=dict(color="black", width=2, dash="dash"))
    
    # Add annotation for threshold
    fig.add_annotation(x=0.5, y=threshold,
                     text=f"Threshold ({threshold})",
                     showarrow=False,
                     yshift=10)
    
    # Update layout
    fig.update_layout(height=400)
    
    # Display chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Display summary statistics
    st.write("### Summary Statistics")
    highlight_count = sum(1 for score in scores if score >= threshold)
    highlight_percentage = (highlight_count / len(scores)) * 100 if scores else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Highlight Sections", highlight_count, f"{highlight_percentage:.1f}% of document")
    col2.metric("Average Score", f"{sum(scores) / len(scores):.2f}" if scores else "N/A")
    col3.metric("Peak Score", f"{max(scores):.2f}" if scores else "N/A")
