FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Neo4j dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader punkt stopwords

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data/raw data/processed

# Expose port for Flask application
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=src/visualization/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# Command to run the application
CMD ["flask", "run"] 