# SkillSphere Phase 18.4 — Itemized Cloud Infrastructure Cost Analysis

**Target Region**: AWS `ap-south-1` (Mumbai)  
**Currency**: USD ($)  
**Tax Regime**: 18% GST (Applicable for AWS India / AISPL billing accounts)  
**Legal Notice**: These figures are calculated engineering estimates based on published AWS on-demand pricing schedules (Q1 2025/2026). They do not constitute guaranteed bills and may fluctuate based on real data throughput, network egress, and compute autoscaling.

---

## 1. Workload Assumptions & Cost Parameters

The following operational assumptions govern this cost model:
- **Monthly Operating Hours**: 730 hours / month (24x7 continuous operation).
- **Public IPv4 Policy**: $0.005 / hour per IPv4 address ($3.65 / IP / month) mandated by AWS across all services (ALB and NAT EIPs).
- **Fargate Pricing (`ap-south-1`)**:
  - vCPU: $0.04048 per vCPU-hour
  - Memory: $0.004445 per GB-hour
- **NAT Gateway Pricing (`ap-south-1`)**:
  - Hourly fee: $0.045 per gateway-hour ($32.85 / gateway / month)
  - Data processing: $0.045 per GB processed
- **S3 Data Path**: Free S3 Gateway VPC Endpoint active; media uploads/downloads incur **$0.00** in NAT data processing fees. External NAT data is limited to container image pulls and Gemini AI API calls (~50 GB / mo).

---

## 2. Exhaustive Itemized Cost Model

### Comparison: Full High-Availability Staging vs. Cost-Optimized Staging vs. Peak Production (10k CCU)

| Cost Component | Pricing Basis | Model A: High-Availability Staging (3-NAT, db.t4g.med, 1vCPU) | Model B: Cost-Optimized Staging (1-NAT, db.t4g.small, 0.5vCPU) | Model C: Peak Production (10,000 CCU Target) |
| :--- | :--- | :--- | :--- | :--- |
| **ECS Fargate (Web)** | $0.04048/vCPU-hr + $0.004445/GB-hr | **$72.08** (2 tasks: 1 vCPU, 2GB) | **$36.04** (2 tasks: 0.5 vCPU, 1GB) | **$720.80** (20 tasks: 1 vCPU, 2GB) |
| **ECS Fargate (Worker)** | $0.04048/vCPU-hr + $0.004445/GB-hr | **$72.08** (2 tasks: 1 vCPU, 2GB) | **$36.04** (2 tasks: 0.5 vCPU, 1GB) | **$360.40** (10 tasks: 1 vCPU, 2GB) |
| **Application Load Balancer** | $0.0225/hr + $0.008/LCU-hr | **$17.60** (1 ALB + 0.2 LCU avg) | **$17.60** (1 ALB + 0.2 LCU avg) | **$65.00** (1 ALB + 6.0 LCU peak) |
| **Public IPv4 Addresses** | $0.005/hr ($3.65/IP-month) | **$21.90** (3 NAT EIPs + 3 ALB IPs)| **$14.60** (1 NAT EIP + 3 ALB IPs) | **$21.90** (3 NAT EIPs + 3 ALB IPs) |
| **NAT Gateways (Hourly)** | $0.045/gateway-hour | **$98.55** (3 NAT Gateways) | **$32.85** (1 Shared NAT Gateway) | **$98.55** (3 NAT Gateways) |
| **NAT Data Processing** | $0.045/GB (S3 traffic excluded) | **$2.25** (~50 GB external traffic)| **$2.25** (~50 GB external traffic)| **$22.50** (~500 GB external traffic) |
| **Cross-AZ Data Transfer** | $0.01/GB in/out | **$0.20** (~20 GB inter-AZ sync) | **$0.55** (~35 GB cross-AZ to 1-NAT)| **$35.00** (~3,500 GB inter-AZ) |
| **Amazon RDS PostgreSQL** | Multi-AZ instance + storage | **$125.13** (`db.t4g.med`, 100GB gp3) | **$72.64** (`db.t4g.small`, 50GB gp3)| **$420.00** (`db.r6g.xlarge`, 500GB gp3) |
| **Amazon ElastiCache Redis** | Multi-AZ (2 nodes) | **$49.64** (`cache.t4g.medium`, 2 nodes) | **$24.82** (`cache.t4g.micro`, 2 nodes) | **$145.00** (`cache.r6g.large`, 2 nodes) |
| **Amazon S3 Storage & API** | $0.023/GB + PUT/GET requests | **$1.20** (50 GB media assets) | **$1.20** (50 GB media assets) | **$35.00** (1,000 GB media assets) |
| **VPC S3 Gateway Endpoint**| AWS internal routing | **$0.00** (Free AWS Service) | **$0.00** (Free AWS Service) | **$0.00** (Free AWS Service) |
| **Amazon CloudFront CDN** | Free tier covers 1TB egress | **$0.00** (Under free allowance) | **$0.00** (Under free allowance) | **$30.00** (3 TB egress) |
| **Amazon CloudWatch Logs** | $0.50/GB ingestion + metrics | **$11.15** (5 GB logs + 5 alarms) | **$8.00** (3 GB logs + 3 alarms) | **$45.00** (50 GB logs + Insights) |
| **Amazon ECR Storage** | $0.10/GB | **$0.15** (3 image revisions) | **$0.15** (3 image revisions) | **$1.00** (10 image revisions) |
| **AWS Secrets Manager** | $0.40/secret/mo + API calls | **$1.30** (2 secrets + API calls) | **$1.30** (2 secrets + API calls) | **$3.50** (5 secrets + API calls) |
| **AWS KMS (Key Management)**| AWS Managed Keys | **$0.00** (Free for AWS service keys)| **$0.00** (Free for AWS service keys)| **$0.00** (Free for AWS service keys) |
| **Subtotal (Pre-Tax)** | **All itemized AWS services** | **$473.23 / month** | **$252.00 / month** | **$2,003.65 / month** |
| **Applicable Taxes (18% GST)**| Indian billing entities (AISPL)| **$85.18 / month** | **$45.36 / month** | **$360.66 / month** |
| **TOTAL ESTIMATED BILL** | **Total Monthly Commitment** | **~$558.41 / month** | **~$297.36 / month** | **~$2,364.31 / month** |

