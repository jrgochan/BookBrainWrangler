"""
Word cloud components for visualizing word frequencies and text analysis.
Provides various visualizations for word frequencies and document analytics.
"""

import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import io
import base64
import time
from typing import Dict, List, Any, Optional, Union, Tuple

def render_word_cloud(
    word_frequencies: Dict[str, Union[int, float]], 
    colormap: str = 'viridis', 
    background_color: str = 'white',
    width: int = 800, 
    height: int = 400,
    max_words: int = 200,
    min_font_size: int = 10,
    max_font_size: int = 300,
    random_state: Optional[int] = None,
    mask: Optional[np.ndarray] = None,
    contour_width: int = 0,
    contour_color: str = 'steelblue'
) -> plt.Figure:
    """
    Render a word cloud visualization based on word frequencies.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        colormap: Matplotlib colormap name
        background_color: Background color
        width: Width of the word cloud
        height: Height of the word cloud
        max_words: Maximum number of words to include
        min_font_size: Minimum font size for words
        max_font_size: Maximum font size for words
        random_state: Random state for reproducibility
        mask: Optional mask image for shaping the word cloud
        contour_width: Width of the contour (0 for no contour)
        contour_color: Color of the contour
        
    Returns:
        Figure object for the word cloud
    """
    if not word_frequencies:
        st.warning("No word frequency data available to generate word cloud.")
        # Return an empty figure
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    try:
        # Create the word cloud with enhanced parameters
        wordcloud = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            colormap=colormap,
            max_words=max_words,
            prefer_horizontal=0.9,
            min_font_size=min_font_size,
            max_font_size=max_font_size,
            random_state=random_state,
            mask=mask,
            contour_width=contour_width,
            contour_color=contour_color,
            collocations=False
        ).generate_from_frequencies(word_frequencies)
        
        # Create a figure and plot the word cloud
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        plt.tight_layout(pad=0)
        
        return fig
    except Exception as e:
        st.error(f"Error generating word cloud: {str(e)}")
        # Return an error figure
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center', fontsize=12, wrap=True)
        ax.axis('off')
        return fig

def render_word_frequency_table(
    word_frequencies: Dict[str, Union[int, float]], 
    max_words: int = 50,
    allow_download: bool = True,
    key_prefix: str = "word_freq"
) -> Optional[pd.DataFrame]:
    """
    Render a sortable table of word frequencies with additional features.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        max_words: Maximum number of words to display
        allow_download: Whether to show download button
        key_prefix: Prefix for Streamlit keys
        
    Returns:
        DataFrame object with the frequency data
    """
    if not word_frequencies:
        st.info("No word frequency data available.")
        return None
    
    try:
        # Create a DataFrame from the word frequencies
        df = pd.DataFrame({
            'Word': list(word_frequencies.keys()),
            'Frequency': list(word_frequencies.values())
        }).sort_values(by='Frequency', ascending=False).head(max_words)
        
        # Add rank column
        df.insert(0, 'Rank', range(1, len(df) + 1))
        
        # Add percentage column
        total_frequency = df['Frequency'].sum()
        df['Percentage'] = df['Frequency'].apply(lambda x: f"{(x / total_frequency * 100):.2f}%")
        
        # Display the table with sorting enabled
        st.dataframe(
            df,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", help="Position by frequency"),
                "Word": st.column_config.TextColumn("Word", help="The word or term"),
                "Frequency": st.column_config.NumberColumn("Count", help="Number of occurrences"),
                "Percentage": st.column_config.TextColumn("% of Total", help="Percentage of total occurrences")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Add download buttons
        if allow_download:
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="word_frequencies.csv",
                    mime="text/csv",
                    key=f"{key_prefix}_download_csv"
                )
            
            with col2:
                excel_file = io.BytesIO()
                df.to_excel(excel_file, index=False, engine='openpyxl')
                excel_file.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=excel_file,
                    file_name="word_frequencies.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"{key_prefix}_download_excel"
                )
        
        return df
    
    except Exception as e:
        st.error(f"Error creating frequency table: {str(e)}")
        return None

