# 🐳 Docker Deployment Guide

This guide covers the complete Docker setup for the AI Micro-Project Generator, including development, production, and security configurations.

## 📋 Overview

The application consists of three main services:
- **API**: FastAPI backend serving the core application logic
- **Frontend**: React application with Nginx serving static files
- **Sandbox**: Secure Python execution environment for running generated code

## 🚀 Quick Start

### Production Deployment
```bash
# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### Development Setup
```bash
# Start with development overrides (hot reload enabled)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use profiles
docker-compose --profile dev up
```

### Production Deployment
```bash
# Start with production optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🏗️ Service Architecture

### API Service
- **Image**: Custom Python 3.12 slim with multi-stage build
- **Port**: 8000 (internal), proxied through frontend
- **Health Check**: HTTP endpoint validation
- **Volumes**:
  - `api_data`: Application data persistence
  - `cache_data`: ChromaDB and cache storage
- **Security**: Non-root user, minimal dependencies

### Frontend Service
- **Image**: Nginx 1.27 Alpine with React build
- **Port**: 80 (HTTP)
- **Health Check**: HTML content validation
- **Features**:
  - SPA routing support
  - API proxy configuration
  - Gzip compression
  - Security headers

### Sandbox Service
- **Image**: Python 3.12 slim with preinstalled ML libraries
- **Security Features**:
  - Read-only filesystem
  - No new privileges
  - Dropped capabilities
  - Isolated network
  - Limited tmpfs storage
- **Libraries**: pandas, numpy, scikit-learn, matplotlib, torch, etc.

## 🔧 Configuration Files

### Main Configuration (`docker-compose.yml`)
- Base service definitions
- Health checks and dependencies
- Volume and network configuration
- Production-ready defaults
- Uses modern Docker Compose format (no version specified)

### Development Override (`docker-compose.dev.yml`)
- Hot reload for API and frontend
- Direct port exposure for debugging
- Larger resource limits
- Development environment variables

### Production Override (`docker-compose.prod.yml`)
- Resource limits and reservations
- Scaling configuration
- Enhanced logging
- Additional security constraints

## 📁 Volume Management

### Persistent Volumes
- `api_data`: Application data, configurations, and logs
- `cache_data`: ChromaDB vector database and LLM caches

### Development Volumes
- Source code mounted for hot reload
- Separate dev volumes to avoid conflicts

### Backup Strategy
```bash
# Backup volumes
docker run --rm -v ai-micro-project-generator_api_data:/data -v $(pwd):/backup alpine tar czf /backup/api_data_backup.tar.gz -C /data .
docker run --rm -v ai-micro-project-generator_cache_data:/data -v $(pwd):/backup alpine tar czf /backup/cache_data_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v ai-micro-project-generator_api_data:/data -v $(pwd):/backup alpine tar xzf /backup/api_data_backup.tar.gz -C /data
```

## 🔒 Security Features

### Sandbox Security
- **Read-only filesystem**: Prevents file system modifications
- **No new privileges**: Blocks privilege escalation
- **Dropped capabilities**: Removes unnecessary system capabilities
- **Resource limits**: CPU and memory constraints
- **Network isolation**: Limited network access
- **Temporary filesystems**: Secure temporary storage

### General Security
- Non-root users in all containers
- Minimal base images (Alpine/slim)
- Health checks for service monitoring
- Proper secret management via environment files

## 🚨 Health Monitoring

All services include comprehensive health checks:

- **API**: HTTP endpoint validation with timeout
- **Frontend**: HTML content validation
- **Sandbox**: Python interpreter availability

Monitor service health:
```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f sandbox

# Restart unhealthy services
docker-compose restart api
```

## 🛠️ Development Workflow

### Hot Reload Development
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# The API will reload on code changes in ./aipg/
# The frontend will reload on changes in ./frontend/
```

### Debugging
```bash
# Access API container
docker-compose exec api bash

# Access sandbox container
docker-compose exec sandbox bash

# View real-time logs
docker-compose logs -f --tail=100 api
```

### Building Images
```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api

# Build with no cache
docker-compose build --no-cache
```

## 🔄 Scaling and Production

### Horizontal Scaling
```bash
# Scale API service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=3

# Scale with load balancer (requires additional configuration)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.lb.yml up -d
```

### Resource Management
The production configuration includes:
- CPU and memory limits
- Resource reservations
- Restart policies
- Logging configuration

### Environment Variables

Required environment variables (create `.env` file):
```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Optional: Langfuse Integration
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## 🐛 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Verify environment file
cat .env

# Check port conflicts
netstat -tulpn | grep :80
netstat -tulpn | grep :8000
```

**Sandbox security issues:**
```bash
# Temporary: disable read-only for debugging
docker-compose exec --user root sandbox bash

# Check security settings
docker inspect $(docker-compose ps -q sandbox) | grep -A 10 SecurityOpt
```

**Volume permission issues:**
```bash
# Fix volume permissions
docker-compose exec --user root api chown -R app:app /app/data
docker-compose exec --user root api chown -R app:app /app/aipg/cache
```

### Performance Tuning

**Database optimization:**
- Ensure sufficient disk space for ChromaDB
- Monitor memory usage during vector operations
- Consider external vector database for large deployments

**Resource monitoring:**
```bash
# Monitor resource usage
docker stats

# Monitor specific service
docker stats $(docker-compose ps -q api)
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Python Security Best Practices](https://docs.python.org/3/library/security_warnings.html)
