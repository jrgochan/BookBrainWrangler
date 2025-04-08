FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    default-jdk \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir Cython && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir jnius || echo "jnius installation failed, but continuing"

# Copy application files
COPY . .

# Create .streamlit directory and config
RUN mkdir -p .streamlit
RUN echo '[server]\nheadless = true\nport = 8501\naddress = "0.0.0.0"' > .streamlit/config.toml

# Expose the port Streamlit will run on
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py"]