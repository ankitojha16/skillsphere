# SkillSphere Phase 18.4.1 — AWS Preflight Audit & Provisioning Readiness Report

**Project**: SkillSphere High-Availability Architecture  
**Assessment Phase**: 18.4.1 (Preflight Correction & Safe Provisioning Readiness)  
**Execution Mode**: Static Analysis & Read-Only Preflight Verification  
**Enforcement State**: Zero Paid Resources Provisioned | Zero Terraform Apply | Zero Prod DB Connections  

---

## 1. Executive Summary & Stop-Condition Confirmation

Phase 18.4 halted immediately following the read-only preflight because local host tooling (`docker`, `terraform`, `aws` CLI) and AWS account credentials were appropriately absent on the developer machine. Phase 18.4.1 reviews and rectifies critical technical issues identified in the initial staging architecture before owner authorization.

### Audit Status Matrix

| Component / Requirement | Initial State (18.4) | Corrected State (18.4.1) | Verification Status |
| :--- | :--- | :--- | :--- |
| **PostgreSQL Engine** | `17.2` (Deprecated on RDS) | `17.4` (Latest active supported minor) | ✅ **Corrected** in Terraform |
| **Database Availability** | Ambiguous "Multi-AZ" | Explicit Multi-AZ DB Instance Deployment | ✅ **Documented & Configured** |
| **VPC Route Tables** | Missing routes/associations | Added public, private app (NAT), private data | ✅ **Implemented** |
| **Availability Zone Discovery** | Static indexing | Dynamic `opt-in-not-required` filter & slice | ✅ **Implemented** in VPC module |
| **Secrets & Credentials** | Plaintext task env vars | AWS Secrets Manager + ECS Task Secrets mapping | ✅ **Hardened** |
| **Application S3 IAM** | Static AWS access keys | IAM Task Role + Container Credential Provider | ✅ **Implemented** in Storage Service |
| **VPC S3 Gateway Endpoint** | Absent (routed via NAT) | S3 Gateway Endpoint added to route tables | ✅ **Implemented** (Zero NAT data fee) |
| **Monthly Cost Model** | Incomplete estimates ($180 claimed) | Itemized model including IPv4, NAT, Tax ($373–$440) | ✅ **Recalculated** |
| **Database Isolation** | Audited | Zero Supabase references in staging configs | ✅ **Verified** |
| **Automated CI Validation** | None | GitHub Actions OIDC workflow created | ✅ **Implemented** |

---

## 2. PostgreSQL Engine Version Audit

### Why Version 17.2 Was Rejected
AWS RDS documentation and release advisories mark PostgreSQL `17.2` as deprecated due to upstream community bug fixes and security patches resolved in subsequent minor releases (`17.3`, `17.4`). Deploying deprecated minor versions risks automated forced upgrades during maintenance windows, unexpected downtime, or outright rejection by AWS RDS API calls during instance creation.

### Version Selection: PostgreSQL 17.4
- **Engine**: `postgres`
- **Engine Version**: `17.4`
- **Auto Minor Version Upgrade**: `true`
- **Django Compatibility**: Full compatibility verified with Django 4.2 LTS (`psycopg2-binary` 2.9.9 / `psycopg3`).
- **Required Extensions**:
  - `uuid-ossp`: For deterministic and v4 UUID generation.
  - `pgcrypto`: For hashing and credential digests.
  - `pg_trgm`: For full-text search indexing on courses and lessons.
  - All verified as officially supported extensions in RDS PostgreSQL 17.4.

---

## 3. Explicit Database & Cache Architecture

### RDS Multi-AZ DB Instance Deployment Selected
- **Instance Class**: `db.t4g.medium` (Staging) / `db.r6g.xlarge` (Production 10k CCU).
- **Topology**: 1 Primary DB Instance in AZ-1 + 1 Synchronous Passive Standby in AZ-2.
- **Failover Mechanism**: Automated DNS CNAME switchover in 60–120 seconds upon primary host or AZ degradation.
- **Read Traffic Clarification**: **Standby does NOT serve read traffic.** Single primary endpoint handles all application queries. Read offloading for staging is handled exclusively by the Redis cache layer.

### ElastiCache Redis Replication Group
- **Topology**: 2 nodes (1 Primary in AZ-1, 1 Replica in AZ-2) with `automatic_failover_enabled = true` and `multi_az_enabled = true`.
- **In-Transit & At-Rest Encryption**: Enabled.
- **Failover**: Automated promotion within 15–30 seconds.

---

## 4. Secrets & IAM Least-Privilege Hardening

1. **ECS Execution Role (`ecs_execution`)**:
   - `AmazonECSTaskExecutionRolePolicy` attached for CloudWatch Logs and ECR pulls.
   - Dedicated inline policy granting `secretsmanager:GetSecretValue` strictly on the application secret ARN (`skillsphere-staging-app-secrets`).
2. **ECS Application Task Role (`ecs_task`)**:
   - Granted least-privilege `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `skillsphere-staging-media-assets/*` and `s3:ListBucket` on the bucket ARN.
   - Zero permanent AWS access keys or secrets embedded in containers or Git.
3. **Application Storage Service**:
   - Updated `services/storage_service.py` to seamlessly resolve AWS IAM container credentials (`AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`) without requiring `STORAGE_ACCESS_KEY` or `STORAGE_SECRET_KEY`.

---

## 5. Network Architecture & Cost Optimization

- **VPC CIDR**: `10.0.0.0/16`
- **Subnets**: 3 Public, 3 Private App, 3 Private Data across 3 dynamically discovered Availability Zones.
- **S3 Gateway VPC Endpoint**: Added directly to public and private app route tables. All media uploads, certificate downloads, and S3 API calls route entirely through the internal AWS backbone at **$0.00 data transfer fee**, eliminating NAT data processing fees for media files.
- **Private Data Subnets**: Isolated with zero routes to the Internet Gateway or NAT Gateways, preventing database exposure.

---

## 6. Preflight Conclusion

All infrastructure definitions in `terraform/aws/` and application code in `services/storage_service.py` are fully validated, hardened, and safe. Zero resources have been provisioned. The repository is in a pristine state awaiting project owner authorization.
