# GitHub Actions Workflows Setup

This document explains the CI/CD workflows and how to configure them for your environment.

## Workflows

### 1. test.yml - Test & Lint (on push to main/develop, on PR)

**Purpose:** Run automated tests and linting on every push and pull request.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Steps:**
1. Install dependencies (pytest, Black, isort, flake8, mypy)
2. Run Black linting
3. Run isort import sorting
4. Run flake8 style checks
5. Run mypy type checking (non-blocking)
6. Run pytest with coverage report
7. Fail if coverage < 80%
8. Comment on PR with results

**Requirements:**
- Python 3.11+ environment
- `pyproject.toml` with dependencies defined
- Tests in `tests/` directory

**No configuration needed.** This workflow runs automatically.

---

### 2. build.yml - Build & Push Docker Image (on push to main/develop)

**Purpose:** Build Docker image and push to GitHub Container Registry after tests pass.

**Triggers:**
- Push to `main` or `develop` branches
- Only if `src/`, `Dockerfile`, `pyproject.toml`, `requirements.txt`, or this workflow changes

**Steps:**
1. Set up Docker Buildx
2. Log in to ghcr.io
3. Extract image metadata (tags, labels)
4. Build and push Docker image
5. Tag with commit SHA, branch name, and `latest`

**Requirements:**
- `Dockerfile` in repository root
- GitHub token (automatic, no config needed)

**Image naming:**
- `ghcr.io/{owner}/{repo}:{tag}`
- Tags: `main`, `develop`, `main-{sha}`, `develop-{sha}`, `latest` (main only)

**Example:**
```
ghcr.io/lexicoding-systems/lexecon:latest
ghcr.io/lexicoding-systems/lexecon:main-a1b2c3d
ghcr.io/lexicoding-systems/lexecon:develop-x9y8z7
```

**No configuration needed** beyond having a Dockerfile.

---

### 3. deploy-staging.yml - Deploy to Staging (on push to main)

**Purpose:** Automatically deploy to staging environment after successful build.

**Triggers:**
- Push to `main` branch
- Only if tests and build succeed

**Steps:**
1. Connect via SSH to staging server
2. Pull latest code from main
3. Pull Docker images
4. Run `docker-compose up -d`
5. Verify `/health` endpoint responds
6. Notify Slack of success/failure

**Configuration Required:**

Add these **secrets** to your GitHub repository (Settings → Secrets and variables → Actions):

```
STAGING_DEPLOY_KEY         - SSH private key for staging server
STAGING_DEPLOY_HOST        - Hostname/IP of staging server
STAGING_DEPLOY_USER        - SSH user on staging server
STAGING_DEPLOY_PATH        - Path to Lexecon directory on staging server
SLACK_WEBHOOK              - Slack webhook URL for notifications
```

**Example Secret Values:**
```
STAGING_DEPLOY_HOST = staging.lexecon.local
STAGING_DEPLOY_USER = deploybot
STAGING_DEPLOY_PATH = /opt/lexecon
```

**SSH Key Setup:**
1. Generate key: `ssh-keygen -t ed25519 -f lexecon_deploy -C "github-actions"`
2. Add public key to staging server: `~deploybot/.ssh/authorized_keys`
3. Copy private key to GitHub secret `STAGING_DEPLOY_KEY`

**Health Check:**
- Endpoint: `http://staging.lexecon.local/health`
- If unhealthy, deployment fails and Slack notification sent

---

### 4. deploy-prod.yml - Deploy to Production (manual workflow dispatch)

**Purpose:** Manual, approval-gated production deployment.

**Trigger:**
- Manual via GitHub Actions UI (`workflow_dispatch`)
- Requires production environment approval (see below)

**Parameters:**
- `version` - Version number to deploy (format: X.Y.Z, e.g., 1.0.0)

**Steps:**
1. Validate version format (X.Y.Z)
2. Connect via SSH to production server
3. Pull latest code from main
4. Create and push git tag
5. Pull Docker images
6. Run `docker-compose up -d`
7. Verify `/health` and `/health/ready` endpoints
8. Notify Slack of success/failure

**Configuration Required:**

