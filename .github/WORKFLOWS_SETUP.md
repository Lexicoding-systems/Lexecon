# GitHub Actions Workflows Setup (Phase 5.3)

**Enterprise-ready CI/CD for Lexecon on AWS EKS + Kubernetes**

This guide covers the automated deployment pipeline that deploys Lexecon to AWS EKS using Kubernetes and Helm.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline Flow                          │
└─────────────────────────────────────────────────────────────────────┘

Push to main
     │
     ├─► test.yml          → Run pytest, linting, coverage
     │        │
     │        ├─► PASS → build.yml → Build Docker image → Push to ghcr.io
     │        │                             │
     │        │                             └─► deploy-staging.yml
     │        │                                      │
     │        │                                      ├─► Update EKS kubeconfig
     │        │                                      ├─► Run deploy.sh
     │        │                                      ├─► Wait for rollout
     │        │                                      ├─► Verify health checks
     │        │                                      └─► Notify Slack
     │        │
     │        └─► FAIL → Block deployment
     │
     └─► infrastructure.yml (manual) → Terraform plan/apply
                                            │
                                            └─► Create/update EKS, RDS, VPC

Manual trigger: deploy-production.yml
     │
     ├─► Require GitHub Environment approval
     ├─► Send Slack notification
     ├─► Create git tag
     ├─► Deploy to EKS production
     ├─► Verify health checks
     └─► Notify Slack
```

## Workflows

### 1. test.yml - Test & Lint

**Triggers:** Push to main/develop, PRs to main/develop

**Actions:** pytest (80%+ coverage), Black, isort, flake8, mypy, upload coverage

**Requirements:** None

### 2. build.yml - Build & Push Docker Image

**Triggers:** Push to main/develop (code changes only)

**Actions:** Build Docker image, tag, push to ghcr.io

**Requirements:** GITHUB_TOKEN (automatic)

### 3. deploy-staging.yml - Deploy to Staging

**Triggers:** Push to main (automatic), manual

**Actions:** Deploy to EKS staging, verify health, notify Slack

**Requirements:**
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- DATABASE_URL_STAGING
- SLACK_WEBHOOK (optional)

### 4. deploy-production.yml - Deploy to Production

**Triggers:** Manual only (requires version input)

**Actions:** Deploy to EKS production with approval, create git tag, verify health

**Requirements:**
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- DATABASE_URL_PRODUCTION
- SLACK_WEBHOOK (optional)

### 5. infrastructure.yml - Terraform Management

**Triggers:** Manual (plan/apply/destroy), PRs changing terraform files

**Actions:** Run terraform, manage EKS/RDS infrastructure

**Requirements:**
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- TERRAFORM_STATE_BUCKET
- TERRAFORM_LOCK_TABLE
- SLACK_WEBHOOK (optional)

## Quick Setup

### 1. AWS Prerequisites

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket --bucket lexecon-terraform-state --region us-east-1
aws s3api put-bucket-versioning --bucket lexecon-terraform-state --versioning-configuration Status=Enabled

# Create DynamoDB table for Terraform locks
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2. GitHub Secrets

Add these in **Settings → Secrets and variables → Actions**:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
TERRAFORM_STATE_BUCKET
TERRAFORM_LOCK_TABLE
DATABASE_URL_STAGING
DATABASE_URL_PRODUCTION
SLACK_WEBHOOK (optional)
```

### 3. GitHub Environments

Create in **Settings → Environments**:

**staging:** No protection rules

**production:** Enable "Required reviewers", add yourself

### 4. Deploy Infrastructure

```bash
# Update infrastructure/terraform/staging.tfvars with your VPC/subnet IDs

# Run via GitHub Actions
# Go to Actions → Infrastructure Management
# Select: environment=staging, action=plan
# Review plan, then run: action=apply
```

### 5. Configure Database URLs

After infrastructure deploys, get RDS endpoint:

```bash
cd infrastructure/terraform
terraform output rds_endpoint
# Format: postgresql://username:password@endpoint:5432/lexecon
```

Add to GitHub Secrets as `DATABASE_URL_STAGING` and `DATABASE_URL_PRODUCTION`.

### 6. Test Deployment

Push to main or run "Deploy to Staging" workflow manually.

## Costs

**Staging:** ~$150-200/month (2 t3.medium nodes, db.t3.micro)

**Production:** ~$300-400/month (3 t3.small nodes, db.t3.small multi-AZ)

## Rollback

```bash
# Application rollback
./infrastructure/scripts/rollback.sh staging

# Or via kubectl
kubectl rollout undo deployment/lexecon-staging -n staging
```

## Troubleshooting

**Workflow fails at kubeconfig:**
- Check AWS credentials in GitHub Secrets
- Verify EKS cluster exists (run infrastructure workflow first)

**Pods CrashLoopBackOff:**
```bash
kubectl get pods -n staging
kubectl logs <pod-name> -n staging
kubectl describe pod <pod-name> -n staging
```

**Terraform lock error:**
```bash
aws dynamodb scan --table-name terraform-locks
terraform force-unlock <lock-id>
```

## Next Steps

- Phase 5.4: Feature Flags
- Phase 6: Monitoring & Observability (Prometheus, Grafana)
- Phase 7: Compliance (SOC 2, GDPR)
- Phase 8: Optimization

