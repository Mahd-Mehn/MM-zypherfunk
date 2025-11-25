# 🚀 Obscura V2 - Deployment Guide

Complete deployment guide for the multi-exchange trading infrastructure.

## 📋 Pre-Deployment Checklist

### 1. Infrastructure Requirements
- [ ] Python 3.9+ installed
- [ ] PostgreSQL 14+ (optional, for order history)
- [ ] Redis 6+ (optional, for caching)
- [ ] Domain name configured (for production)
- [ ] SSL certificates (Let's Encrypt recommended)
- [ ] Cloud provider account (AWS/GCP/Azure/Vercel)

### 2. API Credentials
- [ ] Binance API key + secret (spot trading enabled)
- [ ] Coinbase Advanced Trade credentials
- [ ] Ethereum/Base private key (funded for gas)
- [ ] Starknet account + private key
- [ ] NEAR account with MPC access
- [ ] Nillion API key (for secret storage)

### 3. Security Setup
- [ ] API keys stored in Nillion or secret manager
- [ ] Private keys never committed to git
- [ ] Environment variables configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] IP whitelisting (production)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                 │
│              MM-Obscura on Vercel/BOS               │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────┐
│              API Gateway (FastAPI)                   │
│         Load Balancer + Rate Limiting                │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│         Trading Orchestrator (Conductor)             │
│    AWS ECS / Google Cloud Run / Railway              │
└─────┬──────────┬──────────┬──────────┬──────────────┘
      │          │          │          │
┌─────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
│ Binance │ │Coinbase│ │Uniswap │ │Starknet │
└─────────┘ └────────┘ └────────┘ └─────────┘
```

## 📦 Deployment Options

### Option 1: Docker Compose (Easiest)

Perfect for: Development, staging, small production

```bash
cd obscura-v2/backend

# 1. Create environment file
cp .env.example .env
nano .env  # Fill in your credentials

# 2. Build and run
docker-compose up -d

# 3. Check logs
docker-compose logs -f conductor

# 4. Test
curl http://localhost:8001/health
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  conductor:
    build: ./conductor
    ports:
      - "8001:8001"
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    restart: always
    
  citadel:
    build: ./citadel
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: always
    
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: obscura
      POSTGRES_USER: obscura
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Option 2: AWS ECS (Production)

Perfect for: Large-scale production, high availability

#### Step 1: Build and Push Docker Image

```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# 2. Build image
docker build -t obscura-conductor ./conductor

# 3. Tag image
docker tag obscura-conductor:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/obscura-conductor:latest

# 4. Push image
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/obscura-conductor:latest
```

#### Step 2: Create ECS Task Definition

```json
{
  "family": "obscura-conductor",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "conductor",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/obscura-conductor:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "ENABLE_METRICS", "value": "true"}
      ],
      "secrets": [
        {
          "name": "BINANCE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:obscura/binance-key"
        },
        {
          "name": "BINANCE_API_SECRET",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:obscura/binance-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/obscura-conductor",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 3: Create ECS Service

```bash
aws ecs create-service \
  --cluster obscura-cluster \
  --service-name conductor \
  --task-definition obscura-conductor:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/obscura-conductor/abc123,containerName=conductor,containerPort=8001"
```

### Option 3: Google Cloud Run (Serverless)

Perfect for: Pay-per-use, automatic scaling

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/obscura-conductor ./conductor

# 2. Deploy to Cloud Run
gcloud run deploy obscura-conductor \
  --image gcr.io/PROJECT_ID/obscura-conductor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars LOG_LEVEL=INFO \
  --set-secrets BINANCE_API_KEY=obscura-binance-key:latest \
  --set-secrets BINANCE_API_SECRET=obscura-binance-secret:latest \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10
```

### Option 4: Railway (Fastest)

Perfect for: Quick deployment, prototypes

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
cd obscura-v2/backend/conductor
railway init

# 4. Add environment variables in Railway dashboard
# Then deploy:
railway up
```

## 🔐 Secret Management

### AWS Secrets Manager

```bash
# Store API keys
aws secretsmanager create-secret \
  --name obscura/binance-key \
  --secret-string "your-binance-api-key"

aws secretsmanager create-secret \
  --name obscura/binance-secret \
  --secret-string "your-binance-secret"

# Retrieve in code
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='obscura/binance-key')
api_key = response['SecretString']
```

### Nillion (Recommended for Production)

```python
from citadel.nillion_client import nillion

