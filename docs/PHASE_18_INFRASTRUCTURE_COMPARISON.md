# SkillSphere Phase 18 — Cloud Infrastructure Architecture Comparison

## 1. Executive Summary & Workload Assumptions

To scale SkillSphere to **10,000 concurrent active users (CCU)** and support a horizontally scalable Django application with multi-instance background workers, shared database, cache, and object storage, this document compares three major cloud architecture options:

1. **Option A: AWS ECS with Fargate** (Recommended Primary Architecture)
2. **Option B: Google Cloud Run with Managed Supporting Services** (Viable Alternative Architecture)
3. **Option C: Managed Kubernetes (AWS EKS / GCP GKE)** (Evaluated & Disrecommended for Current Scope)

---

### Workload Assumptions for Capacity Modeling:
- **Concurrency**: 10,000 Concurrently Connected Users (Peak CCU)
- **User Activity Distribution**:
  - $50\%$ Browsing & Discovery (think time 4s $\rightarrow$ 0.25 requests/sec per user)
  - $35\%$ Active Studying & Quiz Submissions (think time 5s $\rightarrow$ 0.2 requests/sec per user)
  - $15\%$ Interactive / Heavy Content (think time 8s $\rightarrow$ 0.125 requests/sec per user)
- **Peak Request Throughput**:
  $$\text{RPS}_{\text{peak}} = (10,000 \times 0.50 \times 0.25) + (10,000 \times 0.35 \times 0.20) + (10,000 \times 0.15 \times 0.125) = 1,250 + 700 + 187.5 \approx \mathbf{2,137.5\text{ RPS}}$$
- **Edge Cache Offload**: Static assets, cached course pages, and public certificates offloaded via CDN ($60\%$ cache hit ratio), leaving approximately **$855\text{ dynamic RPS}$** reaching the Django container fleet.
- **Dynamic Request Budget**:
  - Average Django dynamic request latency: $45\text{ ms}$ ($0.045\text{ s}$).
  - Required container concurrency capacity:
    $$C_{\text{web}} = 855\text{ RPS} \times 0.045\text{ s} \approx \mathbf{38.5\text{ concurrent executions}}$$
- **Container Allocation**: Each task configured with 2 vCPUs, 4 GB RAM running Gunicorn with 4 workers and 4 threads ($16\text{ worker threads/task}$). Fleet requires approximately **$10\text{ to }16\text{ tasks}$** under peak load with headroom for spikes.

---

## 2. Comprehensive 12-Dimension Evaluation Matrix

| Evaluation Dimension | Option A: AWS ECS Fargate | Option B: GCP Cloud Run | Option C: Managed Kubernetes (EKS/GKE) |
| :--- | :--- | :--- | :--- |
| **1. Horizontal Autoscaling** | Target tracking on CPU/Memory and ALB Request Count. Scales tasks in 45–90s. | Sub-second request-driven autoscaling. Scales from 0 to hundreds of instances in seconds. | HPA (Horizontal Pod Autoscaler) + Cluster Autoscaler / Karpenter. Complex tuning required. |
| **2. Multi-Zone Availability** | Native Multi-AZ distribution across 3 AZs with ALB cross-zone balancing. | Regional multi-zone distribution managed entirely by Google transparently. | Multi-AZ worker nodes; requires pod anti-affinity and topology spread constraints. |
| **3. Database Connectivity** | AWS RDS PostgreSQL with RDS Proxy / PgBouncer in same VPC private subnets (< 1.5ms latency). | Serverless VPC Access connector to Cloud SQL. Can encounter cold start latency on connection spikes. | CNI native VPC IP allocation. Direct connection to RDS or Cloud SQL via private subnets. |
| **4. Redis Availability** | AWS ElastiCache for Redis (Multi-AZ with automatic failover and read replicas). | Google Cloud Memorystore for Redis (Standard Tier with cross-zone HA). | Redis Operator on-cluster or external managed ElastiCache/Memorystore. |
| **5. Durable Task Workers** | Dedicated ECS Fargate Worker Service polling queue continuously without request timeouts. | Cloud Tasks / Cloud Run Jobs. Background daemons require persistent CPU allocation ($$$). | Native Kubernetes Deployments / StatefulSets for continuous background worker loops. |
| **6. WebSocket Support** | Native support via Application Load Balancer and ECS Fargate gunicorn/uvicorn. | Cloud Run WebSockets supported (up to 60-min connection timeout), but concurrency pricing applies. | Native WebSocket support via Ingress Controller (NGINX / Traefik / Envoy). |
| **7. Object Storage** | Amazon S3 with IAM Role authentication (zero static keys) and VPC S3 Gateway Endpoints. | Google Cloud Storage (GCS) with Workload Identity Federation. | CSI driver for S3 or standard SDK integration with S3/GCS. |
| **8. CDN Integration** | Amazon CloudFront with Origin Access Control (OAC) and AWS WAF integration. | Google Cloud CDN with Cloud Armor security policies. | CloudFront, Fastly, or Cloudflare pointing to LoadBalancer Ingress. |
| **9. Monitoring** | CloudWatch Container Insights, AWS X-Ray, and native Prometheus scraping via ADOT. | Google Cloud Monitoring (Cloud Logging, Error Reporting, Trace) with native OpenTelemetry. | Prometheus Operator, Grafana, Jaeger, FluentBit. Maximum observability control. |
| **10. Recovery Capabilities** | Automated task replacement on unhealthy status, Multi-AZ task healing, zero-downtime rolling deploys. | Instant traffic migration across revisions, automatic container healing and rollback. | Self-healing pods, replica sets, cluster node draining, complex disaster recovery. |
| **11. Operational Complexity** | **Low to Moderate**: Serverless compute, no EC2 instances to patch, native IAM and VPC security. | **Low**: Fully managed serverless container platform, minimal networking overhead. | **High**: Control plane upgrades, CNI networking, ingress controllers, RBAC, node pooling, storage classes. |
| **12. Five-Nines Feasibility** | Achievable with Multi-AZ Fargate + Multi-AZ RDS + ElastiCache + CloudFront. | Achievable with Regional Cloud Run + HA Cloud SQL + Memorystore + Cloud CDN. | Achievable, but higher risk of human error due to Kubernetes configuration sprawl. |