---

## 3. Correction of Previous "$180 Single-NAT Optimization" Claim

In the initial Phase 18.4 draft, it was colloquially asserted that a single-NAT staging architecture could operate at roughly ~$180 / month. The rigorous itemized recalculation above demonstrates why that initial claim was mathematically incomplete:

1. **Omission of IPv4 Address Surcharges**: AWS's February 2024 pricing introduced a $0.005/hr charge on public IPv4 addresses, adding **$14.60 to $21.90 / month** across ALB and NAT IPs.
2. **Compute Duty Cycle Underestimation**: 4 continuous 24x7 Fargate tasks (1 vCPU, 2GB RAM) cost **$144.16 / month** alone. Operating at ~$180 total would leave only $36 / month for RDS, Redis, ALB, NAT, and storage combined—which is impossible for managed Multi-AZ services.
3. **Itemized Savings from Single-NAT Architecture**:
   - Eliminating 2 NAT Gateways saves: $65.70 / month.
   - Eliminating 2 Elastic IPv4 addresses saves: $7.30 / month.
   - Additional cross-AZ data transfer to single NAT adds: +$0.35 / month.
   - **Net Monthly Savings from Single-NAT: ~$72.65 / month.**
4. **Achieving a Sub-$300 Staging Environment**:
   To safely achieve a ~$250–$295 / month staging bill (Model B), the project must:
   - Use 1 shared NAT Gateway (saves $72.65/mo).
   - Right-size Fargate tasks to 0.5 vCPU / 1GB RAM during staging (saves $72.08/mo).
   - Use `db.t4g.small` Multi-AZ for staging dataset validation (saves $52.49/mo).
   - Use `cache.t4g.micro` for cache testing (saves $24.82/mo).

---

## 4. Cost Control & Budget Alerting Implementation

To prevent unexpected billing spikes during staging stress testing:
1. **AWS Budget**: Configure a hard alert at **$350.00 / month** with notifications to the project administrator.
2. **Auto Scaling Bounds**: Cap `web_max_capacity = 4` and `worker_max_capacity = 2` during non-load-testing hours.
3. **Automated Teardown**: Staging cluster can be stopped outside business hours via ECS desired count = 0 to reduce Fargate runtime costs by 65%.
