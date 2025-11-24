# GitHub Actions Workflows

This directory contains GitHub Actions workflow configurations for CI/CD automation.

## Available Workflows

Currently, this directory is prepared for future CI/CD workflows. Below are recommended workflows to implement:

### 1. Test Workflow (`test.yml`)

Automatically run tests on every push and pull request.

**Triggers:**
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches

**Actions:**
- Set up Python environment
- Install dependencies
- Run pytest with coverage
- Upload coverage reports

### 2. Docker Build Workflow (`docker.yml`)

Build and test Docker images.

**Triggers:**
- Push to `main` branch
- New version tags (`v*`)
- Pull requests to `main` branch

**Actions:**
- Build Docker image
- Run container health checks
- Test application startup

### 3. Docker Publish Workflow (`docker-publish.yml`)

Publish Docker images to Docker Hub.

**Triggers:**
- New version tags (`v*`)

**Actions:**
- Build Docker image
- Login to Docker Hub
- Push image with version tag and `latest` tag

### 4. Release Workflow (`release.yml`)

Create GitHub releases automatically.

**Triggers:**
- New version tags (`v*`)

**Actions:**
- Create GitHub release
- Generate release notes
- Attach build artifacts

### 5. Code Quality Workflow (`quality.yml`)

Check code quality and style.

**Triggers:**
- Pull requests

**Actions:**
- Run linters (flake8, pylint)
- Check code formatting (black)
- Run security checks (bandit)

## Implementation Guide

To implement these workflows, create YAML files in this directory following the examples in [GITHUB_SETUP.md](../../GITHUB_SETUP.md#cicd-with-github-actions).

### Example: Creating a Test Workflow

1. Create `.github/workflows/test.yml`
2. Add workflow configuration
3. Commit and push to GitHub
4. Workflow will run automatically on next push/PR

### Required Secrets

Some workflows require GitHub secrets to be configured:

- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token
- `CODECOV_TOKEN` - Codecov token (optional)

Configure these in: Repository Settings → Secrets and variables → Actions

## Workflow Status Badges

Add workflow status badges to README.md:

```markdown
![Tests](https://github.com/ZenDevMaster/barcodecentral/workflows/Tests/badge.svg)
![Docker Build](https://github.com/ZenDevMaster/barcodecentral/workflows/Docker%20Build/badge.svg)
```

## Best Practices

1. **Keep workflows focused** - One workflow per purpose
2. **Use caching** - Cache dependencies to speed up builds
3. **Fail fast** - Stop on first error to save resources
4. **Use matrix builds** - Test multiple Python versions if needed
5. **Secure secrets** - Never expose secrets in logs
6. **Document workflows** - Add comments explaining complex steps

## Troubleshooting

### Workflow Not Running

- Check workflow triggers match your branch/tag
- Verify YAML syntax is correct
- Check repository permissions

### Workflow Failing

- Review workflow logs in GitHub Actions tab
- Test commands locally first
- Check for missing secrets or permissions

### Slow Workflows

- Implement dependency caching
- Parallelize independent jobs
- Use smaller Docker base images

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)

## Contributing

When adding new workflows:

1. Test locally using [act](https://github.com/nektos/act) if possible
2. Document the workflow purpose and triggers
3. Add status badges to README.md
4. Update this README with workflow details