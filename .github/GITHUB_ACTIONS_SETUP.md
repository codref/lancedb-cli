# GitHub Actions Setup Guide

This project includes GitHub Actions workflows to automatically build and publish your package to PyPI.

## Workflows

### 1. **test-build.yml** (Automatic on push/PR)
- Runs tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
- Tests package import and help command
- Runs on every push to `main` or `develop` branches
- Runs on all pull requests

### 2. **build-and-publish.yml** (Manual trigger on tags)
- Builds the package distribution
- Validates with `twine`
- Publishes to PyPI
- Triggers automatically when you push a tag matching `v*` (e.g., `v0.1.0`)

## Setup Instructions

### Step 1: Create a PyPI Account

1. Go to https://pypi.org/
2. Click "Sign up" and create an account
3. (Optional) Register your project name to reserve it

### Step 2: Generate a PyPI API Token

1. Log in to PyPI
2. Go to https://pypi.org/manage/account/
3. Click "API tokens" in the left sidebar
4. Click "Add API token"
5. **Important**: 
   - Set scope to "Entire account" (or specific to your project if available)
   - Copy the token immediately - you won't be able to see it again
   - Format: `pypi-AgEI...` (starts with `pypi-`)

### Step 3: Add Secret to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI token
6. Click **Add secret**

### Step 4: Configure your package

Make sure these values are updated in `pyproject.toml` and `setup.py`:
- `name` - Your package name (e.g., `lancedb-cli`)
- `version` - Current version (e.g., `0.1.0`)
- `author` - Your name
- `author_email` - Your email
- `url` - Your GitHub repository URL

### Step 5: First Publish

To manually publish without waiting for a tag:

```bash
# Build locally
python -m build

# Upload (requires PyPI token or credentials)
twine upload dist/*
```

## Publishing a New Release

Once everything is configured, publishing is simple:

```bash
# 1. Update version in pyproject.toml and setup.py
# 2. Commit changes
git add pyproject.toml setup.py
git commit -m "Bump version to 0.2.0"

# 3. Create and push a tag
git tag v0.2.0
git push origin v0.2.0
```

The GitHub Action will automatically:
- ✅ Build the package
- ✅ Validate it with twine
- ✅ Upload to PyPI
- ✅ Create a GitHub Release (optional - requires permissions)

## Verification

After publishing, verify your package is on PyPI:

```bash
pip install lancedb-cli
```

Check PyPI: https://pypi.org/project/lancedb-cli/

## Troubleshooting

### "PYPI_API_TOKEN not found"
- Verify the secret exists in Settings → Secrets
- Check the secret name is exactly `PYPI_API_TOKEN`
- Ensure it's in the correct repository

### "Invalid token format"
- PyPI tokens should start with `pypi-`
- Copy the full token from PyPI account page
- Don't include quotes or spaces

### "Package already exists"
- The workflow uses `--skip-existing` flag
- You can't overwrite an existing version
- Increment the version number for new releases

### Test build fails
- Check Python version compatibility in your code
- Review error logs in GitHub Actions UI
- Run tests locally: `pytest tests/`

## Advanced: Test PyPI (Staging)

To test before publishing to production PyPI:

1. Create account on https://test.pypi.org/
2. Generate API token on test.pypi.org
3. Add another secret: `TEST_PYPI_API_TOKEN`
4. Create `test-publish.yml` workflow with:

```yaml
env:
  TWINE_REPOSITORY: testpypi
  TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
```

Then test with:
```bash
pip install -i https://test.pypi.org/simple/ lancedb-cli
```

## Security Notes

- Never commit your PyPI token to the repository
- Use repository secrets for sensitive data
- Consider using organization-level secrets for shared tokens
- Rotate tokens periodically
- Use specific project-scoped tokens if PyPI offers them

## More Information

- [PyPI Help](https://pypi.org/help/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
