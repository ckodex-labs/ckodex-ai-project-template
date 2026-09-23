# Contributing to CKODEX AIOps

Thank you for contributing to the CKODEX AIOps Platform. This project adheres to **CKODEX GAL 1** constitutional standards:
> *Pure Kernel. Shared Validation. Explicit Transport. Evidence Everywhere. Vector State, Not Booleans. Proof Before Authority-Bearing Side Effects. Receipts After Execution. Day-2 by Default.*

---

## 1. Prerequisites

Ensure you have the following installed on your workstation:
- **Python**: 3.12+
- **UV**: Fast Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`)
- **Just**: Modern command runner (`brew install just`)
- **Hugo Extended**: Living documentation generator (`brew install hugo`)
- **Dagger**: Hermetic container CI/CD engine (`brew install dagger/tap/dagger`)

---

## 2. Developer Workflow

### Step 1: Clone & Setup
```bash
git clone https://github.com/ckodex-labs/ckodex-ai-project-template.git
cd ckodex-ai-project-template

# Install and synchronize virtual environment deterministically
just install
```

### Step 2: Preflight Diagnostics
Verify that your local hardware (including macOS Apple Silicon Metal MPS if on Mac), compute, and storage engines are healthy:
```bash
just doctor
```

### Step 3: Fast Inner-Loop Testing
Run fast unit tests in < 2 seconds during active development:
```bash
just test-fast
```

Run the full distributed test suite (128 tests):
```bash
just test
```

### Step 4: Code Formatting & Linting
We enforce 100% clean formatting and linting via **Ruff**:
```bash
# Auto-format and fix lints
just format

# Lint check only
just lint
```

---

## 3. Git Commit Conventions

We follow Conventional Commits:
```text
<type>(<scope>): <short imperative description>

[optional body explaining rationale]
```

Allowed types:
- `feat`: New capability or subsystem
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or updating test suites
- `docs`: Documentation updates in Hugo or README
- `ops`: Deployments, Helmfile, Compose, Justfile, or CI/CD changes

---

## 4. Submitting Pull Requests

1. Create a descriptive feature branch: `git checkout -b feat/my-enhancement`.
2. Ensure `just lint` and `just test` pass 100% green.
3. If modifying public APIs or adding Day-2 commands, update the corresponding Hugo documentation under `docs/content/`.
4. Submit a Pull Request targeting `main`. Our Dagger SSDLC CI will automatically execute hermetic lint, security scans (Gitleaks, Syft, Grype), and test matrices.
