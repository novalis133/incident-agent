# IncidentAgent Docker Setup Guide

Quick reference guide for Docker and Docker Compose operations.

## Quick Start (5 minutes)

```bash
# 1. Clone and setup
git clone <repo-url>
cd incidentagent

# 2. Configure environment
cp .env.example .env
# Edit .env with your Gradient API credentials

# 3. Build and run
docker-compose build
docker-compose up -d

# 4. Access services
# API:       http://localhost:8000
# Docs:      http://localhost:8000/docs
# Dashboard: http://localhost:8501
```

## File Structure

```
incidentagent/
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── .dockerignore              # Files excluded from image
├── nginx.conf                 # Nginx reverse proxy config
├── scripts/
│   └── start.sh              # Multi-service startup script
├── Makefile                   # Convenience commands
├── DOCKER.md                  # Detailed Docker documentation
├── DOCKER_README.md           # This file
└── DEPLOYMENT.md              # Deployment checklist
```

## Essential Commands

### Build and Run

```bash
# Build images
make build
# or: docker-compose build

# Start services (background)
make up
# or: docker-compose up -d

# View logs
make logs
# or: docker-compose logs -f

# Stop services
make stop
# or: docker-compose stop

# Restart services
make restart
# or: make down && make up

# Clean up (removes volumes!)
make clean
```

### Development

```bash
# Access container shell
make shell-api
docker-compose exec api /bin/bash

# Run tests
make test
docker-compose exec api pytest tests/

# Run linting
make lint
docker-compose exec api ruff check .

# Format code
make format
docker-compose exec api black incidentagent/
```

### Monitoring

```bash
# Health check
make health
curl http://localhost:8000/health

# View API logs
make api-logs
docker-compose logs -f api

# View dashboard logs
make dashboard-logs
docker-compose logs -f dashboard

# Check service status
docker-compose ps

# Monitor resource usage
docker stats
```

## Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Key variables:
- `GRADIENT_API_TOKEN`: Your Gradient API token (required)
- `GRADIENT_MODEL_ACCESS_KEY`: Your model access key (required)
- `LLM_MODEL`: LLM to use (default: claude-3-sonnet)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING)

### Service Ports

| Service | Port | URL |
|---------|------|-----|
| API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| Dashboard | 8501 | http://localhost:8501 |
| Elasticsearch | 9200 | http://localhost:9200 |

## Common Tasks

### Adding Python Dependencies

```bash
# 1. Update requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Rebuild image
make build

# 3. Restart service
make restart
```

### Accessing Application Logs

```bash
# View last 100 lines
docker-compose logs --tail=100 api

# Follow real-time logs
docker-compose logs -f api

# View logs from specific time
docker-compose logs --since 2024-01-01T00:00:00Z api
```

### Database/Elasticsearch

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health | python -m json.tool

# View indices
curl http://localhost:9200/_cat/indices

# Backup data
docker-compose exec elasticsearch \
  curl -X POST "localhost:9200/_snapshot/backup/create"

# View volumes
docker volume ls | grep incidentagent
```

### Debugging

```bash
# Enter API container with bash
make shell-api

# Run Python script in container
docker-compose exec api python -c "print('test')"

# Check environment variables
docker-compose exec api env | grep GRADIENT

# Test connectivity
docker-compose exec api curl http://elasticsearch:9200/
```

## Production Deployment

For production use `docker-compose.prod.yml`:

```bash
# Using production config
docker-compose -f docker-compose.prod.yml \
  --env-file .env.prod \
  up -d

# With Nginx reverse proxy
docker-compose -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f
```

See `DEPLOYMENT.md` for full production checklist.

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs <service>

# Verify image exists
docker images | grep incidentagent

# Rebuild
docker-compose build --no-cache

# Restart
make restart
```

### Port already in use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
# ports:
#   - "8001:8000"
```

### Elasticsearch connection issues

```bash
# Test connection
docker-compose exec api curl http://elasticsearch:9200/

# Check Elasticsearch logs
docker-compose logs elasticsearch

# Verify network
docker network ls
docker network inspect incidentagent_network
```

### Out of disk space

```bash
# Check disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup
make clean
```

### Memory issues

```bash
# Check resource usage
docker stats

# Limit service memory (in docker-compose.yml):
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Increase Docker Desktop memory:
# Settings > Resources > Memory: 4GB+
```

## Advanced Topics

### Custom Network

Modify `docker-compose.yml` to create isolated networks for different services.

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect incidentagent_elasticsearch_data

# Backup volume
docker run --rm \
  -v incidentagent_elasticsearch_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/es-backup.tar.gz /data

# Remove volume
docker volume rm incidentagent_elasticsearch_data
```

### Image Management

```bash
# View image details
docker inspect incidentagent:latest

# Build with specific tag
docker build -t incidentagent:v1.0.0 .

# Push to registry
docker tag incidentagent:latest myregistry/incidentagent:latest
docker push myregistry/incidentagent:latest
```

### Docker Compose Overrides

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'
services:
  api:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

## Performance Tips

1. **Use named volumes** for better performance than bind mounts
2. **Enable BuildKit** for faster builds: `export DOCKER_BUILDKIT=1`
3. **Use .dockerignore** to exclude unnecessary files
4. **Limit container resources** to prevent resource exhaustion
5. **Use multi-stage builds** to reduce image size

## Security Best Practices

1. **Don't commit `.env`** files with secrets
2. **Use environment variables** for all credentials
3. **Keep images updated**: `docker-compose pull`
4. **Scan images** for vulnerabilities
5. **Use read-only volumes** where possible
6. **Limit container capabilities**

## Useful Resources

- Docker Docs: https://docs.docker.com/
- Docker Compose Docs: https://docs.docker.com/compose/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Elasticsearch Docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html

## Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Review DOCKER.md for detailed documentation
3. Check DEPLOYMENT.md for production guidance
4. Verify environment variables: `docker-compose config`
5. Test connectivity: `docker-compose exec api curl http://elasticsearch:9200/`

## Version Information

- Python: 3.11
- Docker: 20.10+
- Docker Compose: 2.0+
- Elasticsearch: 8.11.0
- Streamlit: 1.29+
- FastAPI: 0.109+

## License

See parent project LICENSE file.

---

Last updated: 2024
For the latest version, see: https://github.com/your-org/incidentagent
