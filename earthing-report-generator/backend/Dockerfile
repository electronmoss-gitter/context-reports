# Dockerfile for Earthing Report Generator API
# NOTE: This is for future use when you're ready to containerize
# For MVP, run directly with Python (see GETTING_STARTED.md)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download sentence-transformers model (so it's cached in the image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

# Copy application code
COPY app/ ./app/

# Create data directories
RUN mkdir -p /app/data/historical_reports /app/data/vector_db /app/output/generated_reports

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]