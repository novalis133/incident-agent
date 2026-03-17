# Docker Deployment Guide for IncidentAgent

This guide explains how to build, deploy, and manage the IncidentAgent application using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Bash/Shell environment

## Quick Start

### 1. Environment Setup

Copy the template environment file and update with your credentials:

```bash
cp .env.docker .env
# Edit .env with your Gradient API credentials and other settings
```

Required environment variables:
- `GRADIENT_API_TOKEN`: Your Gradient API token
- `GRADIENT_MODEL_ACCESS_KEY`: Your model access key
- `LLM_MODEL`: The LLM model to use (default: claude-3-sonnet)

### 2. Build Images

```bash
# Build all Docker images
docker-compose build

# Or using make
make build
```

### 3. Start Services

```bash
# Start all services in background
docker-compose up -d

# Or using make
make up
```

This will start:
- **API Service**: FastAPI on port 8000
- **Dashboard**: Streamlit on port 8501
- **Elasticsearch**: Data store on port 9200

## Usage

### Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc
- **Dashboard**: http://localhost:8501
- **Elasticsearch**: http://localhost:9200

### View Logs

```bash
# All services
make logs

# Specific service
make api-logs
make dashboard-logs
```

### Shell Access

```bash
# Access API container
make shell-api

# Access Dashboard container
make shell-dashboard
```

### Stop Services

```bash
# Stop containers (keep volumes)
make stop

# Stop and remove containers
make down

# Stop and remove everything including volumes
make clean
```

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Run API
uvicorn incidentagent.api.app:app --reload --port 8000

# In another terminal, run dashboard
streamlit run incidentagent/ui/dashboard.py
```

### Running Tests

```bash
# Inside container
make test

# Local with pytest
pytest tests/ -v --cov=incidentagent
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format
```

## Docker Architecture

### Dockerfile

The Dockerfile uses a multi-stage approach:
- **Base Image**: `python:3.11-slim`
- **Working Directory**: `/app`
- **System Dependencies**: curl, gcc
- **Python Dependencies**: Installed from requirements.txt
- **Exposed Ports**: 8000 (API), 8501 (Dashboard)

### Docker Compose Services

#### API Service
- **Port**: 8000
- **Command**: `uvicorn incidentagent.api.app:app --host 0.0.0.0 --port 8000`
- **Health Check**: HTTP GET to `/health`
- **Dependencies**: Elasticsearch
- **Volumes**: Current directory (for development)

#### Dashboard Service
- **Port**: 8501
- **Command**: `streamlit run incidentagent/ui/dashboard.py`
- **Dependencies**: API service (waits for healthy)
- **Volumes**: Current directory (for development)

#### Elasticsearch Service
- **Port**: 9200
- **Image**: `docker.elastic.co/elasticsearch/elasticsearch:8.11.0`
- **Configuration**: Single-node cluster, no security
- **Storage**: Named volume `elasticsearch_data`

## Production Deployment

### Security Considerations

For production deployments:

1. **Enable Elasticsearch Security**
   ```yaml
   environment:
     - xpack.security.enabled=true
     - ELASTIC_PASSWORD=your_strong_password
   ```

2. **Use Environment Variables**
   ```bash
   docker-compose --env-file .env.production up -d
   ```

3. **Configure Resource Limits**
   ```yaml
   services:
     api:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 1G
   ```

4. **Set Up Reverse Proxy**
   - Use Nginx or Traefik in front of services
   - Enable HTTPS/TLS
   - Configure rate limiting

### Kubernetes Deployment

For Kubernetes deployment, convert docker-compose to Helm charts or Kustomize:

```bash
# Example: Using Kompose
kompose convert -f docker-compose.yml -o k8s/
```

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs -f

# Restart services
make restart
```

### Database Connection Issues

```bash
# Verify Elasticsearch is running
curl http://localhost:9200/

# Check connectivity from API
docker-compose exec api curl http://elasticsearch:9200/
```

### Port Already in Use

```bash
# Change ports in docker-compose.yml
# Or stop conflicting services
lsof -i :8000
kill -9 <PID>
```

### Out of Disk Space

```bash
# Clean up Docker system
docker system prune -a --volumes
```

## Performance Tuning

### Elasticsearch Tuning

```yaml
environment:
  - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
  - indices.memory.index_buffer_size=40%
```

### API Optimization

```yaml
environment:
  - PYTHONOPTIMIZE=2
  - WORKERS=4
```

## Monitoring

### Health Checks

```bash
# Check API health
make health

# Manual checks
curl http://localhost:8000/health
curl http://localhost:9200/_cluster/health
```

### Logging

Logs are stored in containers. For persistent logging:

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Cleanup

```bash
# Remove all containers and volumes
make clean

# Remove only stopped containers
docker container prune

# Remove unused images
docker image prune -a
```

## Advanced Configuration

### Custom Network

Modify `docker-compose.yml` to create custom networks for service isolation.

### Secrets Management

Use Docker secrets for sensitive data:

```yaml
secrets:
  gradient_token:
    file: ./secrets/gradient_token.txt

services:
  api:
    secrets:
      - gradient_token
```

### Volume Mounting

For development with live code reloading:

```yaml
volumes:
  - .:/app
  - /app/__pycache__  # Exclude cache
```

## Support

For issues or questions:
1. Check logs: `make logs`
2. Verify environment variables: `docker-compose config`
3. Test connectivity: `docker-compose exec api curl http://elasticsearch:9200/`

## License

See parent project LICENSE file.
