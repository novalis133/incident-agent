FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY incidentagent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY incidentagent/ .

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "incidentagent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
