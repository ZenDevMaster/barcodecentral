# GitHub Setup Guide for Barcode Central

This guide covers setting up, deploying, and maintaining the Barcode Central project using GitHub.

## Table of Contents

1. [Initial Repository Setup](#initial-repository-setup)
2. [Clone and Deploy](#clone-and-deploy)
3. [Development Workflow](#development-workflow)
4. [Branch Strategy](#branch-strategy)
5. [Commit Message Conventions](#commit-message-conventions)
6. [Pull Request Process](#pull-request-process)
7. [CI/CD with GitHub Actions](#cicd-with-github-actions)
8. [Docker Hub Integration](#docker-hub-integration)
9. [Release Management](#release-management)

---

## Initial Repository Setup

### For Repository Owners

If you're setting up the repository for the first time:

```bash
# 1. Navigate to your project directory
cd /path/to/barcode-central

# 2. Initialize git repository (if not already done)
git init

# 3. Add all files
git add .

# 4. Create initial commit
git commit -m "Initial commit: Barcode Central v1.0.0"

# 5. Add GitHub remote
git remote add origin https://github.com/ZenDevMaster/barcodecentral.git

# 6. Push to GitHub
git branch -M main
git push -u origin main
```

### Verify Repository Setup

```bash
# Check remote configuration
git remote -v

# Should show:
# origin  https://github.com/ZenDevMaster/barcodecentral.git (fetch)
# origin  https://github.com/ZenDevMaster/barcodecentral.git (push)
```

---

## Clone and Deploy

### For New Users/Contributors

#### 1. Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/ZenDevMaster/barcodecentral.git
cd barcodecentral

# Or clone via SSH (if you have SSH keys configured)
git clone git@github.com:ZenDevMaster/barcodecentral.git
cd barcodecentral
```

#### 2. Initial Setup

```bash
# Create required directories
mkdir -p logs previews

# Copy environment configuration
cp .env.production.example .env

# Edit environment variables
nano .env
```

**Important**: Update these critical settings in `.env`:
- `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `LOGIN_USER` - Your admin username
- `LOGIN_PASSWORD` - Your admin password

#### 3. Configure Printers (Optional)

```bash
# Copy printer configuration template
cp printers.json.example printers.json

# Edit with your printer details
nano printers.json
```

You can also configure printers later via the web interface.

#### 4. Deploy with Docker

```bash
# Build and start the application
./scripts/deploy.sh --build

# Or manually with docker-compose
docker-compose up -d --build
```

#### 5. Verify Deployment

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:5000/api/health
```

Access the application at: `http://localhost:5000`

### Deploy Directly from GitHub

You can also deploy without cloning by building directly from GitHub:

```bash
# Create a docker-compose.yml with GitHub context
docker-compose -f docker-compose.github.yml up -d
```

See [Docker Hub Integration](#docker-hub-integration) section for details.

---

## Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/ZenDevMaster/barcodecentral.git
cd barcodecentral

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing

# 4. Create development environment
cp .env.example .env
nano .env

# 5. Create required directories
mkdir -p logs previews

# 6. Run development server
./run_dev.sh
```

### Making Changes

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# ... edit files ...

# 3. Test your changes
./run_tests.sh

# 4. Stage changes
git add .

# 5. Commit with descriptive message
git commit -m "feat: add new feature description"

# 6. Push to GitHub
git push origin feature/your-feature-name

# 7. Create Pull Request on GitHub
```

---

## Branch Strategy

We follow a simplified Git Flow strategy:

### Main Branches

- **`main`** - Production-ready code
  - Always stable and deployable
  - Protected branch (requires PR reviews)
  - Tagged with version numbers

- **`develop`** (optional) - Integration branch
  - Latest development changes
  - Merged into `main` for releases

### Supporting Branches

- **`feature/*`** - New features
  - Branch from: `main` or `develop`
  - Merge into: `develop` or `main`
  - Example: `feature/printer-status-monitoring`

- **`bugfix/*`** - Bug fixes
  - Branch from: `main` or `develop`
  - Merge into: `develop` or `main`
  - Example: `bugfix/preview-generation-error`

- **`hotfix/*`** - Critical production fixes
  - Branch from: `main`
  - Merge into: `main` and `develop`
  - Example: `hotfix/security-patch-1.0.1`

- **`release/*`** - Release preparation
  - Branch from: `develop`
  - Merge into: `main` and `develop`
  - Example: `release/1.1.0`

### Branch Naming Convention

```
feature/short-description
bugfix/issue-number-description
hotfix/version-description
release/version-number
```

---

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies
- **ci**: CI/CD changes
- **build**: Build system changes

### Examples

```bash
# Feature
git commit -m "feat(printer): add printer status monitoring"

# Bug fix
git commit -m "fix(preview): resolve image generation timeout"

# Documentation
git commit -m "docs(readme): update installation instructions"

# Breaking change
git commit -m "feat(api)!: change printer API response format

BREAKING CHANGE: Printer API now returns nested object structure"

# With issue reference
git commit -m "fix(auth): resolve session timeout issue

Fixes #123"
```

---

## Pull Request Process

### Creating a Pull Request

1. **Push your branch to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open Pull Request on GitHub**
   - Go to repository on GitHub
   - Click "Pull requests" → "New pull request"
   - Select your branch
   - Fill in the PR template

3. **PR Title Format**
   ```
   feat(scope): Brief description of changes
   ```

### PR Checklist

Before submitting a PR, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`./run_tests.sh`)
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive data in commits
- [ ] `.env` and `printers.json` not committed
- [ ] PR description is clear and complete

### Review Process

1. **Automated Checks** (if CI/CD configured)
   - Tests must pass
   - Code quality checks
   - Docker build succeeds

2. **Code Review**
   - At least one approval required
   - Address reviewer feedback
   - Update PR as needed

3. **Merge**
   - Squash and merge (preferred)
   - Rebase and merge (for clean history)
   - Merge commit (for feature branches)

---

## CI/CD with GitHub Actions

### Recommended Workflows

Create `.github/workflows/` directory with these workflows:

#### 1. Test Workflow (`.github/workflows/test.yml`)

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

#### 2. Docker Build Workflow (`.github/workflows/docker.yml`)

```yaml
name: Docker Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Build Docker image
      run: |
        docker build -t barcodecentral:test .
    
    - name: Test Docker image
      run: |
        docker run -d --name test-container barcodecentral:test
        sleep 10
        docker logs test-container
        docker stop test-container
```

#### 3. Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
```

### Setting Up Secrets

Add these secrets in GitHub repository settings:

- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token
- `CODECOV_TOKEN` - Codecov token (optional)

---

## Docker Hub Integration

### Manual Push to Docker Hub

```bash
# 1. Build image
docker build -t zendevmaster/barcodecentral:latest .
docker build -t zendevmaster/barcodecentral:1.0.0 .

# 2. Login to Docker Hub
docker login

# 3. Push images
docker push zendevmaster/barcodecentral:latest
docker push zendevmaster/barcodecentral:1.0.0
```

### Automated Docker Hub Builds

Add to `.github/workflows/docker-publish.yml`:

```yaml
name: Publish Docker Image

on:
  push:
    tags: [ 'v*' ]

jobs:
  push:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: zendevmaster/barcodecentral
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

### Deploy from Docker Hub

```bash
# Pull and run from Docker Hub
docker pull zendevmaster/barcodecentral:latest
docker run -d -p 5000:5000 --env-file .env zendevmaster/barcodecentral:latest
```

---

## Release Management

### Creating a Release

1. **Update Version**
   ```bash
   # Update VERSION file
   echo "1.1.0" > VERSION
   
   # Update version in relevant files
   # - README.md badges
   # - docker-compose.yml labels
   # - Any version constants
   ```

2. **Update Changelog**
   ```bash
   # Update CHANGELOG.md with release notes
   nano CHANGELOG.md
   ```

3. **Commit Version Changes**
   ```bash
   git add VERSION CHANGELOG.md
   git commit -m "chore: bump version to 1.1.0"
   ```

4. **Create Git Tag**
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

5. **Create GitHub Release**
   - Go to GitHub repository
   - Click "Releases" → "Create a new release"
   - Select tag `v1.1.0`
   - Add release notes
   - Publish release

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x) - Breaking changes
- **MINOR** (x.1.x) - New features (backward compatible)
- **PATCH** (x.x.1) - Bug fixes (backward compatible)

Examples:
- `1.0.0` → `1.0.1` - Bug fix
- `1.0.1` → `1.1.0` - New feature
- `1.1.0` → `2.0.0` - Breaking change

---

## Best Practices

### Security

- ✅ Never commit `.env` files
- ✅ Never commit `printers.json` with real IPs
- ✅ Use `.env.example` for templates
- ✅ Rotate secrets regularly
- ✅ Use GitHub secrets for CI/CD

### Code Quality

- ✅ Write tests for new features
- ✅ Run tests before pushing
- ✅ Keep commits atomic and focused
- ✅ Write clear commit messages
- ✅ Update documentation

### Collaboration

- ✅ Create issues for bugs/features
- ✅ Reference issues in commits
- ✅ Review PRs thoroughly
- ✅ Be respectful in discussions
- ✅ Keep PRs focused and small

---

## Troubleshooting

### Common Issues

**Problem**: Push rejected due to large files
```bash
# Solution: Check for accidentally committed large files
git ls-files --others --ignored --exclude-standard
```

**Problem**: Merge conflicts
```bash
# Solution: Resolve conflicts manually
git pull origin main
# Fix conflicts in files
git add .
git commit -m "fix: resolve merge conflicts"
```

**Problem**: Need to undo last commit
```bash
# Undo commit but keep changes
git reset --soft HEAD~1

# Undo commit and discard changes
git reset --hard HEAD~1
```

---

## Additional Resources

- [GitHub Documentation](https://docs.github.com/)
- [Git Documentation](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Need Help?**

- 📖 Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- 🐛 Report bugs via [GitHub Issues](https://github.com/ZenDevMaster/barcodecentral/issues)
- 💬 Ask questions in [GitHub Discussions](https://github.com/ZenDevMaster/barcodecentral/discussions)