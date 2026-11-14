# SkillSphere Phase 18.4 — Network Architecture & Security Specification

**VPC CIDR**: `10.0.0.0/16`  
**Region**: `ap-south-1` (Mumbai)  
**Availability Zones**: Dynamically selected across 3 active standard AZs  
**Security Model**: Defense-in-depth, 3-tier isolated subnet hierarchy  

---

## 1. VPC Subnet Segmentation & Route Table Design

The SkillSphere network is partitioned into three isolated tiers across 3 Availability Zones to ensure high availability and prevent lateral movement in the event of a compromised container.

```
                           [ Internet Gateway (IGW) ]
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
  Public Subnet 1                Public Subnet 2                Public Subnet 3
  (10.0.0.0/20 - AZ-a)           (10.0.16.0/20 - AZ-b)          (10.0.32.0/20 - AZ-c)
  [ALB + NAT Gateway 1]          [ALB + NAT Gateway 2]          [ALB + NAT Gateway 3]
        │                              │                              │
        │ Route: 0.0.0.0/0 -> NAT 1    │ Route: 0.0.0.0/0 -> NAT 2    │ Route: 0.0.0.0/0 -> NAT 3
        ▼                              ▼                              ▼
  Private App Subnet 1           Private App Subnet 2           Private App Subnet 3
  (10.0.48.0/20 - AZ-a)          (10.0.64.0/20 - AZ-b)          (10.0.80.0/20 - AZ-c)
  [ECS Web + Worker Tasks]       [ECS Web + Worker Tasks]       [ECS Web + Worker Tasks]
  Direct S3 GW Endpoint          Direct S3 GW Endpoint          Direct S3 GW Endpoint
        │                              │                              │
        │ Local VPC Route Only         │ Local VPC Route Only         │ Local VPC Route Only
        ▼                              ▼                              ▼
  Private Data Subnet 1          Private Data Subnet 2          Private Data Subnet 3
  (10.0.96.0/20 - AZ-a)          (10.0.112.0/20 - AZ-b)         (10.0.128.0/20 - AZ-c)
  [RDS Primary / Redis Prim]     [RDS Standby / Redis Repl]     [Subnet Group Quorum]
  (Zero Internet Routes)         (Zero Internet Routes)         (Zero Internet Routes)
```

### 1.1 Public Subnets
- **Subnet CIDRs**: `10.0.0.0/20`, `10.0.16.0/20`, `10.0.32.0/20`.
- **Route Table**: `0.0.0.0/0` targeted to `aws_internet_gateway.igw`.
- **Attached Workloads**: Dual-AZ public Application Load Balancer and AWS NAT Gateways.
- **Public IP Allocation**: Only ALB interfaces and NAT Gateway Elastic IPs possess public IPv4 addresses.

### 1.2 Private Application Subnets
- **Subnet CIDRs**: `10.0.48.0/20`, `10.0.64.0/20`, `10.0.80.0/20`.
- **Route Table**: Dedicated per-AZ route tables targeting the local AZ's NAT Gateway (`0.0.0.0/0` -> `nat_gateway[count.index]`).
- **Attached Workloads**: ECS Fargate Web tasks and Background Worker tasks.
- **Zero Public IP**: `assign_public_ip = false`. Tasks cannot be directly addressed from the public internet under any circumstance.
- **S3 Gateway Endpoint**: Traffic destined for Amazon S3 (`com.amazonaws.ap-south-1.s3`) is intercepted at the VPC route table level and routed internally without leaving AWS.

### 1.3 Private Data Subnets
- **Subnet CIDRs**: `10.0.96.0/20`, `10.0.112.0/20`, `10.0.128.0/20`.
- **Route Table**: Strictly local VPC routing (`10.0.0.0/16` -> `local`).
- **Zero Outbound Internet**: No route to Internet Gateway. No route to NAT Gateway.
- **Attached Workloads**: Amazon RDS PostgreSQL instance and Amazon ElastiCache Redis cluster.
- **Public Access**: `publicly_accessible = false` strictly enforced on RDS and ElastiCache.

