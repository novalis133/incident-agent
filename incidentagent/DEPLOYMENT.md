# Deployment Checklist for IncidentAgent

This document outlines the steps for deploying IncidentAgent to various environments.

## Pre-Deployment

### Local Development Environment

- [ ] Clone the repository
- [ ] Copy `.env.example` to `.env`
- [ ] Update `.env` with local development settings
- [ ] Install Docker and Docker Compose
- [ ] Run `docker-compose build`
- [ ] Run `docker-compose up -d`
- [ ] Verify services are running: `make health`
- [ ] Test API: `curl http://localhost:8000/docs`
- [ ] Test Dashboard: Open http://localhost:8501

### Staging Environment

- [ ] Use `.env.staging` with staging credentials
- [ ] Run tests: `make test`
- [ ] Run linting: `make lint`
- [ ] Build images: `docker-compose build`
- [ ] Deploy: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Verify services are healthy
- [ ] Run smoke tests against staging API
- [ ] Test dashboard functionality
- [ ] Verify data isolation

### Production Environment

#### Pre-Deployment Security Checks

- [ ] Rotate all API tokens and credentials
- [ ] Update `.env.prod` with production secrets
- [ ] Review Elasticsearch security settings (enable authentication)
- [ ] Configure SSL/TLS certificates
- [ ] Set up backup strategy for Elasticsearch volumes
- [ ] Configure log aggregation (ELK, Splunk, etc.)
- [ ] Set up monitoring and alerting
- [ ] Configure rate limiting
- [ ] Test failover procedures
- [ ] Review security group/firewall rules

#### Deployment Steps

1. **Infrastructure Preparation**
   ```bash
   # Ensure sufficient resources
   # Recommended: 4 CPU cores, 8GB RAM minimum

   # Create SSL certificates
   mkdir -p ssl/
   # Add cert.pem and key.pem

   # Prepare Elasticsearch persistent volume
   mkdir -p /data/elasticsearch
   chmod 777 /data/elasticsearch
   ```

2. **Environment Configuration**
   ```bash
   # Create production environment file
   cp .env.example .env.prod

   # Edit with production values
   # Update: API keys, passwords, hostnames, etc.
   nano .env.prod

   # Verify sensitive values are not in version control
   grep -r "GRADIENT_API_TOKEN\|API_KEY" .
   ```

3. **Build and Deploy**
   ```bash
   # Build images
   docker-compose build

   # Pull latest base images
   docker-compose pull

   # Start services
   docker-compose -f docker-compose.prod.yml \
     --env-file .env.prod \
     up -d
   ```

4. **Verification**
   ```bash
   # Check service health
   docker-compose ps
   docker-compose logs -f

   # Verify API
   curl -H "Authorization: Bearer <token>" \
     https://incident-agent.example.com/health

   # Verify Elasticsearch
   curl -u elastic:password \
     https://incident-agent.example.com:9200/_cluster/health

   # Verify Dashboard
   # Open https://incident-agent.example.com
   ```

5. **Post-Deployment**
   - [ ] Monitor logs for errors
   - [ ] Verify data is persisting (check volumes)
   - [ ] Test API endpoints with production data
   - [ ] Verify backups are running
   - [ ] Monitor system resources
   - [ ] Document any manual configurations

## Updating a Running Deployment

### Zero-Downtime Update

```bash
# 1. Build new images
docker-compose build

# 2. Pull any base image updates
docker-compose pull

# 3. Deploy with rolling update
docker-compose up -d --no-deps --build api
docker-compose up -d --no-deps --build dashboard

# 4. Verify services
docker-compose ps
```

### Database Migrations (if needed)

```bash
# Create backup before migration
docker-compose exec elasticsearch \
  curl -X POST "localhost:9200/_snapshot/backup/create"

# Run migration scripts
docker-compose exec api python -m incidentagent.migrations.run

# Verify data integrity
```

## Rollback Procedure

```bash
# 1. Stop current deployment
docker-compose down

# 2. Revert to previous image tag
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify services
docker-compose ps
docker-compose logs -f
```

