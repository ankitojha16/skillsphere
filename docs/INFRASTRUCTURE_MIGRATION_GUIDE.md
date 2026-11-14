# SkillSphere Infrastructure Migration Guide
## Transitioning from Serverless Vercel to Production Containerized Platforms (AWS ECS, GCP Cloud Run, Kubernetes)

---

## 1. Executive Summary & Migration Motivation

SkillSphere is currently deployed on **Vercel** serverless functions with a managed **Supabase PostgreSQL** instance and Redis caching. While this architecture provides rapid developer iteration and zero-maintenance scaling for early-stage workloads, scaling to **10,000 active concurrent users** and meeting **Five-Nines (99.999%) availability** requires dedicated containerized infrastructure.

### Limitations of Current Serverless Arrangement at 10K Concurrency:
1. **Connection Exhaustion**: Serverless function bursts generate hundreds of ephemeral connections, requiring heavy reliance on PgBouncer.
2. **Cold Starts**: Cold starts during sudden traffic spikes degrade p99 response times beyond 1,500ms.
3. **Execution Limits & Background Tasks**: HTTP request timeouts (15s–60s) prohibit long-running asynchronous orchestration (PDF compilation, batch notification dispatch) without specialized queues.
4. **Network & Region Lock**: Multi-region failover and fine-grained VPC security controls require dedicated cloud VPCs.

This guide provides concrete, copy-paste ready infrastructure definitions, migration execution runbooks, DNS cutover procedures, and comparative cost models for migrating SkillSphere to **AWS ECS Fargate**, **GCP Cloud Run**, and **Kubernetes (EKS / GKE)**.

---

## 2. Docker Container Baseline

SkillSphere utilizes a multi-stage production Docker image adhering to OCI standards, non-root user execution, and fast startup:

```dockerfile
# Dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Production Stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 1001 -m -s /bin/bash appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Health check using stateless liveness probe
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health/live/ || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gthread", "--threads", "4", "--timeout", "30", "--access-logfile", "-"]
```

---

## 3. Target Platform 1: AWS ECS Fargate

### Architecture
- **Ingress**: AWS Application Load Balancer (ALB) across 3 Availability Zones with ACM TLS certificate.
- **Compute**: ECS Fargate service running behind ALB target group.
- **Database**: Amazon Aurora PostgreSQL (Multi-AZ with read replica and RDS Proxy).
- **Cache**: Amazon ElastiCache for Valkey / Redis (Cluster mode enabled).
- **Secrets**: AWS Secrets Manager integrated via ECS Task Definition secret references.

### ECS Task Definition (`task-definition.json`)
```json
{
  "family": "skillsphere-production",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/skillsphere-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::123456789012:role/skillsphere-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/skillsphere:v17.0.0",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DJANGO_SETTINGS_MODULE", "value": "config.settings"},
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "PORT", "value": "8000"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:skillsphere/prod:SECRET_KEY::"},
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:skillsphere/prod:DATABASE_URL::"},
        {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:skillsphere/prod:REDIS_URL::"},
        {"name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:skillsphere/prod:GEMINI_API_KEY::"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health/live/ || exit 1"],
        "interval": 15,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/skillsphere-prod",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Auto-Scaling Policies
- **Target Metric**: ALB Request Count Per Target = 350 requests/min.
- **CPU Threshold**: Scale up when average CPU exceeds 65% for 2 consecutive 60-second periods.
- **Min Tasks**: 10 (baseline multi-AZ capacity).
- **Max Tasks**: 60 (peak 10,000 concurrent capacity).

---

## 4. Target Platform 2: GCP Cloud Run

### Architecture
- **Compute**: Fully managed Google Cloud Run (Generation 2 execution environment).
- **Ingress**: Cloud Load Balancing with Google-managed multi-region SSL certificates.
- **Database**: Cloud SQL for PostgreSQL (Enterprise Plus edition, high availability enabled across 2 zones).
- **VPC Connector**: Serverless VPC Access connector for zero-latency private IP routing.
- **Caching**: Memorystore for Redis (Standard Tier with replication).
- **Secrets**: Google Cloud Secret Manager mounted as environment variables.

### Cloud Run Service Configuration (`service.yaml`)
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: skillsphere-prod
  namespace: 'skillsphere'
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/launch-stage: GA
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "8"
        autoscaling.knative.dev/maxScale: "50"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/vpc-access-connector: "projects/skillsphere-prod/locations/us-central1/connectors/skillsphere-vpc-conn"
        run.googleapis.com/vpc-access-egress: "private-ranges-only"
        run.googleapis.com/execution-environment: "gen2"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 60
      serviceAccountName: skillsphere-cloudrun-sa@skillsphere-prod.iam.gserviceaccount.com
      containers:
      - image: gcr.io/skillsphere-prod/skillsphere:v17.0.0
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "config.settings"
        - name: ENVIRONMENT
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: skillsphere-secret-key
              key: latest
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: skillsphere-database-url
              key: latest
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: skillsphere-redis-url
              key: latest
        startupProbe:
          httpGet:
            path: /health/live/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health/live/
            port: 8000
          periodSeconds: 10
          timeoutSeconds: 3
```

