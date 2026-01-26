# Lexecon Infrastructure as Code

**Status:** Phase 5.2 - Infrastructure as Code

This directory contains Infrastructure as Code (IaC) for deploying Lexecon to production.

## Structure

```
infrastructure/
├── terraform/           # AWS infrastructure (EKS, RDS, VPC)
│   ├── main.tf         # Kubernetes cluster, database, security
│   ├── variables.tf    # Input variables
│   ├── outputs.tf      # Output values
│   ├── staging.tfvars  # Staging environment values
│   └── production.tfvars # Production environment values
│
├── helm/               # Kubernetes application deployment
│   ├── Chart.yaml     # Helm chart metadata
│   ├── values.yaml    # Default configuration
│   └── templates/     # Kubernetes manifests
│       ├── deployment.yaml  # Pod deployment
│       ├── service.yaml     # Network service
│       ├── configmap.yaml   # Configuration
│       ├── secret.yaml      # Secrets management
│       └── _helpers.tpl     # Template helpers
│
└── scripts/            # Deployment automation
    ├── deploy.sh      # Deploy to Kubernetes
    └── rollback.sh    # Rollback to previous version
```

## Architecture

### Infrastructure Layer (Terraform)

**AWS Resources:**
- **EKS Cluster** - Kubernetes cluster for running Lexecon
- **EKS Node Group** - Worker nodes (auto-scaled)
- **RDS PostgreSQL** - Production database with encryption, backups, failover
- **VPC Security Groups** - Network isolation and access control
- **KMS Keys** - Database encryption at rest
- **AWS Secrets Manager** - Encrypted secret storage

**Environment Separation:**
- **Staging:** 2 nodes, t3.medium, db.t3.micro
- **Production:** 3+ nodes, t3.small, db.t3.small, multi-AZ, 30-day backups

### Application Layer (Helm)

**Kubernetes Manifests:**
- **Deployment** - Lexecon pods with health checks, resource limits, auto-scaling
- **Service** - ClusterIP for internal networking
- **ConfigMap** - Non-secret configuration (env, log level, service name)
- **Secret** - Encrypted secrets (database URL, API keys)

**Features:**
- Health checks (liveness, readiness)
- Resource limits & requests
- Pod anti-affinity (spread across nodes)
- Auto-scaling (2-5 replicas, 70% CPU/80% memory trigger)
- Prometheus metrics scraping
- Security context (non-root user, read-only filesystem)

## Prerequisites

### Local Tools

```bash
# AWS CLI
aws --version  # >= 2.0

# Terraform
terraform --version  # >= 1.0

# Helm
helm version  # >= 3.0

# kubectl
kubectl version  # >= 1.28

# jq (for scripts)
jq --version
```

### AWS Account

1. **VPC created** with subnets
   - At least 2 subnets in different AZs (EKS)
   - At least 2 subnets in different AZs (RDS)
   - VPC ID: `vpc-xxxxxxxx`
   - Subnet IDs: `subnet-xxxxxxxx`, `subnet-yyyyyyyy`, etc.

2. **AWS credentials configured**
   ```bash
   aws configure
   ```

3. **S3 bucket for Terraform state**
   ```bash
   aws s3api create-bucket \
     --bucket lexecon-terraform-state \
     --region us-east-1

   aws dynamodb create-table \
     --table-name terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --region us-east-1
   ```

## Quick Start

### Step 1: Configure Terraform Variables

Edit `staging.tfvars` and `production.tfvars`:

```hcl
vpc_id     = "vpc-xxxxxxxx"
subnet_ids = ["subnet-xxxxxxxx", "subnet-yyyyyyyy"]
db_subnet_ids = ["subnet-zzzzzzzz", "subnet-wwwwwwww"]
```

### Step 2: Deploy Infrastructure (One-Time)

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan staging infrastructure
terraform plan -var-file=staging.tfvars -out=staging.tfplan

# Apply staging infrastructure
terraform apply staging.tfplan

# Repeat for production
terraform plan -var-file=production.tfvars -out=production.tfplan
terraform apply production.tfplan
```

### Step 3: Configure kubectl

```bash
# Get Terraform output
CLUSTER_NAME=$(terraform output -raw eks_cluster_id)
AWS_REGION=$(terraform output -raw aws_region)

# Configure kubectl
aws eks update-kubeconfig \
  --region $AWS_REGION \
  --name $CLUSTER_NAME

# Verify connection
kubectl get nodes
```

### Step 4: Deploy Application

```bash
# Set database URL (get from Terraform output or AWS console)
export DATABASE_URL="postgresql://user:password@host:5432/lexecon"

# Deploy to staging
./infrastructure/scripts/deploy.sh staging 0.9.0

# Deploy to production (requires manual approval)
./infrastructure/scripts/deploy.sh production 0.9.0
```

## Operations

### View Deployment Status

```bash
# Check deployment
kubectl get deployment lexecon-staging -n staging -o wide

# View pods
kubectl get pods -n staging -l app.kubernetes.io/name=lexecon

