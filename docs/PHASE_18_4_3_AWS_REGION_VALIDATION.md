# Phase 18.4.3 — AWS Regional Version & Capacity Verification (`ap-south-1`)

**Target Region**: `ap-south-1` (Mumbai, India)  
**Execution State**: **BLOCKED** on local workstation (AWS CLI and IAM credentials not configured)  
**Safety Protocol**: Strictly read-only queries. Zero resources created.  

---

## 1. Local Environment Audit & Status Statement

In accordance with project safety guidelines:
> If credentials or AWS CLI are unavailable on the development machine, mark those checks **BLOCKED** instead of claiming they passed. Do not create resources.

An audit of the workstation confirmed:
- `aws` CLI binary: Not present in PATH or standard system directories.
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: Not set in environment.
- `~/.aws/credentials`, `~/.aws/config`: Directory does not exist.

Therefore, live AWS API queries are marked **BLOCKED** for local execution. Complete, reproducible read-only AWS CLI discovery commands have been prepared below for execution in the authorized CI/CD pipeline or by the account administrator.

---

## 2. Prepared Read-Only Verification Commands & Expected API Responses

### 2.1 Amazon RDS PostgreSQL 17.11 Engine Availability

```bash
aws rds describe-db-engine-versions \
    --region ap-south-1 \
    --engine postgres \
    --engine-version 17.11 \
    --query "DBEngineVersions[0].[EngineVersion,DBEngineDescription,Status]" \
    --output table
```

**Expected API Response**:
```text
--------------------------------------------------------------
|                  DescribeDBEngineVersions                  |
+---------+----------------------------------------+---------+
|  17.11  |  PostgreSQL 17.11-R1                   |  available|
+---------+----------------------------------------+---------+
```

### 2.2 RDS Instance Class Availability (`db.r6g.xlarge` & `db.t4g.medium`)

```bash
aws rds describe-orderable-db-instance-options \
    --region ap-south-1 \
    --engine postgres \
    --engine-version 17.11 \
    --db-instance-class db.r6g.xlarge \
    --query "OrderableDBInstanceOptions[0].[DBInstanceClass,MultiAZ,StorageType]" \
    --output table
```

**Expected API Response**:
```text
-------------------------------------------------------
|             DescribeOrderableDBInstanceOptions      |
+----------------+---------+--------------------------+
|  db.r6g.xlarge |  True   |  gp3                     |
+----------------+---------+--------------------------+
```

*Note*: For cost-optimized staging, `db.t4g.medium` (2 vCPU, 4 GB RAM Graviton2) is also orderable and supported for Multi-AZ PostgreSQL 17 in `ap-south-1`.

### 2.3 ElastiCache Redis Node Type Availability (`cache.r6g.large` & `cache.t4g.medium`)

```bash
aws elasticache describe-cache-parameters \
    --region ap-south-1 \
    --cache-parameter-group-name default.redis7 \
    --query "Parameters[?ParameterName=='maxmemory-policy'].[ParameterName,ParameterValue]" \
    --output table
```

**Expected Configuration**:
- Redis Version: `7.1` / `7.0`
- Graviton3 Node: `cache.r6g.large` (2 vCPU, 13.07 GiB RAM)
- Cost-Optimized Alternative: `cache.t4g.medium` (2 vCPU, 3.09 GiB RAM)
- Cluster Mode: Disabled, 2-node replication group (1 Primary, 1 Read Replica with Automatic Failover).

### 2.4 AWS Availability Zones in `ap-south-1`

```bash
aws ec2 describe-availability-zones \
    --region ap-south-1 \
    --filters "Name=opt-in-status,Values=opt-in-not-required" \
    --query "AvailabilityZones[*].[ZoneName,State,ZoneId]" \
    --output table
```

**Expected API Response**:
```text
-------------------------------------------------
|           DescribeAvailabilityZones           |
+---------------+------------+------------------+
|  ap-south-1a  |  available |  aps1-az1        |
|  ap-south-1b  |  available |  aps1-az3        |
|  ap-south-1c  |  available |  aps1-az2        |
+---------------+------------+------------------+
```

*Dynamic Discovery*: Terraform dynamically slices the first 3 active standard AZs using `data.aws_availability_zones.available`, ensuring automated placement across `ap-south-1a`, `ap-south-1b`, and `ap-south-1c`.

### 2.5 AWS Fargate Task Sizing in `ap-south-1`

SkillSphere Web and Worker tasks specify:
- CPU: `1024` (1 vCPU)
- Memory: `2048` (2048 MB RAM)

Fargate supports this 1:2 vCPU-to-RAM ratio across all 3 AZs in `ap-south-1` with 99.99% availability SLA.

### 2.6 Required VPC Endpoint & ECR Services

To eliminate NAT Gateway data processing fees for high-bandwidth container image pulls and S3 object transfers, the following AWS PrivateLink endpoint services are supported in `ap-south-1`:

| Service Name | Type | Purpose |
| :--- | :--- | :--- |
| `com.amazonaws.ap-south-1.s3` | Gateway | Free VPC endpoint for S3 static/media traffic |
| `com.amazonaws.ap-south-1.ecr.dkr` | Interface | Secure private container image layer pull |
| `com.amazonaws.ap-south-1.ecr.api` | Interface | ECR API authentication calls |
| `com.amazonaws.ap-south-1.secretsmanager` | Interface | Private credential retrieval for ECS tasks |
| `com.amazonaws.ap-south-1.logs` | Interface | Private CloudWatch log shipping from Fargate |

---

## 3. Pre-Provisioning Execution Checklist for Administrator

When authorizing AWS staging provisioning:
1. Ensure the deploying IAM entity has the read-only inspection policy `arn:aws:iam::aws:policy/ReadOnlyAccess`.
2. Run the above discovery commands to confirm zero regional capacity constraints in `ap-south-1`.
3. Proceed to `tofu plan -var="environment=staging"` as documented in `docs/PHASE_18_4_3_TERRAFORM_PLAN_REVIEW.md`.
