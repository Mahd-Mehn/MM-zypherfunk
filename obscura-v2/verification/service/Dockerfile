# =============================================================================
# Obscura V2 - Verification Service Dockerfile
# =============================================================================
# Starknet ZK verification service for trading proofs
# Uses Bun for fast TypeScript execution
# =============================================================================

FROM oven/bun:1.1-alpine AS base

WORKDIR /app

# Install dependencies (don't use frozen lockfile as version may differ)
COPY package.json ./
RUN bun install --production

# =============================================================================
# Development Stage
# =============================================================================
FROM base AS development

# Install dev dependencies
RUN bun install

# Copy source
COPY . .

# Environment
ENV NODE_ENV=development
ENV PORT=3000

EXPOSE 3000

CMD ["bun", "run", "dev"]

# =============================================================================
# Build Stage
# =============================================================================
FROM base AS builder

# Install all dependencies for build
RUN bun install

# Copy source
COPY . .

# Build TypeScript
RUN bun run build

# =============================================================================
# Production Stage
# =============================================================================
FROM oven/bun:1.1-alpine AS production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S obscura && \
    adduser -S -D -H -u 1001 -s /sbin/nologin -G obscura obscura

# Copy production dependencies
COPY --from=base /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package.json ./

# Set ownership
RUN chown -R obscura:obscura /app

# Switch to non-root user
USER obscura

# Environment
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/v1/health || exit 1

EXPOSE 3000

CMD ["bun", "run", "start"]
