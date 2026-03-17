FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports: 8000 (API) and 8501 (Streamlit)
EXPOSE 8000 8501

# Default command runs API
CMD ["uvicorn", "incidentagent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
