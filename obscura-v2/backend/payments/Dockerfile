# =============================================================================
# Obscura V2 - Zcash Payments Module Dockerfile
# =============================================================================
# Multi-stage build for Zcash payments with lightwalletd integration
# 
# Components:
# - Python FastAPI payments service
# - zecwallet-cli light client
# - gRPC client for lightwalletd communication
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build zecwallet-cli from source (or download binary)
# -----------------------------------------------------------------------------
FROM rust:1.75-bookworm AS zecwallet-builder

WORKDIR /build

# Install dependencies for building zecwallet-cli
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone and build zecwallet-cli (light client)
# Using zecwallet-light-cli which connects to lightwalletd
RUN git clone --depth 1 --branch v1.8.8 https://github.com/adityapk00/zecwallet-light-cli.git \
    && cd zecwallet-light-cli \
    && cargo build --release

# -----------------------------------------------------------------------------
# Stage 2: Python application with Zcash client
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
    grpcurl \
    && rm -rf /var/lib/apt/lists/*

# Install grpcurl for testing lightwalletd connection
RUN curl -sSL https://github.com/fullstorydev/grpcurl/releases/download/v1.8.9/grpcurl_1.8.9_linux_x86_64.tar.gz \
    | tar -xzf - -C /usr/local/bin grpcurl

# Copy zecwallet-cli from builder stage
COPY --from=zecwallet-builder /build/zecwallet-light-cli/target/release/zecwallet-cli /usr/local/bin/zecwallet-cli
RUN chmod +x /usr/local/bin/zecwallet-cli

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
