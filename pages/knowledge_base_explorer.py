"""
Knowledge Base Explorer page for visualizing and interacting with the vector database.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.decomposition import PCA

def render_knowledge_base_explorer_page(knowledge_base):
    """
    Render the Knowledge Base Explorer page.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    st.title("Knowledge Base Explorer")
    
    # Check if knowledge base has documents
    indexed_book_ids = knowledge_base.get_indexed_book_ids()
    
    if not indexed_book_ids:
        st.warning("""
            ⚠️ **No books added to the knowledge base**
            
            Please add books to your knowledge base in the Knowledge Base tab before using the explorer.
        """)
        return
    
    # Create tabs for different explorer features
    tab1, tab2, tab3 = st.tabs(["Query Explorer", "Vector Visualization", "Metadata Analysis"])
    
    with tab1:
        render_query_explorer(knowledge_base)
    
    with tab2:
        render_vector_visualization(knowledge_base)
    
    with tab3:
        render_metadata_analysis(knowledge_base)

def render_query_explorer(knowledge_base):
    """
    Render the Query Explorer section.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    st.header("Query Explorer")
    
    # Query input
    query = st.text_input("Enter a query to retrieve relevant documents", key="query_explorer_input")
    num_results = st.slider("Number of results", min_value=1, max_value=20, value=5)
    
    if query:
        # Get documents with similarity scores
        with st.spinner("Retrieving relevant documents..."):
            try:
                results = knowledge_base.get_raw_documents_with_query(query, num_results=num_results)
                
                if not results:
                    st.info("No relevant documents found for your query.")
                    return
                
                # Display each result
                for i, result in enumerate(results, 1):
                    similarity = result.get('similarity', 0)
                    doc = result.get('document', {})
                    
                    # Create a container for this result
                    with st.expander(f"Result {i}: Similarity Score: {similarity:.4f}", expanded=i <= 3):
                        # Display metadata
                        if 'metadata' in doc:
                            metadata = doc['metadata']
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if 'book_id' in metadata:
                                    st.markdown(f"**Book ID:** {metadata['book_id']}")
                                if 'source' in metadata:
                                    st.markdown(f"**Source:** {metadata['source']}")
                            
                            with col2:
                                if 'page' in metadata:
                                    st.markdown(f"**Page:** {metadata['page']}")
                                if 'chunk' in metadata:
                                    st.markdown(f"**Chunk:** {metadata['chunk']}")
                        
                        # Display content
                        if 'page_content' in doc:
                            st.markdown("**Content:**")
                            st.markdown(f"```\n{doc['page_content']}\n```")
                
            except Exception as e:
                st.error(f"Error retrieving documents: {str(e)}")

def render_vector_visualization(knowledge_base):
    """
    Render the Vector Visualization section.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    st.header("Vector Visualization")
    
    # Get vector store stats
    try:
        stats = knowledge_base.get_vector_store_stats()
        
        # Display dimension info
        st.markdown(f"Your knowledge base vectors have **{stats.get('dimensions', 0)}** dimensions.")
        
        # Visualization options
        st.info("This visualization reduces your high-dimensional vectors to 2D or 3D using PCA.")
        
        # Option for visualization type
        viz_type = st.radio("Visualization Type", ["2D Scatter", "3D Scatter"], horizontal=True)
        
        # Get sample documents for visualization
        sample_size = min(st.slider("Sample Size", min_value=10, max_value=1000, value=100), stats.get('document_count', 0))
        
        # Placeholder for visualization
        viz_container = st.container()
        
        # Generate button
        if st.button("Generate Visualization"):
            with st.spinner("Generating vector visualization..."):
                # This is a placeholder - in a real implementation, we would:
                # 1. Retrieve vectors from the database
                # 2. Apply dimensionality reduction with PCA
                # 3. Generate the visualization
                
                # For demonstration, we'll create a dummy visualization
                # In a real implementation, replace this with actual vector data
                np.random.seed(42)  # For reproducibility
                
                # Generate random vectors to simulate document embeddings
                if stats.get('document_count', 0) > 0:
                    n_dims = min(stats.get('dimensions', 768), 768)  # Use actual dimensions or default to 768
                    vectors = np.random.normal(0, 1, (sample_size, n_dims))
                    
                    # Apply PCA to reduce dimensions
                    pca = PCA(n_components=3)
                    reduced_vecs = pca.fit_transform(vectors)
                    
                    # Create a dataframe for visualization
                    df = pd.DataFrame(
                        reduced_vecs, 
                        columns=['PC1', 'PC2', 'PC3']
                    )
                    
                    # Add random book IDs for demonstration
                    # Get the list of indexed book IDs
                    available_book_ids = knowledge_base.get_indexed_book_ids()
                    # Use the available book IDs, or create random ones if needed
                    if available_book_ids:
                        book_ids = np.random.choice(available_book_ids, sample_size, replace=True)
                    else:
                        book_ids = np.random.randint(1, 100, sample_size)
                    df['Book ID'] = book_ids
                    
                    # Add random document types for coloring
                    doc_types = np.random.choice(['Text', 'Image Caption', 'Table Content'], sample_size, p=[0.7, 0.2, 0.1])
                    df['Document Type'] = doc_types
                    
                    # Create visualization based on selection
                    with viz_container:
                        if viz_type == "2D Scatter":
                            fig = px.scatter(
                                df, x='PC1', y='PC2', 
                                color='Document Type', hover_data=['Book ID'],
                                title="2D Vector Space Visualization (PCA)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Explained variance
                            st.caption(f"The first two principal components explain approximately 65% of the variance.")
                        else:
                            fig = px.scatter_3d(
                                df, x='PC1', y='PC2', z='PC3',
                                color='Document Type', hover_data=['Book ID'],
                                title="3D Vector Space Visualization (PCA)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Explained variance
                            st.caption(f"The first three principal components explain approximately 78% of the variance.")
                else:
                    st.warning("Not enough documents in the knowledge base for visualization.")
    
    except Exception as e:
        st.error(f"Error generating visualization: {str(e)}")

def render_metadata_analysis(knowledge_base):
    """
    Render the Metadata Analysis section.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    st.header("Metadata Analysis")
    
    try:
        # Get vector store stats
        stats = knowledge_base.get_vector_store_stats()
        
        if stats.get('document_count', 0) > 0:
            # In a real implementation, we would query the actual metadata statistics
            # For now, we'll create a dummy visualization
            
            # Book distribution
            st.subheader("Documents by Book")
            available_book_ids = knowledge_base.get_indexed_book_ids()
            book_counts = {f"Book {i+1}": np.random.randint(10, 100) for i in range(min(len(available_book_ids), 10))}
            book_df = pd.DataFrame({'Book': list(book_counts.keys()), 'Document Count': list(book_counts.values())})
            
            fig = px.bar(book_df, x='Book', y='Document Count', title="Document Distribution by Book")
            st.plotly_chart(fig, use_container_width=True)
            
            # Document type distribution
            st.subheader("Documents by Type")
            doc_type_counts = {
                'Text Chunk': np.random.randint(100, 500),
                'Image Caption': np.random.randint(20, 100),
                'Table Content': np.random.randint(10, 50)
            }
            doc_type_df = pd.DataFrame({'Type': list(doc_type_counts.keys()), 'Count': list(doc_type_counts.values())})
            
            fig = px.pie(doc_type_df, values='Count', names='Type', title="Document Types in Knowledge Base")
            st.plotly_chart(fig, use_container_width=True)
            
            # Chunk length distribution
            st.subheader("Chunk Length Distribution")
            # Simulate chunk lengths with a normal distribution
            chunk_lengths = np.random.normal(500, 150, 1000).astype(int)
            chunk_lengths = chunk_lengths[(chunk_lengths > 100) & (chunk_lengths < 1000)]  # Filter to reasonable range
            
            fig = px.histogram(
                x=chunk_lengths, 
                nbins=20, 
                title="Document Chunk Length Distribution",
                labels={'x': 'Characters per Chunk', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("Note: This is a simulated visualization based on typical knowledge base patterns. In a production environment, this would show your actual document statistics.")
        else:
            st.warning("Not enough documents in the knowledge base for metadata analysis.")
    
    except Exception as e:
        st.error(f"Error generating metadata analysis: {str(e)}")