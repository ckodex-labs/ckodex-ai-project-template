---
title: "Explanation"
description: "Deep conceptual and architectural rationale explaining the design principles of the CKODEX AIOps platform."
weight: 40
---

# Explanation (Understanding-Oriented)

This section provides deep architectural background, theoretical foundations, and the constitutional rationale behind the **CKODEX GAL 1** design.

## Conceptual Topics

- **[Why the Semantic Kernel is Pure](/explanation/pure-semantic-kernel/)**  
  The critical distinction between domain semantics and runtime substrates, and why framework leakage causes fragility.

- **[The Four Truth Channels and State Coherence](/explanation/four-truth-channels/)**  
  Why telemetry, execution, decisions, and evidence must remain distinct, and how cross-channel decoherence is detected.

- **[Vector State Algebra & Anti-Dominance](/explanation/vector-state-algebra/)**  
  Why boolean `PASS/FAIL` is inadequate for governed reality, and why hard anti-invariants must strictly dominate aggregate scores.

- **[The Canonical Day-2 Control Loop](/explanation/day2-control-loop/)**  
  Deep-dive into the autonomic loop: `OBSERVE -> DETECT -> DIAGNOSE -> DEGRADE -> CONTAIN -> RECOVER -> VERIFY -> RECONCILE`.

- **[Zero-Trust Authority & Capability Attenuation](/explanation/zero-trust-authority/)**  
  How the standing authority hierarchy and ephemeral, bounded capability leases prevent privilege escalation.

- **[Why Diátaxis, Hugo, and Dagger: Hermetic Documentation as Code](/explanation/diataxis-and-docs-as-code/)**  
  Why documentation is treated as a compiled, immutable engineering artifact and built hermetically in containerized CI.