# Store credentials securely
async def store_cex_credentials():
    key_id = await nillion.store_secret(
        binance_api_key,
        "binance-api-key"
    )
    
    secret_id = await nillion.store_secret(
        binance_api_secret,
        "binance-api-secret"
    )
    
    return key_id, secret_id

# Retrieve when needed
async def get_cex_credentials(key_id, secret_id):
    api_key = await nillion.retrieve_secret(key_id)
    api_secret = await nillion.retrieve_secret(secret_id)
    return api_key, api_secret
```

## 📊 Monitoring Setup

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'conductor'
    static_configs:
      - targets: ['conductor:9090']
  
  - job_name: 'citadel'
    static_configs:
      - targets: ['citadel:9090']
```

### Application Logs

```python
import logging
import sys

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "module":"%(name)s", "message":"%(message)s"}',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("obscura.conductor")
```

## 🧪 Testing Before Production

### 1. Integration Tests

```bash
# Test all exchanges with testnet credentials
export BINANCE_TESTNET=true
python test_trading.py
```

### 2. Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f load_test.py --host http://localhost:8001
```

**load_test.py**:
```python
from locust import HttpUser, task, between

class TradingUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_price(self):
        self.client.get("/price/BTC/USDT?side=buy")
    
    @task(2)
    def get_balance(self):
        self.client.get("/balance?asset=BTC")
    
    @task(1)
    def execute_trade(self):
        self.client.post("/execute", json={
            "user_id": "test_user",
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "market",
            "amount": "0.001",
            "strategy": "best_price"
        })
```

### 3. Security Audit

```bash
# Check for vulnerabilities
pip install safety
safety check

# Scan for secrets in code
pip install trufflehog
trufflehog filesystem ./ --json

# Static analysis
pip install bandit
bandit -r . -f json
```

## 🚦 Production Readiness

### Essential Checklist

- [ ] All tests passing
- [ ] Load testing completed (handle expected traffic)
- [ ] Monitoring and alerting configured
- [ ] Logging aggregation setup
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] Rate limiting configured
- [ ] DDOS protection enabled
- [ ] SSL/TLS certificates installed
- [ ] Environment variables secured
- [ ] Database migrations tested
- [ ] Rollback procedure documented
- [ ] On-call rotation established

## 🔧 Troubleshooting

### Common Issues

#### 1. Exchange Connection Fails
```bash
# Check credentials
python -c "from exchanges.binance_connector import BinanceConnector; import asyncio; asyncio.run(BinanceConnector({'api_key': 'test', 'api_secret': 'test'}).initialize())"

# Test network connectivity
curl -I https://api.binance.com/api/v3/ping
```

#### 2. High Memory Usage
```bash
# Monitor memory
docker stats conductor

# Reduce concurrent connections
export MAX_CONCURRENT_REQUESTS=50
```

#### 3. Slow Response Times
```bash
# Enable Redis caching
export REDIS_URL=redis://localhost:6379
export CACHE_TTL=30  # 30 seconds

# Check database queries
export LOG_SQL=true
```

## 📈 Scaling Strategy

### Horizontal Scaling

```bash
# AWS ECS - Increase desired count
aws ecs update-service \
  --cluster obscura-cluster \
  --service conductor \
  --desired-count 5

# Cloud Run - Auto-scaling
gcloud run services update obscura-conductor \
  --min-instances 2 \
  --max-instances 20 \
  --concurrency 100
```

### Database Scaling

```sql
-- Add read replicas
-- Configure connection pooling
-- Implement query caching
-- Use database partitioning for large tables
```

## 🎯 Performance Optimization

1. **Connection Pooling**: Reuse exchange connections
2. **Caching**: Redis for price data (30s TTL)
3. **Async Operations**: Use asyncio for concurrent requests
4. **Load Balancing**: Distribute traffic across multiple instances
5. **CDN**: Cloudflare for static assets and DDoS protection

## 📞 Support & Maintenance

- **Health Check Endpoint**: `GET /health`
- **Metrics Endpoint**: `GET /metrics` (Prometheus format)
- **Log Aggregation**: CloudWatch/Stackdriver/DataDog
- **Alerting**: PagerDuty/Opsgenie for critical issues

---

**Next Steps**: After deployment, monitor for 24-48 hours and gradually increase traffic.
