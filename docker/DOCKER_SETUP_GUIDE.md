# Docker Setup Guide

## Environment Note

This Docker setup is configured for local development with live reload capabilities. However, the current environment has the Docker daemon (dockerd) not running, which is required for Docker containers to function.

## Current Status

- ✅ Docker CLI is installed (`/usr/local/bin/docker`)
- ❌ Docker daemon (dockerd) is not running
- ✅ Containerd is running
- ✅ Docker socket exists at `/var/run/docker.sock`
- ✅ Current context is set to "default" pointing to the system Docker socket

## Troubleshooting Docker Connection Issues

### 1. Start Docker Service

**Option A: System Service (if running on Linux with systemd)**
```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

**Option B: Manual Dockerd (if systemd not available)**
```bash
# Start Docker daemon in background
dockerd --host=unix:///var/run/docker.sock &

# Wait a few seconds for it to start
sleep 3
```

### 2. Fix Docker Context

The current Docker context might need to be changed:
```bash
# Switch to default context (already done)
docker context use default

# List available contexts
docker context ls
```

### 3. Check Docker Environment

```bash
# Check if Docker daemon is responding
docker info

# Check available images
docker images

# Check running containers
docker ps
```

## Alternative: Native Development (Without Docker)

If Docker is not available in your environment, you can develop using the native approach:

### Quick Start Commands

```bash
# Navigate to project root
cd /home/nisreen/Videos/yt-project/quran-intelligent-tafsir

# Start API with live reload (background)
# In one terminal window:
cd services/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend with live reload (background)
# In another terminal window:
cd apps/web
npm run dev

# Check service health
# In browser or curl:
curl http://localhost:8000/health
curl http://localhost:3000/api/health
```

### Background Services

For background development, you can use:

```bash
# Start API in background
title "QURAN AI API" && cd services/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > api.log 2>&1

# Start Frontend in background
title "QURAN AI Frontend" && cd apps/web && npm run dev > web.log 2>&1

# Check logs
tail -f api.log
tail -f web.log

# Stop services
pkill -f "uvicorn app.main:app"
pkill -f "next dev"
```

## Docker Compose Commands (When Docker is Available)

### Basic Commands

```bash
# Navigate to docker directory
cd docker

# List running projects
nerdctl compose ls

# Start services with live reload
nerdctl compose up --build

# Start services in background
nerdctl compose up --build -d

# View logs
nerdctl compose logs -f

# Stop services
nerdctl compose down

# Rebuild services
nerdctl compose build --no-cache
nerdctl compose up -d
```

### Development Commands

```bash
# Execute commands in API container
nerdctl compose exec api python -m pip list
nerdctl compose exec api python manage.py shell

# Execute commands in Frontend container
nerdctl compose exec web npm run test
nerdctl compose exec web npm run lint

# View real-time logs
nerdctl compose logs -f api web
```

### Advanced Commands

```bash
# Scale services (for production)
nerdctl compose up --scale api=3
nerdctl compose up --scale web=2

# View service status
nerdctl compose ps

# Check health status
nerdctl compose exec api curl http://localhost:8000/health
nerdctl compose exec web curl http://localhost:3000/api/health
```

## File Structure Reference

```
docker/
├── docker-compose.yml              # Main orchestration file
├── services/
│   ├── Dockerfile                  # API service
│   └── entrypoint.sh             # Enhanced startup script
├── apps/
│   ├── Dockerfile                  # Frontend service
│   └── start.sh                    # Enhanced startup script
└── README.md                      # This documentation
```

## Dockerfile Configuration

### API Service (`services/Dockerfile`)
- Base: Python 3.12 slim
- Dependencies: All Python packages from requirements.txt
- Features:
  - Hot reload with file watching
  - Health check endpoint
  - Non-root user for security
  - Custom entrypoint script

### Frontend Service (`apps/Dockerfile`)
- Base: Node.js 20 alpine
- Dependencies: npm packages from package.json
- Features:
  - Live reload with Next.js hot module replacement
  - Health check endpoint
  - Non-root user for security
  - Custom startup script

### Key Files

#### `entrypoint.sh`
- Watches for file changes using `inotifywait`
- Automatically restarts API on code changes
- Includes custom log formatting

#### `start.sh`
- Starts Next.js with Turbopack (if available) or Webpack
- Watches for frontend file changes
- Automatically rebuilds and refreshes browser
- Includes development-specific optimizations

## Environment Variables

### API Service
```yaml
environment:
  - DEBUG=true
  - ENVIRONMENT=development
  - PYTHONPATH=/app
