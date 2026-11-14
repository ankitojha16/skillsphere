# SkillSphere Phase 18.4 — Secrets Management & IAM Hardening Specification

**Security Standard**: CIS AWS Foundations Benchmark v3.0 / Least-Privilege IAM  
**Credential Storage**: AWS Secrets Manager (Encrypted with AWS KMS)  
**Authentication Paradigm**: Role-Based IAM Credentials (Zero Static Keys in Containers)  

---

## 1. Secrets Management Architecture

In accordance with strict security standards, real credential values are never committed to Git, passed via build arguments, embedded in container image layers, or exposed in plaintext ECS environment variables.

### 1.1 Secrets Manager Schema (`skillsphere-staging-app-secrets`)
All staging application credentials are stored as an encrypted JSON secret in AWS Secrets Manager:

```json
{
  "SECRET_KEY": "django-insecure-staging-entropy-key-here",
  "DATABASE_URL": "postgresql://skillsphere_admin:RDS_MANAGED_PASS@skillsphere-staging-db.c7x8y.ap-south-1.rds.amazonaws.com:5432/skillsphere",
  "REDIS_URL": "rediss://skillsphere-staging-redis.c7x8y.clustercfg.aps1.cache.amazonaws.com:6379",
  "GEMINI_API_KEY": "AIzaSyStagingKeyPlaceholder"
}
```

### 1.2 ECS Task Definition Secrets Injection
ECS Agent retrieves secrets at container launch time and securely injects them directly into container process environment variables:

```hcl
secrets = [
  { name = "SECRET_KEY",     valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:SECRET_KEY::" },
  { name = "DATABASE_URL",   valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:DATABASE_URL::" },
  { name = "REDIS_URL",      valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:REDIS_URL::" },
  { name = "GEMINI_API_KEY", valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:GEMINI_API_KEY::" }
]
```

### 1.3 Permitted Plaintext Environment Variables
Only non-sensitive operational parameters are passed as static environment variables:
- `DEBUG`: `"False"`
- `WEB_CONCURRENCY`: `"2"`
- `GUNICORN_THREADS`: `"4"`
- `STORAGE_BACKEND`: `"s3"`
- `AWS_STORAGE_BUCKET_NAME`: `"skillsphere-staging-media-assets"`
- `AWS_S3_REGION_NAME`: `"ap-south-1"`
- `STORAGE_USE_IAM_ROLE`: `"True"`

---

## 2. Separation of IAM Roles (Least-Privilege Enforcement)

SkillSphere implements strict role separation between infrastructure orchestration, container execution, and application runtime:

```
    [ GitHub Actions CI/CD ]           [ ECS Fargate Agent ]           [ SkillSphere Python App ]
                │                                │                                  │
      (sts:AssumeRoleWithWebIdentity)   (AmazonECSTaskExecutionRole)        (Container Credential Provider)
                ▼                                ▼                                  ▼
    [ Provisioning Role ]              [ Execution Role ]                 [ Application Task Role ]
    - Terraform Plan/Apply             - Pull ECR container image          - S3: PutObject, GetObject
    - VPC, RDS, Redis, ECS             - Create CloudWatch logs            - S3: DeleteObject, ListBucket
    - Boundary: Staging Env Only       - Get Secrets from Secrets Manager  - Zero Access to DB/VPC/IAM
```

### 2.1 ECS Task Execution Role (`ecs-execution-role`)
- **Trust Policy**: `ecs-tasks.amazonaws.com`
- **Managed Policy**: `arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy`
  - Allows ECS agent to pull Docker images from Amazon ECR.
  - Allows ECS agent to create log streams and push logs to CloudWatch Logs (`/ecs/skillsphere-staging-*`).
- **Custom Inline Policy**:
  - `secretsmanager:GetSecretValue` strictly on `arn:aws:secretsmanager:ap-south-1:<ACCOUNT_ID>:secret:skillsphere-staging-app-secrets*`.

### 2.2 ECS Application Task Role (`ecs-task-role`)
- **Trust Policy**: `ecs-tasks.amazonaws.com`
- **Permissions Scope**: Grants the Python Django code inside the running container access to AWS APIs.
- **S3 Least-Privilege Inline Policy**:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowMediaObjectOperations",
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        "Resource": "arn:aws:s3:::skillsphere-staging-media-assets/*"
      },
      {
        "Sid": "AllowBucketListing",
        "Effect": "Allow",
        "Action": ["s3:ListBucket"],
        "Resource": "arn:aws:s3:::skillsphere-staging-media-assets"
      }
    ]
  }
  ```
- **Zero Permanent Credentials**: The container uses AWS IAM role credentials provided dynamically by the ECS metadata endpoint (`169.254.170.2`). No AWS access key ID or secret access key exists inside the container or image.

### 2.3 CI/CD Infrastructure Provisioning Role (OIDC Federation)
- Uses GitHub Actions OpenID Connect (OIDC) identity provider.
- Eliminates permanent long-lived AWS IAM User credentials in GitHub repository secrets.
- **Trust Policy Condition**:
  ```json
  {
    "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
    "StringLike": { "token.actions.githubusercontent.com:sub": "repo:ankitojha16/ankit-kumar-portfolio:environment:staging-audit" }
  }
  ```

---

## 3. Terraform State Protection & Backend Encryption

To safeguard Terraform state files containing infrastructure metadata:
1. **Remote State Backend**: Amazon S3 bucket (`skillsphere-terraform-state-staging`).
2. **Server-Side Encryption**: Enforced with AWS KMS (`aws:kms`).
3. **Bucket Versioning**: Enabled to prevent accidental deletion and preserve complete history.
4. **Public Access Block**: All public ACLs and bucket policies blocked.
5. **State Locking**: Amazon DynamoDB table (`skillsphere-terraform-locks`) prevents concurrent execution conflicts.
