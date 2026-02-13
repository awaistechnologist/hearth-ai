FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# git and curl are often useful. ffmpeg is required for audio processing (Whisper).
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set python path to allow imports from core
ENV PYTHONPATH=/app

# Default command
CMD ["python", "core/api.py"]