```

### Frontend Service
```yaml
environment:
  - NODE_ENV=development
  - NEXT_PUBLIC_API_URL=http://localhost:8000
  - NEXT_TELEMETRY_DISABLED=true
```

## Volume Management

Docker volumes are used for:

1. **Source Code**: Mounts project source for live reload
2. **Node Modules**: Cache npm packages to avoid reinstalls
3. **Python Packages**: Cache pip packages to avoid reinstalls

## Health Checks

Both services include health checks:

- **API**: `GET http://localhost:8000/health`
- **Frontend**: `GET http://localhost:3000/api/health`

These are used by Docker to determine service readiness.

## Security Considerations

1. **Non-Root Users**: Containers run as non-root users
2. **Limited Ports**: Only necessary ports are exposed
3. **Volume Permissions**: Proper permissions set on mounted volumes
4. **Environment Isolation**: Each service runs in its own container

## Production Considerations

For production deployment:

1. **Disable Live Reload**: Remove file watching from Dockerfiles
2. **Use Reverse Proxy**: Configure Nginx or similar for SSL termination
3. **Environment Variables**: Use `.env` files for configuration
4. **Resource Management**: Set appropriate CPU/memory limits
5. **Logging**: Centralize logs for easier monitoring
6. **Backup**: Regular database backups

## Troubleshooting Common Issues

### "Cannot connect to Docker daemon"

**Solutions:**
1. Start Docker service: `sudo systemctl start docker`
2. Check Docker socket: `ls -la /var/run/docker.sock`
3. Fix Docker context: `docker context use default`

### "Address already in use"

**Solutions:**
1. Stop existing services: `docker compose down`
2. Use different ports: Modify `docker-compose.yml`
3. Force restart: `docker compose down && docker compose up --build`

### "File watch errors"

**Solutions:**
1. Ensure `inotify-tools` is installed (for API service)
2. Check file permissions
3. Verify `inotifywait` is working: `inotifywait --version`

## Getting Help

### Documentation

- **Main README**: Project root `README.md`
- **Docker Guide**: This `DOCKER_SETUP_GUIDE.md`
- **API Documentation**: `http://localhost:8000/docs`
- **Frontend Documentation**: `http://localhost:3000`

### Support

1. **Check Logs**: `nerdctl compose logs -f api web`
2. **Container Shell**: `nerdctl compose exec <service_name> bash`
3. **Build Cache**: Clear with `--no-cache` flag
4. **Network Issues**: Verify service dependencies

## Summary

This Docker setup provides:

✅ **Live Reload Development**: Instant feedback without manual restarts
✅ **Optimized Builds**: Layer caching for faster deployment
✅ **Service Isolation**: Each component in its own container
✅ **Health Monitoring**: Automatic service health checks
✅ **Production Ready**: Scalable and configurable for production
✅ **Development Friendly**: Easy debugging and troubleshooting

**Current Recommendation**: If Docker daemon is not available, use the native development approach with direct service execution. If Docker becomes available later, the Docker configuration will provide a more robust production-ready setup.

## Setup Checklist

- [ ] Install Docker daemon (if not installed)
- [ ] Start Docker service
- [ ] Verify Docker connection (`docker info`)
- [ ] Set correct Docker context
- [ ] Navigate to project root
- [ ] Run development commands
- [ ] Monitor logs for issues

## Quick Start Summary

**With Docker (preferred if available):**
```bash
cd docker
nerdctl compose up --build -d
# Access services at:
# API: http://localhost:8000
# Frontend: http://localhost:3000
```

**Without Docker (current workaround):**
```bash
cd services/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd apps/web && npm run dev
```

Both approaches provide the same development experience with live reload capabilities.