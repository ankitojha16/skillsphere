# SkillSphere Five-Nines (99.999%) Availability & Disaster Recovery Blueprint

## 1. Five-Nines Reality & Definitions

**99.999% Availability** permits at most:
- **5.26 minutes** of total downtime per year.
- **25.9 seconds** of downtime per month.
- **6.05 seconds** of downtime per week.

> [!IMPORTANT]
> Application code cannot guarantee five-nines availability independently. Achieving 99.999% requires infrastructure-level multi-AZ redundancy, automated zero-downtime rolling deployments, active-passive database failover, and multi-region anycast DNS routing.

---

## 2. Infrastructure Dependencies for Five-Nines

### 1. Multi-Zone Compute Tier (GCP Cloud Run / AWS ECS Fargate)
- **Minimum 3 Availability Zones**: Container tasks distributed across at least 3 distinct AZs (e.g. `ap-south-1a`, `ap-south-1b`, `ap-south-1c`).
- **Autoscaling Target**: Scaled from 3 tasks (off-peak baseline) to 30 tasks based on CPU utilization ($>65\%$) and request queue depth ($>150\text{ req/min}$).
- **Zero-Downtime Rolling Updates**: New container images deployed using blue/green or canary deployments; traffic cuts over only when `/health/ready/` returns 200 OK.

### 2. High-Availability PostgreSQL Cluster
- **Primary-Replica with Automated Failover**: Supabase Enterprise or AWS RDS Multi-AZ with automated heartbeat-based failover ($<30\text{ seconds}$ RTO).
- **PgBouncer Poolers**: Redundant pooler instances behind internal network load balancers.

### 3. Distributed Redis Cluster
- Multi-node Redis with automated master-replica failover (e.g., Upstash Global Replication or AWS ElastiCache Multi-AZ with Auto-Failover).

---

## 3. Disaster Recovery Objectives (RTO & RPO)

| Scenario | Recovery Time Objective (RTO) | Recovery Point Objective (RPO) | Recovery Procedure |
|---|---|---|---|
| **Single Container Crash** | **$< 2\text{ seconds}$** | **$0\text{ seconds}$** | ALB routes traffic to healthy sibling tasks |
| **Zone Outage (Single AZ)** | **$< 5\text{ seconds}$** | **$0\text{ seconds}$** | Traffic auto-rebalanced across surviving 2 AZs |
| **Primary Database Failover** | **$< 30\text{ seconds}$** | **$< 1\text{ second}$** | Standby replica promoted automatically; PgBouncer updates pool target |
| **Complete Region Outage** | **$< 10\text{ minutes}$** | **$< 5\text{ minutes}$** | Global DNS re-routes to secondary standby region |
| **Accidental Data Deletion** | **$< 30\text{ minutes}$** | **$< 1\text{ hour}$** | Point-in-Time Recovery (PITR) from Supabase WAL archiving |
