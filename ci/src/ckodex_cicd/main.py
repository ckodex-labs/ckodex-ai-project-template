"""
Ckodex SSDLC Dagger CI/CD Pipeline (CKODEX Constitutional Standard).
Provides high-assurance, reproducible, containerized pipelines:
1. Linting & Code Formatting (Ruff)
2. Static Type Verification (Mypy)
3. High-Assurance Unit & Property Tests (Pytest)
4. Platform Preflight Diagnostics (Doctor)
5. Multi-Dimensional Conformance Evaluation (GAL 1 Invariants)
6. Continuous Vulnerability Management (Syft SBOM, Grype CVE gating, Gitleaks secrets audit)
7. Living Documentation Build (Hugo extended)
8. Multi-Layer OCI Artifact & Air-Gap Distribution Packaging
"""

from __future__ import annotations

import dagger
from dagger import dag, function, object_type


@object_type
class CkodexCicd:
    """High-assurance DevSecOps pipeline harness implemented in Dagger with Python SDK."""

    def _base_python(self, source: dagger.Directory) -> dagger.Container:
        """Returns base Python 3.12 container with UV installed and dependencies synced."""
        uv_bin = dag.container().from_("ghcr.io/astral-sh/uv:latest").file("/uv")
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_file("/usr/local/bin/uv", uv_bin)
            .with_env_variable("RAY_ENABLE_UV_RUN_RUNTIME_ENV", "0")
            .with_mounted_directory("/workspace", source)
            .with_workdir("/workspace")
            .with_exec(["uv", "sync", "--frozen", "--no-install-project"])
        )

    @function
    def lint(self, source: dagger.Directory) -> dagger.Container:
        """Run Ruff linter and code style formatting verification."""
        return (
            dag.container()
            .from_("ghcr.io/astral-sh/ruff:latest")
            .with_mounted_directory("/workspace", source)
            .with_workdir("/workspace")
            .with_exec(["/ruff", "check", "."])
            .with_exec(["/ruff", "format", "--check", "."])
        )

    @function
    def typecheck(self, source: dagger.Directory) -> dagger.Container:
        """Run Mypy static type verification across core kernel and adapters."""
        return self._base_python(source).with_exec(
            [
                "uv",
                "run",
                "mypy",
                "src/ckodex_aiops/kernel",
                "src/ckodex_aiops/validation",
                "src/ckodex_aiops/models",
                "src/ckodex_aiops/adapters/tracking",
                "src/ckodex_aiops/adapters/serving",
                "src/ckodex_aiops/adapters/distribution",
                "src/ckodex_aiops/adapters/ray/runtime.py",
            ]
        )

    @function
    def test(self, source: dagger.Directory) -> dagger.Container:
        """Run comprehensive unit and integration test suite via Pytest."""
        return (
            self._base_python(source)
            .with_env_variable("RAY_ADDRESS", "")
            .with_exec(["uv", "run", "pytest", "-v", "--durations=10"])
        )

    @function
    def doctor(self, source: dagger.Directory) -> dagger.Container:
        """Run Day-2 preflight platform health diagnostics (Rule #37)."""
        return self._base_python(source).with_exec(["uv", "run", "ckodex-aiops", "doctor"])

    @function
    def conformance(self, source: dagger.Directory) -> dagger.Container:
        """Run multi-dimensional transition conformance evaluation (Rule #20 & #21)."""
        return self._base_python(source).with_exec(["uv", "run", "ckodex-aiops", "conformance"])

    @function
    def scan_sbom(self, source: dagger.Directory) -> dagger.File:
        """Generate machine-verifiable Software Bill of Materials (SBOM) using Syft."""
        return (
            dag.container()
            .from_("anchore/syft:latest")
            .with_entrypoint([])
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["/syft", "dir:.", "-o", "spdx-json=/src/sbom.spdx.json"])
            .file("/src/sbom.spdx.json")
        )

    @function
    def scan_vulnerabilities(self, source: dagger.Directory) -> dagger.Container:
        """Audit dependencies against known CVEs using Grype with strict gating."""
        sbom = self.scan_sbom(source)
        return (
            dag.container()
            .from_("anchore/grype:latest")
            .with_entrypoint([])
            .with_file("/tmp/sbom.spdx.json", sbom)
            .with_exec(
                ["/grype", "sbom:/tmp/sbom.spdx.json", "--fail-on", "critical", "--output", "table"]
            )
        )

    @function
    def scan_secrets(self, source: dagger.Directory) -> dagger.Container:
        """Scan repository for leaked credentials and tokens using Gitleaks."""
        return (
            dag.container()
            .from_("zricethezav/gitleaks:latest")
            .with_entrypoint([])
            .with_mounted_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["gitleaks", "dir", "--verbose", "--redact", "/src"])
        )

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

    @function
    def pack_oci_template(self, source: dagger.Directory) -> dagger.Directory:
        """Package template as an OCI Image Layout artifact with embedded SBOMs and OSCAL."""
        return (
            self._base_python(source)
            .with_exec(
                [
                    "uv",
                    "run",
                    "ckodex-aiops",
                    "oci",
                    "pack",
                    "--source",
                    ".",
                    "--out",
                    "/dist/oci-template",
                ]
            )
            .directory("/dist/oci-template")
        )

    @function
    def pack_airgap(self, source: dagger.Directory) -> dagger.File:
        """Build and cryptographically verify air-gap distribution bundle (Rule #40)."""
        return (
            self._base_python(source)
            .with_exec(
                [
                    "uv",
                    "run",
                    "ckodex-aiops",
                    "airgap-pack",
                    "--name",
                    "ckodex-ci-bundle",
                    "--out",
                    "/dist/airgap-bundle.tar.gz",
                ]
            )
            .with_exec(
                [
                    "uv",
                    "run",
                    "ckodex-aiops",
                    "airgap-verify",
                    "--path",
                    "/dist/airgap-bundle.tar.gz",
                ]
            )
            .file("/dist/airgap-bundle.tar.gz")
        )

    @function
    async def all(self, source: dagger.Directory) -> str:
        """Execute complete SSDLC pipeline: Lint, Typecheck, Scan, Conformance, Docs, and Build."""
        # 1. Lint & Format
        await self.lint(source).sync()
        # 2. Secret Scan
        await self.scan_secrets(source).sync()
        # 3. Vulnerability Audit
        await self.scan_vulnerabilities(source).sync()
        # 4. Typecheck
        await self.typecheck(source).sync()
        # 5. Doctor Preflight
        await self.doctor(source).sync()
        # 6. Conformance Evaluation
        await self.conformance(source).sync()
        # 7. Living Documentation Compilation
        await self.build_docs(source).sync()
        # 8. High-Assurance Unit & Property Tests
        await self.test(source).sync()
        # 9. OCI Template Packaging
        await self.pack_oci_template(source).sync()

        return (
            "CKODEX SSDLC pipeline passed: 0 vulnerabilities (critical), "
            "0 leaked secrets, 100% tests, conformance & OCI packaging verified."
        )