---

## 5. Target Platform 3: Kubernetes (EKS / GKE)

### Production Kubernetes Manifests

#### 1. Deployment (`k8s/deployment.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skillsphere-web
  namespace: skillsphere
  labels:
    app: skillsphere
    tier: web
spec:
  replicas: 12
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  selector:
    matchLabels:
      app: skillsphere
      tier: web
  template:
    metadata:
      labels:
        app: skillsphere
        tier: web
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: ["skillsphere"]
              topologyKey: "topology.kubernetes.io/zone"
      containers:
      - name: skillsphere
        image: ghcr.io/ankitojha16/skillsphere:v17.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1500m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health/live/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 2
        envFrom:
        - configMapRef:
            name: skillsphere-config
        - secretRef:
            name: skillsphere-secrets
```

#### 2. Horizontal Pod Autoscaler (`k8s/hpa.yaml`)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: skillsphere-web-hpa
  namespace: skillsphere
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: skillsphere-web
  minReplicas: 10
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 65
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### 3. Ingress & TLS (`k8s/ingress.yaml`)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: skillsphere-ingress
  namespace: skillsphere
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "20m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "5"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "30"
    nginx.ingress.kubernetes.io/enable-real-ip: "true"
spec:
  tls:
  - hosts:
    - skillsphere.com
    secretName: skillsphere-tls-cert
  rules:
  - host: skillsphere.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: skillsphere-service
            port:
              number: 80
```

---

## 6. Zero-Downtime Migration Execution Plan

To migrate from the current Vercel production deployment to the target containerized platform without downtime or data corruption, follow this phased execution plan:

```
[Phase A: Infra Provisioning]  --->  [Phase B: DB Read-Replica Sync]  --->  [Phase C: Dual-Run Verification]
                                                                                     |
[Phase F: Post-Migration Teardown] <-- [Phase E: DB Primary Cutover] <-- [Phase D: Canary Traffic Routing]
```

### Step 1: Pre-Migration Checklist (-7 Days)
- [ ] Deploy target cluster (ECS, Cloud Run, or Kubernetes) in primary and secondary availability zones.
- [ ] Verify database network peering and security groups.
- [ ] Reduce DNS record TTL on Route53 / Cloudflare from 86,400s (24h) to **300 seconds (5m)**.
- [ ] Complete full regression testing on target staging environment using the identical container image.
- [ ] Verify zero schema drift between Django migrations and PostgreSQL schema.

### Step 2: Database Synchronization (-24 Hours)
- Setup continuous logical replication or live streaming replica between current database and target production database cluster.
- Run validation script comparing row counts across all primary tables:
  - `auth_user`, `users_studentprofile`, `courses_course`, `courses_lesson`, `courses_enrollment`, `certificates_certificate`.