---

## 2. VPC Endpoints vs NAT Gateway Cost-Benefit Tradeoff

AWS provides two types of VPC Endpoints: **Gateway Endpoints** and **Interface Endpoints (AWS PrivateLink)**.

### 2.1 S3 Gateway Endpoint (Implemented: Mandatory)
- **Hourly Cost**: **$0.00 / month** (Completely Free).
- **Data Processing Cost**: **$0.00 / GB** (Completely Free).
- **Benefit**: All media uploads, certificate downloads, and S3 bucket API calls bypass the NAT Gateway entirely. This saves **$0.045 / GB** in NAT data processing fees and provides sub-5ms internal latency.

### 2.2 Interface Endpoints Evaluation (ECR, CloudWatch, Secrets Manager, STS)
AWS charges **$0.01 / hour per AZ** for each interface endpoint ($7.30 / endpoint / month per AZ) plus **$0.01 / GB** data processing:
- To deploy interface endpoints across 3 AZs for 5 services (ECR API, ECR DKR, CloudWatch Logs, Secrets Manager, STS):
  $$\text{Cost} = 5 \text{ services} \times 3 \text{ AZs} \times \$7.30/\text{mo} = \$109.50 / \text{month (base)}$$
- In contrast, staging data transfer through NAT Gateway for image pulls and API calls is estimated at **~50 GB / month**:
  $$\text{NAT Processing Cost} = 50 \text{ GB} \times \$0.045/\text{GB} = \$2.25 / \text{month}$$

### Architectural Decision:
For staging, deploying 15 interface endpoint ENIs ($109.50/mo) to save $2.25 in NAT processing is commercially wasteful. SkillSphere utilizes the **S3 Gateway Endpoint (Free)** for bulk media traffic, while routing occasional ECR image pulls, CloudWatch logs, and Secrets Manager API calls through the existing NAT Gateways. In production (where container churn and log volume exceed 2.5 TB/mo), interface endpoints become financially justified.

---

## 3. Security Groups Least-Privilege Rules Matrix

```
                      [ Client: Public Internet ]
                                   │
                           TCP 80, 443 │
                                   ▼
                      ┌─────────────────────────┐
                      │    alb-security-group   │
                      └────────────┬────────────┘
                                   │
                              TCP 8000 │ (Gunicorn)
                                   ▼
                      ┌─────────────────────────┐
                      │   ecs-web-security-group│
                      └──────┬────────────┬─────┘
                             │            │
                    TCP 5432 │            │ TCP 6379
                             ▼            ▼
             ┌─────────────────────┐  ┌─────────────────────┐
             │ rds-security-group  │  │ redis-security-group│
             └─────────────────────┘  └─────────────────────┘
                             ▲            ▲
                    TCP 5432 │            │ TCP 6379
                             │            │
                      ┌──────┴────────────┴─────┐
                      │ecs-worker-security-group│
                      │  (No Inbound Ports)     │
                      └─────────────────────────┘
```

| Security Group ID | Ingress Protocol / Port | Allowed Source | Description |
| :--- | :--- | :--- | :--- |
| `skillsphere-staging-alb-sg` | TCP 80, 443 | `0.0.0.0/0` | Public internet HTTP/HTTPS traffic |
| `skillsphere-staging-ecs-web-sg` | TCP 8000 | `skillsphere-staging-alb-sg` | Ingress strictly from ALB |
| `skillsphere-staging-ecs-worker-sg` | None | None | No inbound ports; worker pulls jobs via polling |
| `skillsphere-staging-rds-sg` | TCP 5432 | `ecs-web-sg`, `ecs-worker-sg` | PostgreSQL ingress from authorized containers only |
| `skillsphere-staging-redis-sg` | TCP 6379 | `ecs-web-sg`, `ecs-worker-sg` | Redis ingress from authorized containers only |

All security groups implement strict egress filtering. Database and cache security groups have zero external ingress rules, preventing any unauthorized network penetration.
