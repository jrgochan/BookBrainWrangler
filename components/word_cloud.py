"""
Word cloud component for visualizing word frequencies.
"""

import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import io
import base64

def render_word_cloud(word_frequencies, 
                     colormap='viridis', 
                     background_color='white',
                     width=800, 
                     height=400,
                     max_words=200):
    """
    Render a word cloud visualization based on word frequencies.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        colormap: Matplotlib colormap name
        background_color: Background color
        width: Width of the word cloud
        height: Height of the word cloud
        max_words: Maximum number of words to include
        
    Returns:
        Figure object for the word cloud
    """
    # Create the word cloud
    wordcloud = WordCloud(
        width=width,
        height=height,
        background_color=background_color,
        colormap=colormap,
        max_words=max_words,
        prefer_horizontal=0.9,
        collocations=False
    ).generate_from_frequencies(word_frequencies)
    
    # Create a figure and plot the word cloud
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout(pad=0)
    
    return fig

def render_word_frequency_table(word_frequencies, max_words=50):
    """
    Render a sortable table of word frequencies.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        max_words: Maximum number of words to display
    """
    # Create a DataFrame from the word frequencies
    df = pd.DataFrame({
        'Word': list(word_frequencies.keys()),
        'Frequency': list(word_frequencies.values())
    }).sort_values(by='Frequency', ascending=False).head(max_words)
    
    # Display the table
    st.dataframe(df)

def render_frequency_chart(word_frequencies, max_words=20, 
                          chart_type='bar', title='Top Words'):
    """
    Render a chart of word frequencies.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        max_words: Maximum number of words to display
        chart_type: Type of chart ('bar' or 'line')
        title: Chart title
    """
    # Get the top N words
    top_words = dict(sorted(word_frequencies.items(), 
                            key=lambda x: x[1], 
                            reverse=True)[:max_words])
    
    # Create a DataFrame
    df = pd.DataFrame({
        'Word': list(top_words.keys()),
        'Frequency': list(top_words.values())
    })
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(10, 5))
    
    if chart_type == 'bar':
        ax.bar(df['Word'], df['Frequency'])
    else:  # line chart
        ax.plot(df['Word'], df['Frequency'], 'o-')
    
    # Set labels and title
    ax.set_xlabel('Word')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Display the chart
    st.pyplot(fig)

def get_word_cloud_download_link(fig, filename="wordcloud.png"):
    """
    Generate a download link for the word cloud image.
    
    Args:
        fig: Matplotlib figure object
        filename: Name of the download file
        
    Returns:
        HTML string with download link
    """
    # Save the figure to a bytes buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    
    # Encode the bytes to base64
    b64 = base64.b64encode(buf.read()).decode()
    
    # Create the download link
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">Download Word Cloud</a>'
    
    return href