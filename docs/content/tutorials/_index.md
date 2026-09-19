---
title: "Tutorials"
description: "Hands-on, learning-oriented lessons to acquire practical experience with the CKODEX AIOps platform."
weight: 10
---

# Tutorials (Learning-Oriented)

Welcome to the **CKODEX AIOps** tutorial track. These tutorials are designed for developers, platform engineers, and DevSecOps practitioners who want a structured, guided journey through the platform's core workflows.

## Learning Goals

By completing these tutorials, you will learn how to:
1. Initialize the platform and verify preflight hardware accelerators (**Apple Silicon Metal MPS** / **NVIDIA CUDA**).
2. Execute an end-to-end Kedro DAG producing columnar Lance datasets and memory-safe Safetensors checkpoints.
3. Mint and verify cryptographic **In-toto SLSA v1.0** provenance attestations.
4. Experience the autonomic **Day-2 Reconciler** detecting drift and self-healing storage fragments.

---

## Available Tutorials

1. **[Your First Pipeline & SLSA Attestation](/tutorials/getting-started/)**  
   *Duration: ~15 minutes*  
   Take a fresh clone from preflight check, through Polars feature extraction, Ray distributed embedding, PyTorch training, to a signed In-toto SLSA v1.0 provenance receipt.

2. **[Observing & Healing Drift with the Day-2 Reconciler](/tutorials/first-reconciliation/)**  
   *Duration: ~10 minutes*  
   Inject synthetic fragment drift into Lance storage, watch the StateVector transition from `NORMAL` to `DEGRADED`, and trigger the autonomic reconciler to converge back to the active baseline profile.