Add these **secrets**:
```
PROD_DEPLOY_KEY         - SSH private key for production server
PROD_DEPLOY_HOST        - Hostname/IP of production server
PROD_DEPLOY_USER        - SSH user on production server
PROD_DEPLOY_PATH        - Path to Lexecon directory on production server
SLACK_WEBHOOK           - Slack webhook URL for notifications
```

**Environment Protection:**

Create a **production environment** with approval rules:

1. Go to Settings → Environments → New environment
2. Name: `production`
3. Add **Required reviewers** (e.g., team leads)
4. Select **Require reviewers to approve** before deploying

This forces manual approval before production deployment runs.

**How to Deploy:**
1. Go to Actions → Deploy to Production
2. Click "Run workflow"
3. Enter version number (e.g., `1.0.1`)
4. Required reviewers get notification to approve
5. Deployment runs after approval
6. Slack notification sent with result

---

## Branch Protection Rules

To enforce that tests must pass before merging, configure branch protection:

**Settings → Branches → Branch protection rules → Add rule**

Configure for `main` branch:

- [x] Require a pull request before merging
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require status checks to pass before merging
  - Status checks: `test` (from test.yml)
  - Require branches to be up to date before merging
- [x] Require branches to be up to date before merging
- [x] Include administrators

This ensures:
- All PRs require review
- Tests must pass (test.yml must succeed)
- No force pushes to main
- Admins follow same rules

---

## Secrets Configuration Checklist

### Staging Deployment

- [ ] `STAGING_DEPLOY_KEY` - SSH private key
- [ ] `STAGING_DEPLOY_HOST` - Staging server hostname
- [ ] `STAGING_DEPLOY_USER` - SSH user
- [ ] `STAGING_DEPLOY_PATH` - Deployment directory

### Production Deployment

- [ ] `PROD_DEPLOY_KEY` - SSH private key
- [ ] `PROD_DEPLOY_HOST` - Production server hostname
- [ ] `PROD_DEPLOY_USER` - SSH user
- [ ] `PROD_DEPLOY_PATH` - Deployment directory
- [ ] `SLACK_WEBHOOK` - Slack notification URL

### Staging & Production

- [ ] `SLACK_WEBHOOK` - Used by both staging and production deployments

---

## Rollback Procedure

### Rollback Staging
1. SSH to staging server manually
2. Checkout previous commit: `git checkout HEAD~1`
3. Redeploy: `docker-compose up -d`

### Rollback Production
1. Use GitHub Actions UI
2. Go to Actions → Deploy to Production
3. Click "Run workflow"
4. Enter previous version number
5. Approve deployment
6. Production rolls back to previous version

---

## Monitoring Workflows

View workflow status:
- Dashboard: Actions tab
- Status badges: Add to README.md

```markdown
![Test](https://github.com/lexicoding-systems/lexecon/actions/workflows/test.yml/badge.svg)
![Build](https://github.com/lexicoding-systems/lexecon/actions/workflows/build.yml/badge.svg)
```

---

## Troubleshooting

### Tests fail locally but pass in CI
- Check Python version: `python --version` (should be 3.11+)
- Check dependencies: `pip install -e .`
- Run tests: `pytest tests/ -v --cov`

### Docker image doesn't push
- Check permissions: `docker login ghcr.io`
- GitHub token has `write:packages` permission

### Staging deployment fails
- Check SSH key: `ssh -i ~/.ssh/id_rsa deploybot@staging.lexecon.local`
- Check `/opt/lexecon/docker-compose.yml` exists
- Check network connectivity from GitHub runner (may need VPN)

### Production deployment requires approval but nobody sees it
- Check environment exists: Settings → Environments → production
- Check reviewers are configured: Environment → Required reviewers
- Check GitHub notifications are enabled

---

## Next Steps

1. **Create secrets** (see checklist above)
2. **Create production environment** with required reviewers
3. **Set up branch protection** for main branch
4. **Test workflows:**
   - Push to develop branch → watch test.yml run
   - Create PR → watch test.yml run and block merge until passing
   - Merge to main → watch build.yml and deploy-staging.yml run
   - Manually trigger deploy-prod.yml and approve

5. **Monitor deployments** in Actions tab
