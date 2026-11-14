# Phase 18.4.3 — Owner Authorization & Financial Commitment Checklist

**Target**: SkillSphere AWS Staging Infrastructure Provisioning  
**Region**: `ap-south-1` (Mumbai, India)  
**Governance**: Strict Financial & Architectural Readiness Gate  

---

## 1. Owner & Financial Sponsor Sign-Off

> [!IMPORTANT]
> **Parent / Guardian & Account Owner Financial Review Notice**:  
> Cloud infrastructure provisioning creates ongoing recurring monthly charges billed to the attached credit/debit card on Amazon Web Services. Once provisioned, resources like NAT Gateways, ALBs, RDS databases, and ElastiCache clusters incur hourly costs even when idle. Appropriate adult/guardian review and explicit approval of recurring billing commitments are mandatory prior to provisioning.

### Financial Commitment Summary:
- **Estimated Staging Monthly Footprint**: **`$195 – $290 USD / month`** (Low-Cost Tier) or **`$480 – $525 USD / month`** (Full High-Availability Tier).
- **Statutory Taxes**: Indian GST (18%) will be added to the final monthly AWS invoice.
- **Billing Alarm Requirement**: A hard threshold alert must be set at `$100.00` and `$250.00` in the AWS Billing & Cost Management Console.

---

## 2. Technical Prerequisites & Safety Verification

Before running `terraform apply`, verify each item:

- [ ] **AWS Account Created & Active**: Account status verified with active payment method in `ap-south-1`.
- [ ] **Zero Production Cross-Talk Verified**: Audited code confirms zero connections to live Supabase (`aws-0-ap-south-1.pooler.supabase.com`).
- [ ] **Billing Alerts Configured**:
  - [ ] CloudWatch Alarm for EstimatedCharges > $50.00
  - [ ] CloudWatch Alarm for EstimatedCharges > $150.00
  - [ ] AWS Budgets daily spend report enabled.
- [ ] **IAM Deployment Identity Configured**:
  - [ ] GitHub Actions OIDC trust policy configured with `repo:ankitojha16/skillsphere:ref:refs/heads/main`.
  - [ ] Zero static AWS access keys stored in repository files.
- [ ] **Software Baseline Verified**:
  - [ ] Python `3.12.16` confirmed.
  - [ ] Django `5.2.19` LTS confirmed.
  - [ ] 369 regression tests passing (0 failures, 0 errors).
  - [ ] Zero Django deprecation warnings (`python -Wd manage.py check`).
- [ ] **Static Asset Pipeline Prepared**:
  - [ ] Manifest verified with 179 content-hashed assets.
  - [ ] Cumulative S3 upload strategy active (`scripts/deploy_static_assets.py`).
  - [ ] CloudFront CDN distribution defined with Origin Access Control (OAC).

---

## 3. Form of Authorization

```text
I, [Account Owner Name], and [Parent/Guardian Name if applicable], hereby authorize:
1. The creation of staging cloud resources in AWS region ap-south-1.
2. A recurring monthly cloud infrastructure budget of up to $__________ USD.
3. The automated deployment of the SkillSphere staging environment via Terraform / OpenTofu.

Signature: ___________________________    Date: _______________
```

---

## 4. Execution Procedure Upon Formal Authorization

Once written authorization is granted and AWS credentials are provided:

```bash
# 1. Export authorized deployment credentials or assume OIDC role
export AWS_REGION="ap-south-1"

# 2. Deploy static assets to S3 and verify CDN availability
python scripts/deploy_static_assets.py \
    --bucket skillsphere-staging-static-assets \
    --region ap-south-1 \
    --apply

# 3. Initialize and execute Terraform staging deployment
cd terraform/aws
tofu init -backend=true
tofu plan -var="environment=staging" -out=staging.tfplan
tofu apply staging.tfplan

# 4. Verify deployment health probe
ALB_DNS=$(tofu output -raw alb_dns_name)
curl -f http://${ALB_DNS}/health/live/
```
