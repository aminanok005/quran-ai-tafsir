# Docker Development Environment

This directory contains Docker configurations for the QURAN AI project development environment with live reload capabilities.

## Overview

The Docker setup provides a complete development environment with hot reload for both the FastAPI backend (API) and Next.js frontend (Web) services. This ensures instant feedback during development with minimal setup complexity.

## Services

### API Service (`services/api/`)
- **Port**: 8000
- **Technology**: FastAPI with Uvicorn
- **Features**: Live reload on code changes, auto-restart, health checks
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Frontend Service (`apps/web/`)
- **Port**: 3000
- **Technology**: Next.js (React)
- **Features**: Hot module replacement, live reload, Tailwind CSS
- **Default Language**: Thai (th)
- **Health Check**: `http://localhost:3000/api/health`

### Redis Cache (`redis/`)
- **Port**: 6379
- **Technology**: Redis with persistence
- **Purpose**: Session caching, rate limiting, message queue

## Getting Started

### Prerequisites

- Docker or nerdctl installed
- Sufficient disk space (at least 2GB)

### Quick Start (Development)

```bash
# Navigate to project root
cd /home/nisreen/Videos/yt-project/quran-intelligent-tafsir

# Start development environment with live reload
nerdctl compose up --build -d

# Check service status
nerdctl compose ps

# View real-time logs
nerdctl compose logs -f

# Stop services
nerdctl compose down
```

### Individual Services

```bash
# Start API with hot reload
nerdctl compose exec api bash

# Start frontend with hot reload
nerdctl compose exec web bash

# Execute commands in containers
nerdctl compose exec api python -m pip list
nerdctl compose exec web npm run test
```

### Rebuild and Restart

```bash
# Rebuild all services and restart
nerdctl compose down && nerdctl compose up --build

# Update dependencies only
nerdctl compose build --no-cache api
nerdctl compose up -d api

# Update frontend only
nerdctl compose build --no-cache web
nerdctl compose up -d web
```

## Development Workflow

1. **Code Changes**: Make changes to any source file in `services/api/` or `apps/web/`
2. **Live Reload**: Automatically restarts affected services
3. **Rebuild**: Compiles/bundles changed code
4. **Verification**: Health checks confirm service readiness
5. **Access**: Services available at their respective ports

### Example

```bash
# Edit a Python file in the API service
echo "print('Hello from reloaded API')" >> services/api/app.py

# Edit a React component in the frontend
echo "<div>New Component</div>" >> apps/web/src/components/NewComponent.tsx

# Both changes will trigger live reload automatically
```

## File Structure

```
docker/
├── services/
│   ├── Dockerfile              # API service configuration
│   └── entrypoint.sh         # Enhanced startup script with file watching
├── apps/
│   ├── Dockerfile              # Frontend service configuration  
│   └── start.sh               # Enhanced startup script with Next.js hot reload
├── docker-compose.yml          # Main orchestration file
└── README.md                  # This documentation
```

## Benefits

- **Instant Feedback**: Changes reflected immediately without manual restarts
- **Code Safety**: Non-destructive file watching to prevent accidental restarts
- **Performance**: Layer caching for faster builds and deployments
- **Debugging**: Direct access to containers for troubleshooting
- **Portability**: Consistent development environment across machines
- **Scalability**: Easy service scaling for production deployment

## Production Considerations

For production deployment, consider:

1. **Disable Live Reload**: Remove file watching in production Dockerfiles
2. **Use Reverse Proxy**: Configure Nginx or similar for SSL termination
3. **Environment Variables**: Use `.env` files for configuration
4. **Resource Management**: Set appropriate CPU/memory limits
5. **Logging**: Centralize logs for easier monitoring
6. **Backup**: Regular database backups

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's running on ports 8000 or 3000
   lsof -i :8000
   lsof -i :3000
   ```

2. **Build Failures**
   ```bash
   # Rebuild with clean cache
   nerdctl compose build --no-cache
   nerdctl compose up
   ```

3. **Health Check Failures**
   ```bash
   # Check individual service status
   curl http://localhost:8000/health
   curl http://localhost:3000/api/health
   ```

4. **Live Reload Not Working**
   ```bash
   # Verify inotify tools are installed
   api_container=$(nerdctl compose ps -q api)
   nerdctl exec $api_container inotifywait --version
   ```

### Getting Help

1. **Check Logs**: `nerdctl compose logs -f api web`
2. **Container Shell**: `nerdctl compose exec <service_name> bash`
3. **Build Cache**: Clear with `--no-cache` flag
4. **Network Issues**: Verify service dependencies are running

## Configuration

### Environment Variables

The following environment variables can be set:

- `DEBUG=true/false` - Enable/disable debug mode
- `ENVIRONMENT=development/production` - Set deployment environment
- `PYTHONPATH` - Python module search path
- `NODE_ENV=development/production` - Node.js environment
- `NEXT_TELEMETRY_DISABLED=true/false` - Disable Next.js telemetry

### Health Checks

Both services include health checks:

- **API**: `GET /health`
- **Frontend**: `GET /api/health`

These are used by Docker to determine service readiness.

## Customization

### Adding New Services

To add a new service, create:
1. A Dockerfile in the appropriate directory
2. Add to `docker-compose.yml`
3. Update dependencies if needed

### Modifying Port Mappings

Change port mappings in `docker-compose.yml`:

```yaml
ports:
  - "8000:8000"  # Host:Container
  - "3000:3000"
```

### Scaling Services

For production scaling, use Docker's native scaling:

```bash
# Scale API to 3 instances
nerdctl compose up --scale api=3

# Scale web to 2 instances
nerdctl compose up --scale web=2
```

## License

This Docker configuration is provided as part of the QURAN AI project. Modifications should follow the project's licensing guidelines.

## Support

For Docker-related issues, refer to this README or contact the development team.