### Step 3: Canary Traffic & Verification (-2 Hours)
- Route 5% of incoming traffic to the new container cluster via Cloudflare Weighted Load Balancing.
- Monitor `/health/live/`, `/health/ready/`, and `/api/metrics/`:
  - Error rate must remain $< 0.01\%$.
  - p95 latency must remain $< 150\text{ms}$.

### Step 4: Primary DNS & DB Cutover (T = 0)
1. **Maintenance Window Flag**: Activate ultra-brief (10–15s) maintenance mode or read-only replica routing in Django settings (`MAINTENANCE_MODE=True`).
2. **Promote Database**: Promote the target PostgreSQL instance to primary master.
3. **Switch DNS**: Update DNS CNAME / A records to point 100% of user traffic to the ALB / Ingress IP.
4. **Disable Maintenance**: Deactivate maintenance flag on target containers.
5. **Verify**: Run smoke tests against `/health/ready/` and verify learner login and course enrollment.

### Step 5: Rollback Decision Gates
If any of the following occur within 60 minutes post-cutover:
- Error rate $\ge 1.0\%$ for $> 3$ consecutive minutes.
- Database connection pool exhaustion with $> 95\%$ utilization.
- Critical data mutation failure on user courses or certificates.
**Action**: Immediately revert DNS A/CNAME record back to Vercel CNAME (`cname.vercel-dns.com`). Target TTL of 300s ensures restoration within 5 minutes.

---

## 7. Cost & Capacity Comparison (10,000 Concurrent Users)

| Dimension | Current Vercel Serverless | AWS ECS Fargate | GCP Cloud Run | Kubernetes (EKS / GKE) |
| :--- | :--- | :--- | :--- | :--- |
| **Compute Configuration** | Serverless Edge & Lambdas | 15–35 tasks (1 vCPU, 2GB) | 12–30 instances (2 vCPU, 2GB) | 12–35 Pods across 4 node instances |
| **Database Tier** | Supabase Pro ($25/mo) | AWS Aurora PostgreSQL (db.r6g.xlarge) | Cloud SQL Enterprise Plus (4 vCPU, 16GB) | RDS Aurora / Cloud SQL |
| **Connection Pooling** | Supabase PgBouncer | AWS RDS Proxy | Cloud SQL Auth Proxy / Built-in | PgBouncer Deployment |
| **Monthly Compute Cost** | \$180 – \$350 (invocations) | \$380 – \$620 | \$320 – \$540 | \$450 – \$720 (nodes + control plane) |
| **Monthly Database Cost** | \$25 – \$75 | \$280 – \$410 | \$260 – \$390 | \$280 – \$410 |
| **Monthly Cache Cost** | Upstash Serverless (\$30) | ElastiCache Redis (\$110) | Memorystore Redis (\$95) | Redis Operator / Managed (\$95) |
| **Total Estimated Monthly** | **\$235 – \$455** | **\$770 – \$1,140** | **\$675 – \$1,025** | **\$825 – \$1,225** |
| **Five-Nines SLA Suitability** | ⚠️ Limited by Edge/FaaS SLAs (99.95%) | ✅ High (Multi-AZ ALB + Aurora HA) | ✅ High (Regional Cloud Run + HA DB) | ✅ Highest (Multi-AZ Pod Anti-affinity) |
| **Recommendation** | Ideal for Dev / Beta ($<1,000$ active) | Recommended for Enterprise AWS stacks | Recommended for cost-effective 10K scale | Recommended if company manages K8s |

---

## 8. Conclusion & Recommendation

SkillSphere's Phase 17 codebase has been built with **server and provider independence**:
- Configuration is driven entirely through 12-factor environment variables (`settings.py`).
- Storage, cache, task queues, and circuit breakers use abstract, pluggable interfaces.
- Standard health probes (`/health/live/`, `/health/ready/`) and metrics endpoints (`/api/metrics/`) are natively supported.

When scaling past 1,000 concurrent peak learners or transitioning to institutional enterprise contracts, SkillSphere is fully architected to migrate to **GCP Cloud Run** (fastest, most cost-effective) or **AWS ECS Fargate** (most widely adopted enterprise standard) within a 4-hour deployment window.
