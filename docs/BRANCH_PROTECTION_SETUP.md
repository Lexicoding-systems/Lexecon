# Branch Protection and Security Setup Guide

This guide walks you through setting up branch protection rules, security features, and quality gates for the Lexecon repository.

## Table of Contents

- [Branch Protection Rules](#branch-protection-rules)
- [Required Status Checks](#required-status-checks)
- [Code Review Requirements](#code-review-requirements)
- [Security Features](#security-features)
- [Badge Setup](#badge-setup)
- [Troubleshooting](#troubleshooting)

---

## Branch Protection Rules

Branch protection rules enforce quality gates and prevent accidental changes to important branches.

### Setup Instructions

1. **Navigate to Branch Protection Settings**
   - Go to: `https://github.com/Lexicoding-systems/Lexecon/settings/branches`
   - Or: Repository → Settings → Branches → Branch protection rules

2. **Add Rule for `main` Branch**
   - Click "Add branch protection rule"
   - Branch name pattern: `main`

3. **Configure Protection Settings**

#### ✅ Require Pull Request Reviews
```
☑ Require a pull request before merging
  ☑ Require approvals: 1
  ☑ Dismiss stale pull request approvals when new commits are pushed
  ☐ Require review from Code Owners (optional - enable when CODEOWNERS file is added)
  ☑ Require approval of the most recent reviewable push
```

**Why**: Ensures code review even if you're the sole maintainer (forces you to review your own PRs).

#### ✅ Require Status Checks
```
☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  
  Required status checks:
  - test (Python 3.8, ubuntu-latest)
  - test (Python 3.9, ubuntu-latest)
  - test (Python 3.10, ubuntu-latest)
  - test (Python 3.11, ubuntu-latest)
  - test (Python 3.12, ubuntu-latest)
  - lint
  - format-check
  - security
  - build
  - CodeQL
  - dependency-review
```

**Why**: Prevents merging broken code, failing tests, or code with security vulnerabilities.

**Note**: Status checks will appear in the list after the first PR triggers them. You can add them progressively.

#### ✅ Require Conversation Resolution
```
☑ Require conversation resolution before merging
```

**Why**: Ensures all review comments are addressed.

#### ✅ Require Signed Commits (Recommended)
```
☑ Require signed commits
```

**Why**: Cryptographic verification of commit authorship (highly recommended for security-focused projects like Lexecon).

**Setup GPG Signing**:
```bash
# Generate GPG key
gpg --full-generate-key

# List keys
gpg --list-secret-keys --keyid-format=long

# Export public key
gpg --armor --export YOUR_KEY_ID

# Add to GitHub: Settings → SSH and GPG keys → New GPG key

# Configure git to sign commits
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

#### ✅ Require Linear History (Optional)
```
☑ Require linear history
```

**Why**: Keeps commit history clean (enforces rebase or squash merges).

#### ✅ Additional Settings
```
☑ Do not allow bypassing the above settings
☑ Restrict who can push to matching branches (optional - for teams)
☐ Allow force pushes (keep disabled)
☐ Allow deletions (keep disabled)
```

---

## Required Status Checks

Status checks that must pass before merging:

### CI Pipeline (`ci.yml`)

| Check | Purpose | Configuration |
|-------|---------|---------------|
| **test** | Run pytest on all OS/Python combinations | Matrix: 3 OS × 5 Python versions |
| **lint** | Run flake8 and mypy | Python 3.11 on Ubuntu |
| **format-check** | Verify black and isort formatting | Python 3.11 on Ubuntu |
| **security** | Run pip-audit and bandit | Python 3.11 on Ubuntu |
| **build** | Verify package builds correctly | Python 3.11 on Ubuntu |

### Security Checks

| Check | Purpose | Frequency |
|-------|---------|--------|
| **CodeQL** | Static analysis for security vulnerabilities | Every push + weekly |
| **dependency-review** | Check for vulnerable dependencies in PRs | Every PR |

### How to Handle Failures

**If a check fails**:
1. Click "Details" next to the failed check
2. Review the error logs
3. Fix the issue in your branch
4. Push the fix
5. Wait for checks to re-run

**Common failures**:
- **Test failures**: Fix the bug or update the test
- **Lint failures**: Run `make lint` locally
- **Format failures**: Run `make format` locally
- **Security failures**: Update vulnerable dependencies
- **Build failures**: Check for missing dependencies or syntax errors

---

## Code Review Requirements

### Self-Review Checklist

Even if you're reviewing your own PR, use this checklist:

- [ ] All CI checks pass
- [ ] Code follows style guidelines (black, isort, flake8)
- [ ] New code has tests
- [ ] Tests achieve adequate coverage (>80%)
- [ ] Documentation is updated (README, docstrings, etc.)
- [ ] No security vulnerabilities introduced
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages follow conventional commits
- [ ] No debug code or commented-out code left behind
- [ ] All review comments are resolved

### Review Guidelines

**What to look for**:
1. **Correctness**: Does the code do what it claims?
2. **Security**: Any vulnerabilities? Input validation? Cryptographic issues?
3. **Testing**: Are tests adequate and meaningful?
4. **Documentation**: Is the change documented?
5. **Design**: Is the design clean and maintainable?
6. **Performance**: Any performance concerns?

**How to review your own PR**:
1. Create PR and wait for CI to complete
2. Review the "Files changed" tab carefully
3. Add comments on your own code where needed
4. Wait 24 hours before merging (gives time for reflection)
5. Merge only when satisfied

---

## Security Features

### 1. Dependabot

**Already configured** in `.github/dependabot.yml`

**What it does**:
- Automatically checks for dependency updates weekly
- Creates PRs for security updates
- Groups minor/patch updates

**How to manage**:
- Review Dependabot PRs regularly
- Merge security updates promptly
- Test thoroughly before merging

### 2. CodeQL Analysis

**Already configured** in `.github/workflows/codeql.yml`

**What it does**:
- Scans code for security vulnerabilities
- Runs on every push and weekly
- Creates Security Advisories for findings

**How to review findings**:
1. Go to: Repository → Security → Code scanning alerts
2. Review each alert
3. Fix or dismiss with justification

### 3. Secret Scanning

**Enable in GitHub Settings**:
1. Go to: Repository → Settings → Security → Secret scanning
2. Enable "Secret scanning"
3. Enable "Push protection"

**What it does**:
- Scans for accidentally committed secrets
- Blocks pushes containing secrets
- Alerts you to exposed tokens/keys

### 4. Dependency Review

**Already configured** in `.github/workflows/dependency-review.yml`

**What it does**:
- Checks PRs for vulnerable dependencies
- Fails PR if moderate+ severity vulnerabilities found
- Comments summary in PR

### 5. Private Vulnerability Reporting

**Enable in GitHub Settings**:
1. Go to: Repository → Settings → Security → Private vulnerability reporting
2. Enable "Private vulnerability reporting"

**What it does**:
- Allows security researchers to privately report vulnerabilities
- Creates private advisories

---

## Badge Setup

Badges are already in README.md, but some require additional setup:

### 1. CI Badge ✅
**Already working** - Shows status of CI workflow

### 2. CodeQL Badge ✅
**Already working** - Shows status of CodeQL analysis

### 3. Codecov Badge ⚙️

**Setup required**:

1. **Sign up for Codecov**
   - Go to: https://codecov.io/
   - Sign in with GitHub
   - Add Lexecon repository

2. **Get Upload Token**
   - Go to: https://app.codecov.io/gh/Lexicoding-systems/Lexecon/settings
   - Copy the upload token

3. **Add Token to GitHub Secrets**
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Create new secret: `CODECOV_TOKEN`
   - Paste the token

4. **Update CI Workflow** (if needed)
   - Already configured in `.github/workflows/ci.yml`
   - Token is used via `CODECOV_TOKEN` secret

5. **Verify Badge**
   - After first upload, badge will show coverage %
   - May take 10-15 minutes for first report

### 4. OpenSSF Best Practices Badge ⚙️

**Setup required**:

1. **Create OpenSSF Account**
   - Go to: https://www.bestpractices.coreinfrastructure.org/
   - Sign in with GitHub

2. **Add Project**
   - Click "Add Project"
   - Enter repository URL: `https://github.com/Lexicoding-systems/Lexecon`

3. **Complete Badge Criteria**
   - Answer questions about your project
   - Many criteria are already met (tests, CI, documentation, etc.)
   - Work towards passing level

4. **Update Badge URL**
   - Once you get a project ID, update the README badge URL
   - Replace `9999` with your actual project ID

---

## Quality Gates Summary

### Passing Criteria

A PR can be merged only if:

✅ All CI tests pass (15 test jobs across OS/Python versions)
✅ Linting passes (flake8, mypy)
✅ Formatting is correct (black, isort)
✅ Security scans pass (pip-audit, bandit, CodeQL)
✅ Package builds successfully
✅ No vulnerable dependencies introduced
✅ At least 1 approval (even self-approval)
✅ All conversations resolved
✅ Branch is up to date with main

### This Prevents

🚫 Merging broken code
🚫 Merging code with failing tests
🚫 Merging code with security vulnerabilities
🚫 Merging code with poor formatting
🚫 Merging code without review
🚫 Accidentally pushing to main

---

## Troubleshooting

### Issue: "Required status checks are not passing"

**Solution**: 
- Check which checks failed
- Click "Details" to view logs
- Fix issues and push again

### Issue: "Branch is out of date"

**Solution**:
```bash
git checkout main
git pull origin main
git checkout your-branch
git rebase main
git push --force-with-lease
```

### Issue: "Required reviews not met"

**Solution**:
- If you're the only maintainer, you can approve your own PR
- Click "Review changes" → "Approve" → "Submit review"

### Issue: "Status checks not appearing in branch protection"

**Solution**:
- Status checks only appear after they run at least once
- Create a test PR to trigger all workflows
- Then they'll be available in branch protection settings

### Issue: "Codecov upload failing"

**Solution**:
- Verify `CODECOV_TOKEN` is set in repository secrets
- Check workflow logs for specific error
- Ensure you're using the correct token from Codecov dashboard

---

## Maintenance

### Regular Tasks

**Weekly**:
- [ ] Review and merge Dependabot PRs
- [ ] Check CodeQL security alerts
- [ ] Review any failed CI runs

**Monthly**:
- [ ] Update pinned GitHub Actions SHAs
- [ ] Review and update branch protection rules
- [ ] Check for new security best practices

**Quarterly**:
- [ ] Review test coverage reports
- [ ] Update security documentation
- [ ] Audit access permissions

### Updating Pinned Actions

GitHub Actions are pinned by SHA for security. To update:

1. **Check for new versions**
   - Visit action repository (e.g., `actions/checkout`)
   - Check releases for newer versions

2. **Get new SHA**
   - Go to the tag/release page
   - Find the full commit SHA (40 characters)

3. **Update workflow files**
   ```yaml
   # Old
   uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
   
   # New
   uses: actions/checkout@<new-sha> # v4.2.0
   ```

4. **Test thoroughly**
   - Create PR with updated actions
   - Ensure all workflows pass
   - Merge after verification

---

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Security Features](https://docs.github.com/en/code-security)
- [Codecov Documentation](https://docs.codecov.com/)
- [OpenSSF Best Practices](https://www.bestpractices.coreinfrastructure.org/en/criteria)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

## Questions?

If you have questions about these settings:
- Open an issue: https://github.com/Lexicoding-systems/Lexecon/issues
- Start a discussion: https://github.com/Lexicoding-systems/Lexecon/discussions
- Email: jacobporter@lexicoding.tech