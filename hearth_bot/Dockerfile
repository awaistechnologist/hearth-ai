FROM python:3.11-slim

WORKDIR /app

# Install dependencies layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy logic
COPY . .

# Run
CMD ["python", "main.py"]
