---
title: "How to Build and Deploy Hugo Documentation to GitHub Pages with Dagger"
description: "Task-oriented guide for compiling living Hugo documentation inside containerized Dagger pipelines and publishing to GitHub Pages."
weight: 70
---

# How to Build and Deploy Hugo Documentation to GitHub Pages with Dagger

## Problem
You need to publish living architecture, compliance, and API documentation to GitHub Pages while maintaining hermetic reproducibility, zero drift between local and CI environments, and compliance with **Rule #41 (Invisible Excellence)**.

---

## Prerequisites
- [Dagger CLI](https://docs.dagger.io/install) (`>=0.12.0`)
- Git repository with GitHub Pages enabled in Repository Settings (`Settings` -> `Pages` -> `Source: GitHub Actions`)
- Hugo Extended (optional for local preview, containerized via Dagger in CI)

---

## Step 1: Verify the Dagger Pipeline Function

The CI pipeline defines a typed `build_docs` method in `ci/src/ckodex_cicd/main.py`:

```python
@function
def build_docs(self, source: dagger.Directory, base_url: str = "") -> dagger.Directory:
    """Build living Hugo architecture & DevSecOps documentation site."""
    cmd = ["hugo", "--destination", "/src/docs/public", "--cleanDestinationDir"]
    if base_url:
        cmd.extend(["--baseURL", base_url])
    return (
        dag.container()
        .from_("klakegg/hugo:ext-ubuntu")
        .with_entrypoint([])
        .with_mounted_directory("/src", source)
        .with_workdir("/src/docs")
        .with_exec(cmd)
        .directory("/src/docs/public")
    )
```

---

## Step 2: Test Containerized Compilation Locally

Build the documentation site using Dagger with an overridden `baseURL` matching your GitHub Pages organization and repository:

```bash
# Export the compiled site into docs/public
just docs-pages-build base_url="https://ckodex-labs.github.io/ckodex-ai-project-template/"
```

Inspect the generated static artifacts:
```bash
ls -la docs/public/
# Verify index.html, 404.html, and section directories exist
```

---

## Step 3: Configure the GitHub Pages Workflow

The GitHub Actions workflow operates as a thin dispatching layer in `.github/workflows/pages.yml`:

```yaml
name: Deploy Hugo Docs to GitHub Pages (Dagger Engine)

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    name: Build Hugo Docs (Dagger)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source Code
        uses: actions/checkout@v4

      - name: Build and Export Static Site via Dagger
        uses: dagger/dagger-for-github@v7
        with:
          version: "0.21.8"
          verb: call
          args: build-docs --source . --base-url "https://ckodex-labs.github.io/ckodex-ai-project-template/" export --path ./public
          workdir: ci

      - name: Upload GitHub Pages Artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    name: Deploy to GitHub Pages
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy Pages Site
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## Step 4: Configure GitHub Repository Settings

1. Navigate to your GitHub repository: `https://github.com/<org>/<repo>/settings/pages`.
2. Under **Build and deployment**:
   - **Source**: Select `GitHub Actions`.
3. Push a commit to `main` or manually trigger the workflow via the GitHub Actions tab (`Run workflow`).
4. Once completed, your documentation site will be live at:
   `https://<org>.github.io/<repo>/`

---

## Step 5: Setting a Custom Domain (Optional)

If your organization uses a custom domain (such as `https://docs.ckodex.ai`):
1. Add a file `docs/static/CNAME` containing your domain:
   ```text
   docs.ckodex.ai
   ```
2. Update the `base_url` argument in `.github/workflows/pages.yml`:
   ```yaml
   args: build-docs --source . --base-url "https://docs.ckodex.ai/" export --path ./public
   ```
3. Commit and push to `main`.
