# EvalForge Deployment Guide

This guide covers two deployment targets:
1. **Containerized Deployment (Docker Compose)** for on-prem or single-server staging.
2. **Production AWS Architecture** for high-availability enterprise environments.

---

## 1. Containerized Deployment via Docker Compose

### Prerequisites
- Docker Engine & Docker Compose
- Minimum 2 CPU cores, 4 GB RAM

### Steps
```bash
# Clone and enter repo
git clone <repo_url>
cd evalforge

# Copy and configure environment variables
cp .env.example .env

# Build and start services
docker compose up -d --build

# Check status
docker compose ps

# View application logs
docker compose logs -f backend
```

Services exposed:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI Backend & Interactive API Docs**: `http://localhost:8000/api/v1/docs`
- **PostgreSQL Database**: `localhost:5432`
- **Redis Cache & Broker**: `localhost:6379`

---

## 2. Enterprise AWS Deployment Path

For enterprise deployments with SLA guarantees, decouple stateful storage from stateless compute:

```
                            [ Amazon Route 53 (DNS) ]
                                        │
                         [ AWS CloudFront (CDN + SSL) ]
                                        │
           ┌────────────────────────────┴───────────────────────────┐
           │                                                        │
[ Amazon S3 (Static / Next.js) ]              [ Application Load Balancer (ALB) ]
                                                                    │
                                            ┌───────────────────────┴───────────────────────┐
                                            │                                               │
                               [ Amazon ECS Fargate (FastAPI) ]        [ Amazon ECS Fargate (Celery Workers) ]
                                            │                                               │
                                            └───────────────────────┬───────────────────────┘
                                                                    │
                                        ┌───────────────────────────┴───────────────────────────┐
                                        │                                                       │
                       [ Amazon RDS PostgreSQL + pgvector ]                     [ Amazon ElastiCache (Redis) ]
```

### AWS Managed Services Mapping
1. **Frontend**:
   - Host Next.js build output in **AWS Amplify Hosting** or **Amazon S3** fronted by **Amazon CloudFront** for global caching and HTTPS termination.
2. **Backend API**:
   - Package `docker/Dockerfile.backend` into **Amazon ECR (Elastic Container Registry)**.
   - Run stateless FastAPI tasks on **AWS Fargate** behind an **Application Load Balancer (ALB)** with Auto Scaling based on CPU/Request count.
3. **Background Worker Engine**:
   - Run Celery workers on dedicated **AWS Fargate** containers scaling on Redis queue depth (`approximate_number_of_messages`).
4. **Database**:
   - **Amazon RDS for PostgreSQL (Engine 16)** with the `vector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
   - Enable Multi-AZ deployment for high availability and automatic failover.
5. **Cache & Task Broker**:
   - **Amazon ElastiCache for Redis (Cluster mode)** with Multi-AZ replication.
6. **Secrets & Credentials Management**:
   - Store API keys (OpenAI, Anthropic, Gemini, JWT secret) in **AWS Secrets Manager** or **AWS Systems Manager Parameter Store**; inject securely via ECS task definitions.
7. **Observability & Logging**:
   - Export structured logs to **Amazon CloudWatch Logs** and configure **AWS X-Ray** / OpenTelemetry for distributed tracing.

---

## 3. Database Migrations (Alembic)

To apply or generate schema revisions:
```bash
cd backend
alembic upgrade head
```