## Monitoring and Maintenance

### Daily Checks

```bash
# Health status
make health

# Log errors
docker-compose logs --tail=100 api | grep ERROR
docker-compose logs --tail=100 dashboard | grep ERROR

# Disk space
docker system df

# Resource usage
docker stats
```

### Weekly Tasks

- [ ] Review logs for warnings
- [ ] Verify backups completed successfully
- [ ] Check Elasticsearch cluster health
- [ ] Monitor API response times
- [ ] Verify SSL certificate expiration (> 30 days)

### Monthly Tasks

- [ ] Update base images
- [ ] Review security updates
- [ ] Analyze performance metrics
- [ ] Test disaster recovery procedure
- [ ] Review and clean up old logs

## Common Issues and Fixes

### Service Won't Start

```bash
# Check logs
docker-compose logs <service_name>

# Verify image built correctly
docker images | grep incidentagent

# Try rebuilding
docker-compose build --no-cache <service_name>
```

### Elasticsearch Connection Issues

```bash
# Verify container is running
docker-compose ps elasticsearch

# Check connectivity
docker-compose exec api curl http://elasticsearch:9200/

# Check logs
docker-compose logs elasticsearch

# Reset Elasticsearch (WARNING: deletes data)
docker-compose down
docker volume rm incidentagent_elasticsearch_data
docker-compose up -d elasticsearch
```

### High Memory Usage

```bash
# Check service resource usage
docker stats

# Increase Elasticsearch heap
# Edit docker-compose.yml:
# ES_JAVA_OPTS: "-Xms2g -Xmx2g"

# Restart with new settings
docker-compose up -d
```

### API Errors with 502 Bad Gateway

```bash
# Check API health
curl -v http://localhost:8000/health

# Review API logs
docker-compose logs api -f

# Check Nginx configuration
docker-compose logs nginx -f
```

## Backup and Recovery

### Elasticsearch Backup

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d'{"type": "fs", "settings": {"location": "/backup"}}'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup/snapshot-1"

# List snapshots
curl -X GET "localhost:9200/_snapshot/backup/_all"

# Restore from snapshot
curl -X POST "localhost:9200/_snapshot/backup/snapshot-1/_restore"
```

### Volume Backup

```bash
# Backup Elasticsearch volume
docker run --rm \
  -v incidentagent_elasticsearch_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/elasticsearch_backup.tar.gz /data

# Restore from backup
docker run --rm \
  -v incidentagent_elasticsearch_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/elasticsearch_backup.tar.gz -C /
```

## Scaling

### Horizontal Scaling (Multiple Nodes)

For multi-node Kubernetes deployment, use Helm charts:

```bash
# Install Helm chart
helm install incidentagent ./helm-charts \
  -f values-prod.yaml
```

### Vertical Scaling (Larger Instance)

```bash
# Update docker-compose.prod.yml
# Increase resource limits:
# cpus: '4'
# memory: 4G

# Rebuild and redeploy
docker-compose -f docker-compose.prod.yml up -d
```

## Security Hardening

### Network Security

- [ ] Restrict API access to known IPs
- [ ] Use VPN for Elasticsearch access
- [ ] Enable TLS for all connections
- [ ] Configure firewall rules

### Authentication

- [ ] Implement API key rotation schedule
- [ ] Use strong Elasticsearch passwords
- [ ] Enable audit logging
- [ ] Implement OAuth2/OIDC if needed

### Data Protection

- [ ] Enable encryption at rest
- [ ] Configure field-level encryption
- [ ] Regular security scanning of images
- [ ] Keep dependencies up to date

## Support and Documentation

- Reference: `/DOCKER.md` for Docker-specific documentation
- Logs: `docker-compose logs -f` for real-time monitoring
- Status: `docker-compose ps` for service status
- Health: `make health` for health check

## Contacts and Escalation

For production issues:
1. Check logs: `docker-compose logs -f`
2. Verify health: `make health`
3. Check system resources: `docker stats`
4. Review recent changes: `git log --oneline -10`
