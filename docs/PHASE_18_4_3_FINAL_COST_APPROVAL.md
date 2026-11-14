# Phase 18.4.3 — Final Infrastructure Cost & Capacity Modeling

**Target Region**: AWS `ap-south-1` (Mumbai, India)  
**Currency**: USD ($) (Excluding local statutory taxes unless noted)  
**Scope**: Resource Inventory, Sizing Models, Operational Overhead & Billing Safeguards  

---

## 1. Complete Cloud Resource Inventory

| Infrastructure Component | Specification / Sizing | Minimum Staging Tier | High-Availability Tier |
| :--- | :--- | :--- | :--- |
| **AWS Region** | Mumbai, India (`ap-south-1`) | `ap-south-1` | `ap-south-1` |
| **Availability Zones** | 3 Fault Domains | Single AZ (`ap-south-1a`) | 3 AZs (`1a`, `1b`, `1c`) |
| **Virtual Private Cloud** | Dedicated CIDR `10.0.0.0/16` | 1 VPC | 1 VPC |
| **Subnets** | Public, Private App, Private Data | 3 Subnets | 9 Subnets (3x3) |
| **NAT Gateways** | Managed Outbound Egress | 1 NAT Gateway | 3 NAT Gateways |
| **Elastic IP Addresses** | Static Public IPv4 | 1 Elastic IP | 3 Elastic IPs |
| **Application Load Balancer** | Dual-AZ Public Ingress | 1 ALB (2 subnets) | 1 ALB (3 subnets) |
| **ECS Fargate Web** | 1 vCPU, 2 GB RAM | 2 Tasks | 2-4 Tasks |
| **ECS Fargate Worker** | 1 vCPU, 2 GB RAM | 1 Task | 2 Tasks |
| **Amazon RDS PostgreSQL** | PostgreSQL `17.11`, 100 GB gp3 | `db.t4g.medium` (Single-AZ) | `db.r6g.xlarge` (Multi-AZ) |
| **Amazon ElastiCache Redis** | Redis 7.0, In-transit TLS | `cache.t4g.medium` (1 Node) | `cache.r6g.large` (2 Nodes, Multi-AZ) |
| **Amazon S3 Storage** | Media + Immutable Static | ~10 GB S3 Standard | ~50 GB S3 Standard |
| **Amazon CloudFront** | PriceClass_100 CDN with OAC | 1 Distribution | 1 Distribution |
| **AWS Secrets Manager** | KMS Encrypted Credentials | 1 Secret | 1 Secret |
| **CloudWatch Monitoring** | Container Insights + Logs | Basic Logging | Container Insights + Detailed Alarms |
| **Amazon ECR** | Container Image Registry | 1 Repo (~2 GB) | 1 Repo (~5 GB) |

---

## 2. Unit Pricing Baseline (`ap-south-1`)

The following unit rates from AWS Mumbai pricing are used for all calculations:

- **Fargate vCPU**: `$0.04048` per vCPU-hour
- **Fargate RAM**: `$0.004445` per GB-hour
  - *1 Web Task (1 vCPU, 2 GB)*: `($0.04048 + 2 * $0.004445) * 730 = $36.04/month`
- **NAT Gateway**: `$0.045` per hour (`$32.85/month`) + `$0.045` per GB data processed
- **Public IPv4 Address**: `$0.005` per hour (`$3.65/month` per IP)
- **ALB**: `$0.0225` per hour (`$16.43/month`) + `$0.008` per LCU-hour
- **RDS PostgreSQL `db.t4g.medium` (Single-AZ)**: `$0.076` per hour (`$55.48/month`)
- **RDS PostgreSQL `db.r6g.xlarge` (Multi-AZ)**: `$0.704` per hour (`$513.92/month`)
- **ElastiCache `cache.t4g.medium`**: `$0.068` per node-hour (`$49.64/month`)
- **ElastiCache `cache.r6g.large` (2 Nodes)**: `2 * $0.276 * 730 = $402.96/month`
- **EBS gp3 Storage**: `$0.115` per GB-month (`100 GB = $11.50/month`)
- **S3 Standard**: `$0.023` per GB-month

---

## 3. Five Scalability Cost Models

### Model 1: Low-Cost Staging Tier (Developer & PR Verification)
*Objective*: Minimal expense while providing isolated cloud staging.
- 1 NAT Gateway + 1 EIP: `$36.50`
- 1 ALB + Public IPv4: `$23.73`
- 2 Web Tasks (1 vCPU, 2 GB): `$72.08`
- 1 Worker Task (1 vCPU, 2 GB): `$36.04`
- RDS `db.t4g.medium` (Single-AZ) + 50 GB gp3: `$61.23`
- ElastiCache `cache.t4g.medium` (1 node): `$49.64`
- S3 + CloudFront + Secrets + Logs: `$12.00`
- **Subtotal**: **`$291.22 / month`**
- *With Single Fargate Web + Single Worker (minimum footprint)*: **`$219.14 / month`**
- *With VPC Gateway Endpoints avoiding NAT data fees*: **`~$195.00 / month`**

