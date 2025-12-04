# =============================================================================
# Obscura V2 - Zcash Payments Module Dockerfile
# =============================================================================
# Multi-stage build for Zcash payments with lightwalletd integration
# 
# Components:
# - Python FastAPI payments service
# - zecwallet-cli light client (pre-built binary)
# - gRPC client for lightwalletd communication
# =============================================================================

# -----------------------------------------------------------------------------
# Python application with Zcash client
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Create non-root user for security
ARG APP_USER=obscura
ARG APP_UID=1000
RUN useradd --create-home --uid ${APP_UID} ${APP_USER}

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libssl3 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install grpcurl for testing lightwalletd connection (detect architecture)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then \
        GRPC_ARCH="linux_arm64"; \
    else \
        GRPC_ARCH="linux_x86_64"; \
    fi && \
    curl -sSL "https://github.com/fullstorydev/grpcurl/releases/download/v1.8.9/grpcurl_1.8.9_${GRPC_ARCH}.tar.gz" \
    | tar -xzf - -C /usr/local/bin grpcurl && \
    chmod +x /usr/local/bin/grpcurl

# Download pre-built zecwallet-cli binary (much faster than building from source)
# Note: For production on ARM64 (Apple Silicon), you may need to build from source
# or use x86_64 emulation. For now, we'll make CLI optional and use gRPC directly.
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then \
        echo "ARM64 detected - zecwallet-cli will run in mock mode (no native ARM build available)" && \
        touch /usr/local/bin/zecwallet-cli && chmod +x /usr/local/bin/zecwallet-cli; \
    else \
        curl -sSL "https://github.com/adityapk00/zecwallet-light-cli/releases/download/v1.7.9/linux-zecwallet-cli-v1.7.9.zip" -o /tmp/zecwallet.zip && \
        unzip /tmp/zecwallet.zip -d /tmp && \
        mv /tmp/linux-zecwallet-cli-v1.7.9/zecwallet-cli /usr/local/bin/zecwallet-cli && \
        chmod +x /usr/local/bin/zecwallet-cli && \
        rm -rf /tmp/zecwallet.zip /tmp/linux-zecwallet-cli-v1.7.9; \
    fi

WORKDIR /app

# Copy and install Python dependencies first (for layer caching)
COPY payments/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ ./shared/

# Copy payments module
COPY payments/ ./payments/

# Create directories for wallet data and logs
RUN mkdir -p /app/data/wallet /app/logs \
    && chown -R ${APP_USER}:${APP_USER} /app

# Switch to non-root user
USER ${APP_USER}

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ZECWALLET_CLI_PATH=/usr/local/bin/zecwallet-cli \
    LIGHTWALLETD_URL=https://mainnet.lightwalletd.com:9067 \
    ZCASH_NETWORK=mainnet \
    WALLET_DATA_DIR=/app/data/wallet

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the service port
EXPOSE 8000

# Start the payments service
CMD ["uvicorn", "payments.main:app", "--host", "0.0.0.0", "--port", "8000"]
