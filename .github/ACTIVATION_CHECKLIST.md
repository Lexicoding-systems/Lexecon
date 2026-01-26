# GitHub Actions Activation Checklist

After pushing these workflows to GitHub, complete the following setup:

## Phase 1: Enable & Test (5 minutes)

- [ ] Push branch to GitHub: `git push origin main`
- [ ] Go to Actions tab → verify workflows are listed:
  - Test & Lint
  - Build & Push Docker Image
  - Deploy to Staging
  - Deploy to Production
- [ ] Create a test branch and open a pull request
  - Watch `test.yml` run automatically
  - Verify linting and tests execute
  - Verify PR is blocked if tests fail

## Phase 2: Configure Staging Deployment (10 minutes)

### Staging Server Setup (one-time)
- [ ] Have access to staging server (SSH)
- [ ] Server has Docker and docker-compose installed
- [ ] `/opt/lexecon/` directory exists (or adjust STAGING_DEPLOY_PATH)
- [ ] Create deploy user: `sudo useradd -m -s /bin/bash deploybot`
- [ ] Add GitHub's SSH key to deploybot authorized_keys

### GitHub Secrets
1. Go to Settings → Secrets and variables → Actions
2. Create new secrets:

```
STAGING_DEPLOY_KEY
  - Content: SSH private key (paste output of: cat ~/.ssh/id_rsa)
  - Or generate new: ssh-keygen -t ed25519 -f lexecon_deploy -C "github-actions"

STAGING_DEPLOY_HOST
  - Value: staging.lexecon.local (or your staging IP/hostname)

STAGING_DEPLOY_USER
  - Value: deploybot

STAGING_DEPLOY_PATH
  - Value: /opt/lexecon (or where Lexecon is deployed)

SLACK_WEBHOOK
  - Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  - Get from: Slack workspace → Settings → Apps → Incoming Webhooks
```

### Test Staging Deployment
- [ ] Merge PR to main
- [ ] Watch Actions tab → Deploy to Staging runs
- [ ] Verify deployment notification in Slack
- [ ] Check staging server: `curl http://staging.lexecon.local/health`
- [ ] Server should return 200 with health details

## Phase 3: Configure Production Deployment (15 minutes)

### Production Server Setup (one-time)
- [ ] Have access to production server (SSH)
- [ ] Server has Docker and docker-compose installed
- [ ] `/opt/lexecon/` directory exists (or adjust PROD_DEPLOY_PATH)
- [ ] Create deploy user: `sudo useradd -m -s /bin/bash deploybot`
- [ ] Add GitHub SSH key to deploybot authorized_keys

### GitHub Secrets
1. Go to Settings → Secrets and variables → Actions
2. Create secrets (same pattern as staging):

```
PROD_DEPLOY_KEY
  - SSH private key for production server

PROD_DEPLOY_HOST
  - Value: api.lexecon.io (or production IP/hostname)

PROD_DEPLOY_USER
  - Value: deploybot

PROD_DEPLOY_PATH
  - Value: /opt/lexecon
```

(SLACK_WEBHOOK already created in Phase 2)

### GitHub Environment Protection
1. Go to Settings → Environments
2. Create new environment:
   - Name: `production`
   - Click "Create environment"
3. Configure protection rules:
   - [x] Required reviewers
   - Add reviewers (e.g., @your-github-username)
   - [x] Require reviewers to approve before deploying
4. Save

### Test Production Deployment
- [ ] Go to Actions tab → Deploy to Production
- [ ] Click "Run workflow"
- [ ] Enter version: `1.0.0`
- [ ] Required reviewers receive approval notification
- [ ] Review and approve the deployment
- [ ] Watch deployment run
- [ ] Verify notification in Slack
- [ ] Check production server: `curl https://api.lexecon.io/health`

## Phase 4: Branch Protection Rules (5 minutes)

1. Go to Settings → Branches
2. Click "Add rule" (or edit main branch rule)
3. Branch name pattern: `main`
4. Configure rules:
   - [x] Require a pull request before merging
   - [x] Require status checks to pass before merging
     - Search for status check: `test`
     - Select: `test`
   - [x] Require branches to be up to date before merging
   - [x] Include administrators
5. Save changes

### Verify Branch Protection
- [ ] Try to push directly to main: `git push origin main` (should fail)
- [ ] Create branch and PR → can only merge after tests pass
- [ ] Approve workflow in PR → can merge

## Phase 5: Docker Registry Access (optional, if private images)

If using private Docker registry:

1. Go to Settings → Secrets and variables → Actions
2. Create secret: `REGISTRY_PASSWORD`
3. Update `build.yml` to use: `${{ secrets.REGISTRY_PASSWORD }}`

## Verification Checklist

After all setup:

- [ ] `test.yml` runs on every push/PR
- [ ] `build.yml` runs after successful tests on main
- [ ] Docker images pushed to `ghcr.io/lexicoding-systems/lexecon`
- [ ] `deploy-staging.yml` auto-deploys after build
- [ ] Staging notifications appear in Slack
- [ ] `deploy-prod.yml` available via Actions → Run workflow
- [ ] Production deployment requires reviewer approval
- [ ] Production notifications appear in Slack
- [ ] Branch protection enforces test passage before merge
- [ ] Admins cannot bypass checks

## Troubleshooting

### Workflows not appearing in Actions tab
- [ ] Check: `.github/workflows/` directory exists
- [ ] Check: Files are `.yml` format
- [ ] Check: Pushed to GitHub (not just local)
- [ ] Refresh Actions page

### Tests fail but should pass
- [ ] Verify Python version: 3.11+
- [ ] Verify dependencies: `pip install -e .`
- [ ] Check locally: `pytest tests/ -v --cov`
- [ ] View workflow logs in Actions tab

### Staging deployment fails
- [ ] Check SSH key is correctly pasted (no extra whitespace)
- [ ] Verify server is reachable: `ssh -i key deploybot@server`
- [ ] Check docker-compose.yml exists on server
- [ ] Check /health endpoint is implemented
- [ ] View full logs in Actions tab

### Production approval not received
- [ ] Check environment exists: Settings → Environments → production
- [ ] Check reviewers configured
- [ ] Check notification settings in GitHub
- [ ] Check Slack is connected (if using Slack notifications)

### Docker image not pushing
- [ ] Check permissions on GitHub token
- [ ] Verify you can authenticate locally: `docker login ghcr.io`
- [ ] Check image name format in build.yml
- [ ] View build logs for details

## Support

Detailed setup guide: See `.github/WORKFLOWS_SETUP.md`

Questions? Check:
1. Workflow YAML syntax
2. Secret names match workflow references
3. Server SSH keys and permissions
4. Network connectivity from GitHub runners to servers