---

## 3. Cost Evaluation Across Scale Tiers

*Assumptions: ap-south-1 (Mumbai) / asia-south1 pricing. Compute: Fargate ($0.04048/vCPU-hr, $0.004445/GB-hr). RDS Multi-AZ + ElastiCache Multi-AZ + CloudFront Egress.*

### 3.1 Tier 1: 1,000 Concurrent Active Users (~85 dynamic RPS)
- **AWS ECS Fargate**:
  - Web: 2 tasks (1 vCPU, 2 GB) = \$65/mo
  - Worker: 2 tasks (1 vCPU, 2 GB) = \$65/mo
  - RDS db.t4g.medium Multi-AZ = \$72/mo
  - ElastiCache cache.t4g.medium = \$38/mo
  - ALB + NAT Gateway + Data Transfer = \$65/mo
  - **Total Estimated AWS**: **~\$305 / month**
- **GCP Cloud Run**:
  - Cloud Run Web & Workers = \$110/mo
  - Cloud SQL db-custom-2-8 Regional = \$85/mo
  - Memorystore 2 GB = \$35/mo
  - Cloud CDN + Load Balancer = \$55/mo
  - **Total Estimated GCP**: **~\$285 / month**
- **Kubernetes (EKS)**:
  - EKS Control Plane = \$73/mo
  - 3x t4g.medium nodes = \$75/mo
  - RDS + Redis + ALB = \$210/mo
  - **Total Estimated EKS**: **~\$358 / month**

---

### 3.2 Tier 2: 5,000 Concurrent Active Users (~425 dynamic RPS)
- **AWS ECS Fargate**:
  - Web: 6 tasks (2 vCPU, 4 GB) = \$390/mo
  - Worker: 4 tasks (1 vCPU, 2 GB) = \$130/mo
  - RDS db.r6g.large Multi-AZ = \$260/mo
  - ElastiCache cache.r6g.large Multi-AZ = \$155/mo
  - ALB + NAT + CloudFront = \$140/mo
  - **Total Estimated AWS**: **~\$1,075 / month**
- **GCP Cloud Run**:
  - Cloud Run Web & Workers = \$490/mo
  - Cloud SQL db-custom-4-16 Regional = \$275/mo
  - Memorystore 5 GB = \$85/mo
  - Load Balancer + CDN = \$160/mo
  - **Total Estimated GCP**: **~\$1,010 / month**
- **Kubernetes (EKS)**:
  - EKS Control Plane (\$73) + 4x c6g.xlarge nodes (\$380) + RDS/Redis/ALB (\$555) = **~\$1,008 / month**

---

### 3.3 Tier 3: 10,000 Concurrent Active Users (~855 dynamic RPS)
- **AWS ECS Fargate**:
  - Web: 12 tasks (2 vCPU, 4 GB) = \$780/mo
  - Worker: 6 tasks (2 vCPU, 4 GB) = \$390/mo
  - RDS db.r6g.xlarge Multi-AZ with PgBouncer = \$520/mo
  - ElastiCache cache.r6g.large Multi-AZ = \$155/mo
  - ALB + NAT Gateways + CloudFront Data Egress (1.5 TB) = \$265/mo
  - CloudWatch Logs & Metrics = \$50/mo
  - **Total Estimated AWS**: **~\$2,160 / month**
- **GCP Cloud Run**:
  - Cloud Run Web & Workers = \$1,020/mo
  - Cloud SQL db-custom-8-32 Regional = \$550/mo
  - Memorystore 10 GB HA = \$170/mo
  - Cloud CDN + Load Balancer + Logging = \$380/mo
  - **Total Estimated GCP**: **~\$2,120 / month**
- **Kubernetes (EKS)**:
  - EKS Control Plane (\$73) + 6x c6g.2xlarge nodes (\$1,140) + RDS/Redis/ALB (\$940) = **~\$2,153 / month**

---

## 4. Final Architecture Recommendation

### Primary Recommendation: AWS ECS with Fargate
1. **Zero Node Maintenance**: Unlike Kubernetes, Fargate requires zero EC2 operating system patching, zero AMI maintenance, and zero Kubernetes control plane version upgrade toil.
2. **Native Long-Running Background Workers**: ECS Fargate runs our `python manage.py run_task_worker` daemon continuously without the invocation timeout constraints found in pure serverless functions.
3. **Enterprise Security & Compliance**: Native AWS IAM roles for tasks eliminate API credentials; VPC isolation protects the database, cache, and application tiers.

### Viable Alternative: Google Cloud Run with Managed Supporting Services
- Ideal for organizations heavily invested in Google Cloud Platform. Offers ultra-fast autoscaling and developer velocity, though background task daemons require dedicated Cloud Run Jobs or always-allocated CPU instances.

### Why Kubernetes (EKS/GKE) is NOT Recommended:
- SkillSphere is a cohesive Django 12-factor application, not a constellation of 50 decoupled microservices. Introducing Kubernetes creates unnecessary operational overhead (ingress controllers, CNI routing, cert-manager, cluster autoscaler, RBAC management) without delivering better performance or availability than ECS Fargate.
