# Frontend Service Dockerfile with Hot Reload
FROM node:20-alpine

# Install additional packages for hot reload
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

WORKDIR /app

# Copy package files
COPY apps/web/package.json apps/web/package-lock.json* ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy rest of application
COPY apps/web/ .

# Create nextjs user
RUN adduser -D -u 1001 nextjs && chown -R nextjs:nextjs /app
USER nextjs

EXPOSE 3000

# Enhanced startup script with Next.js file watcher
COPY --chown=nextjs:nextjs start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

ENTRYPOINT ["/usr/local/bin/start.sh"]