def render_frequency_chart(
    word_frequencies: Dict[str, Union[int, float]], 
    max_words: int = 20, 
    chart_type: str = 'bar', 
    title: str = 'Top Words',
    color: str = '#1f77b4',
    show_values: bool = True,
    horizontal: bool = False
) -> Optional[plt.Figure]:
    """
    Render a chart of word frequencies with enhanced options.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        max_words: Maximum number of words to display
        chart_type: Type of chart ('bar', 'line', or 'pie')
        title: Chart title
        color: Color for the chart elements
        show_values: Whether to show values on the chart
        horizontal: Whether to display horizontal bar chart (for bar type only)
        
    Returns:
        Figure object for the chart
    """
    if not word_frequencies:
        st.info("No word frequency data available for chart.")
        return None
    
    try:
        # Get the top N words
        top_words = dict(sorted(word_frequencies.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:max_words])
        
        # Create a DataFrame
        df = pd.DataFrame({
            'Word': list(top_words.keys()),
            'Frequency': list(top_words.values())
        })
        
        # Create the chart with appropriate size
        fig_width = 10
        fig_height = 5 if not horizontal else max(5, max_words * 0.25)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        if chart_type == 'bar':
            if horizontal:
                # Horizontal bar chart (better for many categories)
                bars = ax.barh(df['Word'], df['Frequency'], color=color)
                ax.set_xlabel('Frequency')
                ax.set_ylabel('Word')
                
                # Add values on bars
                if show_values:
                    for bar in bars:
                        width = bar.get_width()
                        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                               f'{width}', ha='left', va='center')
            else:
                # Vertical bar chart
                bars = ax.bar(df['Word'], df['Frequency'], color=color)
                ax.set_xlabel('Word')
                ax.set_ylabel('Frequency')
                
                # Add values on bars
                if show_values:
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2, height + 0.5,
                               f'{height}', ha='center', va='bottom')
        
        elif chart_type == 'line':
            line = ax.plot(df['Word'], df['Frequency'], 'o-', color=color)
            ax.set_xlabel('Word')
            ax.set_ylabel('Frequency')
            
            # Add values on points
            if show_values:
                for i, freq in enumerate(df['Frequency']):
                    ax.text(i, freq + 0.5, f'{freq}', ha='center', va='bottom')
        
        elif chart_type == 'pie':
            # For pie chart, limit to fewer categories for readability
            pie_df = df.head(min(10, len(df)))
            ax.pie(pie_df['Frequency'], labels=pie_df['Word'], autopct='%1.1f%%', 
                  shadow=True, startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Set title
        ax.set_title(title)
        
        # Rotate x-axis labels for better readability (for non-horizontal bar and line charts)
        if chart_type != 'pie' and not horizontal:
            plt.xticks(rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return None

def render_interactive_word_cloud(
    word_frequencies: Dict[str, Union[int, float]],
    allow_customization: bool = True,
    key_prefix: str = "interactive_wc"
) -> None:
    """
    Render an interactive word cloud with customization controls.
    
    Args:
        word_frequencies: Dictionary of word frequencies
        allow_customization: Whether to show customization controls
        key_prefix: Prefix for Streamlit keys
    """
    if not word_frequencies:
        st.info("No word frequency data available for visualization.")
        return
    
    # Set up default parameters
    width = 800
    height = 400
    colormap = 'viridis'
    background_color = 'white'
    max_words = 200
    
    # Add customization controls if enabled
    if allow_customization:
        with st.expander("Word Cloud Customization", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Color scheme
                colormap = st.selectbox(
                    "Color scheme",
                    options=[
                        'viridis', 'plasma', 'inferno', 'magma', 'cividis',
                        'Greys', 'Blues', 'Greens', 'Oranges', 'Reds',
                        'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu',
                        'coolwarm', 'PiYG', 'PRGn', 'RdYlGn', 'RdYlBu'
                    ],
                    index=0,
                    key=f"{key_prefix}_colormap"
                )
                
                # Background color
                background_color = st.color_picker(
                    "Background color",
                    value=background_color,
                    key=f"{key_prefix}_bg_color"
                )
            
            with col2:
                # Word count
                max_words = st.slider(
                    "Maximum words",
                    min_value=10,
                    max_value=500,
                    value=max_words,
                    step=10,
                    key=f"{key_prefix}_max_words"
                )
                
                # Size
                size_option = st.radio(
                    "Word cloud size",
                    options=["Small", "Medium", "Large"],
                    index=1,
                    horizontal=True,
                    key=f"{key_prefix}_size"
                )
                
                # Map size option to dimensions
                if size_option == "Small":
                    width, height = 600, 300
                elif size_option == "Medium":
                    width, height = 800, 400
                else:  # Large
                    width, height = 1000, 500
    
    # Generate the word cloud
    with st.spinner("Generating word cloud..."):
        fig = render_word_cloud(
            word_frequencies,
            colormap=colormap,
            background_color=background_color,
            width=width,
            height=height,
            max_words=max_words
        )
    
    # Display the word cloud
    st.pyplot(fig)
    
    # Add download button
    download_link = get_word_cloud_download_link(fig, f"wordcloud_{int(time.time())}.png")
    st.markdown(download_link, unsafe_allow_html=True)

def get_word_cloud_download_link(
    fig: plt.Figure, 
    filename: str = "wordcloud.png",
    dpi: int = 300
) -> str:
    """
    Generate a download link for the word cloud image.
    
    Args:
        fig: Matplotlib figure object
        filename: Name of the download file
        dpi: Dots per inch for the saved image
        
    Returns:
        HTML string with download link
    """
    try:
        # Save the figure to a bytes buffer with high quality
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        
        # Encode the bytes to base64
        b64 = base64.b64encode(buf.read()).decode()
        
        # Create the download link with button styling
        href = f"""
        <a href="data:image/png;base64,{b64}" download="{filename}" 
           style="display: inline-block; padding: 0.5em 1em; 
                  text-decoration: none; color: white;
                  background-color: #4CAF50; border-radius: 4px;
                  font-weight: bold; text-align: center;">
           📥 Download Word Cloud
        </a>
        """
        
        return href
    
    except Exception as e:
        return f"<p style='color: red;'>Error creating download link: {str(e)}</p>"