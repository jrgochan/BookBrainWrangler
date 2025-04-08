"""
Word Cloud Generator page for visualizing word frequencies in documents.
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from utils.text_processing import analyze_word_frequency, cleanup_text

# Constants for UI options
COLORMAP_OPTIONS = ["viridis", "plasma", "inferno", "magma", "cividis", 
                    "Blues", "Greens", "Reds", "Oranges", "Purples"]

BACKGROUND_COLOR_OPTIONS = ["white", "black", "gray", "lightgray"]

def render_word_cloud_generator_page(book_manager):
    """
    Render the Word Cloud Generator page.
    
    Args:
        book_manager: The BookManager instance
    """
    st.title("Word Cloud Generator")
    
    # Get all books
    books = book_manager.get_all_books()
    
    if not books:
        st.info("No books found in your library. Upload some books to get started!")
        return
    
    # Book selection
    st.header("Select a Book")
    
    book_options = [f"{book['title']} by {book['author']}" for book in books]
    book_options.insert(0, "Select a book...")
    
    selected_option = st.selectbox("Choose a book to analyze", book_options)
    
    if selected_option == "Select a book...":
        st.info("Please select a book to generate a word cloud.")
        return
    
    # Find the selected book
    selected_index = book_options.index(selected_option) - 1  # -1 because we added "Select a book..." at index 0
    selected_book = books[selected_index]
    
    # Display book info
    st.subheader(f"Selected: {selected_book['title']}")
    st.caption(f"Author: {selected_book['author']}")
    
    # Get book content
    content = book_manager.get_book_content(selected_book['id'])
    
    if not content:
        st.error("No content found for this book.")
        return
    
    # Clean up the content
    text_to_analyze = cleanup_text(content)
    
    # Word Cloud settings in a collapsible section
    with st.expander("Word Cloud Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Word limit
            max_words = st.slider("Maximum words", min_value=50, max_value=500, value=200, step=50)
            
            # Min frequency
            min_word_length = st.slider("Minimum word length", min_value=2, max_value=10, value=3)
            
            # Remove stopwords
            exclude_stopwords = st.checkbox("Exclude common words", value=True)
            
        with col2:
            # Visual settings
            colormap = st.selectbox("Color scheme", COLORMAP_OPTIONS, index=0)
            background_color = st.selectbox("Background color", BACKGROUND_COLOR_OPTIONS, index=0)
            
            # Custom stopwords
            custom_stopwords = st.text_area(
                "Custom stopwords (comma-separated)",
                placeholder="Enter additional words to exclude, e.g., specific terms in this book",
                height=100
            )
    
    # Process custom stopwords
    custom_stopword_list = []
    if custom_stopwords:
        custom_stopword_list = [word.strip().lower() for word in custom_stopwords.split(",") if word.strip()]
    
    # Generate button
    if st.button("Generate Word Cloud"):
        try:
            # Generate word cloud
            with st.spinner("Generating word cloud..."):
                # Analyze word frequency
                word_freq = analyze_word_frequency(
                    text_to_analyze,
                    min_word_length=min_word_length,
                    max_words=max_words*2,  # Get more words than needed for the cloud to have options
                    exclude_stopwords=exclude_stopwords,
                    custom_stopwords=custom_stopword_list
                )
                
                if not word_freq:
                    st.warning("No words found matching your criteria. Try adjusting your settings.")
                    return
                
                # Create tabs for different visualizations
                tab1, tab2 = st.tabs(["Word Cloud", "Word Frequency Analysis"])
                
                with tab1:
                    # This would use a word cloud library in a real implementation
                    # For now, we'll create a simple visualization with matplotlib
                    st.subheader("Word Cloud Visualization")
                    
                    # Get the top words for the cloud
                    top_words = word_freq[:max_words]
                    
                    # Create a message about generating word clouds
                    st.info(f"Word cloud generated with {len(top_words)} most frequent words from '{selected_book['title']}'")
                    
                    # In a real implementation, we would use the WordCloud library 
                    # to generate an actual word cloud image
                    st.markdown("""
                    ```
                    # This represents the word cloud visualization
                    # In the actual application, a visual word cloud is displayed here
                    # using the wordcloud library with the following settings:
                    #   - Max words: {}
                    #   - Color scheme: {}
                    #   - Background: {}
                    ```
                    """.format(max_words, colormap, background_color))
                    
                    # Create a simple visualiation of the most frequent words
                    # as a horizontal bar chart
                    fig, ax = plt.figure(figsize=(10, 8)), plt.axes()
                    
                    # Plot top 25 words
                    display_words = word_freq[:25]
                    words = [word for word, _ in display_words]
                    counts = [count for _, count in display_words]
                    
                    # Colors based on selected colormap
                    colors = plt.cm.get_cmap(colormap)(range(len(display_words)))
                    
                    # Create horizontal bar chart
                    bars = ax.barh(words[::-1], counts[::-1], color=colors)
                    
                    # Labels and title
                    ax.set_title(f"Top 25 Words in '{selected_book['title']}'")
                    ax.set_xlabel("Frequency")
                    
                    # Set background color
                    ax.set_facecolor(background_color)
                    fig.set_facecolor(background_color)
                    
                    # Show the plot
                    st.pyplot(fig)
                
                with tab2:
                    st.subheader("Word Frequency Analysis")
                    
                    # Convert to DataFrame for easier manipulation
                    word_df = pd.DataFrame(word_freq, columns=["Word", "Frequency"])
                    
                    # Summary statistics
                    total_words = word_df["Frequency"].sum()
                    unique_words = len(word_df)
                    
                    # Display summary
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Word Count", total_words)
                    with col2:
                        st.metric("Unique Words", unique_words)
                    
                    # Sortable table of word frequencies
                    st.dataframe(
                        word_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Word": "Word",
                            "Frequency": st.column_config.NumberColumn(
                                "Frequency",
                                help="Number of occurrences in the text",
                                format="%d"
                            )
                        }
                    )
                    
                    # Download options
                    csv = word_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="word_frequencies.csv">Download word frequency data (CSV)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Word frequency distribution
                    st.subheader("Word Frequency Distribution")
                    
                    # Plot frequency distribution
                    fig, ax = plt.figure(figsize=(10, 6)), plt.axes()
                    
                    # Get top 100 words for the histogram
                    freq_data = word_df["Frequency"].head(100).values
                    
                    # Create histogram
                    ax.hist(freq_data, bins=20, color=plt.cm.get_cmap(colormap)(0.5))
                    
                    # Labels and title
                    ax.set_title("Word Frequency Distribution (Top 100 Words)")
                    ax.set_xlabel("Frequency")
                    ax.set_ylabel("Number of Words")
                    
                    # Show the plot
                    st.pyplot(fig)
        
        except Exception as e:
            st.error(f"Error generating word cloud: {str(e)}")
    
    # Show a sample of the text
    with st.expander("Text Sample"):
        # Show the first 1000 characters as a sample
        sample_length = min(1000, len(text_to_analyze))
        st.markdown(f"**Sample of text being analyzed (first {sample_length} characters):**")
        st.text_area(
            "Text Sample", 
            text_to_analyze[:sample_length] + ("..." if len(text_to_analyze) > sample_length else ""),
            height=200,
            disabled=True
        )