---

### Model 2: High-Availability Staging Tier (Full Multi-AZ Parity)
*Objective*: Exact architectural mirror of production with 3 AZs and automated failover.
- 3 NAT Gateways + 3 EIPs: `3 * ($32.85 + $3.65) = $109.50`
- 1 ALB (Multi-AZ): `$25.00`
- 2 Web Tasks (1 vCPU, 2 GB): `$72.08`
- 2 Worker Tasks (1 vCPU, 2 GB): `$72.08`
- RDS `db.t4g.medium` (Multi-AZ) + 100 GB gp3: `$122.46`
- ElastiCache `cache.t4g.medium` (2 nodes, Multi-AZ): `$99.28`
- S3 + CloudFront + Secrets + Container Insights: `$25.00`
- **Total HA Staging Cost**: **`$525.40 / month`**

---

### Model 3: 1,000 Concurrent Users (Production Workload)
*Traffic*: 1,000 CCU, ~120 requests/sec, 95th percentile latency < 150ms.
- 3 NAT Gateways: `$109.50` + `$18.00` data transfer = `$127.50`
- 1 ALB (2 LCUs average): `$36.68`
- 4 Web Tasks (1 vCPU, 2 GB): `$144.16`
- 2 Worker Tasks (1 vCPU, 2 GB): `$72.08`
- RDS `db.r6g.large` (Multi-AZ) + 150 GB gp3: `$274.25`
- ElastiCache `cache.r6g.large` (2 nodes, Multi-AZ): `$402.96`
- S3 + CloudFront (1 TB egress): `$45.00`
- Secrets Manager + Container Insights: `$30.00`
- **Total 1,000 CCU Cost**: **`$1,132.63 / month`**

---

### Model 4: 5,000 Concurrent Users (Enterprise Scale)
*Traffic*: 5,000 CCU, ~600 requests/sec, distributed background tasks.
- 3 NAT Gateways + High Bandwidth Data Transfer: `$185.00`
- 1 ALB (6 LCUs average): `$65.00`
- 12 Web Tasks (1 vCPU, 2 GB, Autoscaled): `$432.48`
- 4 Worker Tasks (1 vCPU, 2 GB): `$144.16`
- RDS `db.r6g.xlarge` (Multi-AZ) + 300 GB gp3: `$548.42`
- ElastiCache `cache.r6g.large` (3-node cluster with read replica): `$604.44`
- CloudFront CDN + S3 (5 TB egress): `$140.00`
- CloudWatch + Secrets + Performance Insights: `$65.00`
- **Total 5,000 CCU Cost**: **`$2,184.50 / month`**

---

### Model 5: 10,000 Concurrent Users (Target Ultra-Scale Architecture)
*Traffic*: 10,000 CCU, ~1,250 requests/sec, 5-nines operational reliability.
- 3 NAT Gateways + S3 Gateway Endpoints: `$240.00`
- 2 ALBs (Weighted Route 53 latency routing): `$150.00`
- 20 Web Tasks (1 vCPU, 2 GB, Autoscaling Peak): `$720.80`
- 8 Worker Tasks (Distributed queue processing): `$288.32`
- RDS `db.r6g.2xlarge` (Multi-AZ Primary + Dedicated Read Replica): `$1,085.00`
- ElastiCache Redis Cluster (3 shards, 6 nodes total): `$1,208.00`
- S3 + CloudFront (15 TB egress with Brotli compression): `$320.00`
- Full Observability (CloudWatch, Prometheus, X-Ray, DLQ monitoring): `$120.00`
- **Total 10,000 CCU Ultra-Scale Cost**: **`$4,132.12 / month`**

---

## 4. Hidden & Operational Cost Analysis

When budgeting for AWS infrastructure, the following secondary charges must be accounted for:

1. **Public IPv4 Address Charges**: AWS charges `$0.005/hour` for every public IPv4 address assigned to EC2, NAT Gateways, and ALBs. For a 3-NAT + ALB setup, this contributes **`~$18.25/month`**.
2. **NAT Gateway Data Processing**: Every gigabyte traversing a NAT Gateway incurs a `$0.045/GB` fee. By implementing a **free S3 VPC Gateway Endpoint** (`com.amazonaws.ap-south-1.s3`), container image downloads and static asset uploads bypass NAT Gateways entirely, saving hundreds of dollars monthly.
3. **Statutory Taxes**: Indian Goods and Services Tax (**GST at 18%**) applies to all AWS India invoices. A `$500` cloud spend results in an actual debit of `$590`.

---

## 5. Cost Control & Billing Safeguards

Before authorizing provisioning, the repository owner must enforce the following safeguards in the AWS Billing Console:

1. **Zero-Spend Alert**: Triggers email notification if spending exceeds `$10.00`.
2. **Staging Budget Threshold**: Hard alarm at `$250.00/month` with SNS notification.
3. **Auto-Stop Policy**: Scripted AWS Lambda function configured to scale ECS tasks to 0 if monthly budget threshold ($500) is breached.