# View logs
kubectl logs -f deployment/lexecon-staging -n staging

# Port forward to local
kubectl port-forward svc/lexecon-staging 8000:80 -n staging
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment/lexecon-staging \
  --replicas=3 \
  -n staging

# Auto-scaling is configured in Helm values.yaml
# Min replicas: 2
# Max replicas: 5
# CPU threshold: 70%
# Memory threshold: 80%
```

### Rollback Deployment

```bash
# Rollback to previous version
./infrastructure/scripts/rollback.sh staging

# Or manually with Helm
helm rollback lexecon-staging 1 -n staging
```

### Update Configuration

```bash
# Update ConfigMap
kubectl edit configmap lexecon-config -n staging

# Update Secret
kubectl edit secret lexecon-secrets -n staging

# Restart pods to apply changes
kubectl rollout restart deployment/lexecon-staging -n staging
```

## Monitoring

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Response includes:
# - Database connection status
# - Ledger availability
# - Auth service status
# - Rate limiter status
```

### Metrics

Prometheus metrics available at:
```
http://localhost:8000/metrics
```

Key metrics:
- `lexecon_decision_latency_ms` - Decision evaluation latency
- `lexecon_decisions_total` - Total decisions made
- `lexecon_errors_total` - Error count by type
- `lexecon_auth_latency_ms` - Authentication latency

### Logs

```bash
# Stream logs
kubectl logs -f deployment/lexecon-staging -n staging

# View logs from all pods
kubectl logs -f -l app.kubernetes.io/name=lexecon -n staging

# Search logs
kubectl logs deployment/lexecon-staging -n staging | grep ERROR
```

## Troubleshooting

### Pod Won't Start

```bash
# Check pod events
kubectl describe pod <pod-name> -n staging

# Check logs
kubectl logs <pod-name> -n staging --previous

# Common issues:
# - Database connection failed (check DATABASE_URL)
# - Image not available (check image.repository in values.yaml)
# - Insufficient resources (check node capacity)
```

### Database Connection Issues

```bash
# Test connection from pod
kubectl exec -it <pod-name> -n staging -- \
  psql -h <db-host> -U <username> -d lexecon

# Check RDS security group
aws ec2 describe-security-groups \
  --group-ids <sg-id> \
  --query 'SecurityGroups[0].IpPermissions'

# Check database logs
aws rds describe-db-logs --db-instance-identifier lexecon-staging
```

### Deployment Failures

```bash
# Check Helm release status
helm status lexecon-staging -n staging

# Get release history
helm history lexecon-staging -n staging

# Get detailed error
helm get values lexecon-staging -n staging
kubectl describe deployment lexecon-staging -n staging
```

## Security

### Secrets Management

- Secrets stored in AWS Secrets Manager (encrypted with KMS)
- Database password rotated automatically
- No secrets in Kubernetes YAML files
- Secrets injected at deployment time via Helm

### Network Security

- Database accessible only from EKS node security group
- Kubernetes API endpoint requires authentication
- Pod security context: non-root user, read-only filesystem
- Network policies can be added for pod-to-pod communication

### Compliance

- Database encryption at rest (KMS)
- Database encryption in transit (TLS)
- Backups encrypted and retained per environment policy
- Audit logs available from RDS Enhanced Monitoring

## Cost Optimization

### Staging Environment

- 2 t3.medium nodes (dev/test workloads)
- db.t3.micro instance (shared resources)
- 7-day backup retention
- No multi-AZ failover

**Estimated cost:** ~$150-200/month

### Production Environment

- 3 t3.small nodes (production workloads)
- db.t3.small instance (dedicated database)
- Multi-AZ failover
- 30-day backup retention

**Estimated cost:** ~$300-400/month

### Cost Reduction Options

1. **Use spot instances** for non-critical workloads
2. **Schedule staging** to auto-scale down at night
3. **Enable RDS auto-scaling** for database compute
4. **Use lifecycle policies** for backup retention

## Disaster Recovery

### RTO/RPO

- **RTO (Recovery Time Objective):** 30 minutes
- **RPO (Recovery Point Objective):** 1 hour

### Backup Strategy

- Automated daily snapshots (retained 7-30 days)
- Multi-AZ failover (production only)
- Cross-region backup replication (optional)

### Restore Procedure

```bash
# List available snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier lexecon-production

# Create new instance from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier lexecon-restored \
  --db-snapshot-identifier <snapshot-id>

# Update Helm values to point to new database
kubectl edit secret lexecon-secrets -n production
# Update DATABASE_URL

# Restart pods
kubectl rollout restart deployment/lexecon-prod -n production
```

## Next Steps

- **Phase 5.3:** Automated Deployments (CI/CD integration with GitHub Actions)
- **Phase 5.4:** Feature Flags (LaunchDarkly/Unleash integration)
- **Phase 6:** Monitoring & Observability (APM, alerting, health checks)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Terraform/Helm documentation
3. Check AWS CloudTrail for infrastructure events
4. Review Kubernetes events: `kubectl get events -n <namespace>`
