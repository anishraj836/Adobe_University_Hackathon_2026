---
name: engagement-audit
description: Audits on-site visitor orientation (5-second rule), AI referral landing readiness, deep-link citation anchors, substantive content density, and conversion friction traps.
license: Apache-2.0
allowed-tools:
  - python
  - bash
---

# Engagement & Friction Audit Skill

## When to use
Use when diagnosing why visitors referred from AI assistants bounce immediately or fail to engage with the website.

## Inputs
- `target`: URL or path to local fixture bundle.
- Executed directly via `scripts/audit_engagement.py <target>` or imported as a module by the orchestrator.

## Procedure & Modular Architecture
Composed of 4 dedicated sub-modules:
1. `orientation_evaluator.py`: Evaluates 5-second cognitive orientation (H1 presence/clarity, meta description alignment, mobile viewport presence).
2. `hierarchy_evaluator.py`: Analyzes heading hierarchy progression (H1 -> H2 -> H3) and deep citation anchor attributes (`id`) for paragraph-level referencing.
3. `quotability_evaluator.py`: Simulates neural retrieval passage slicing (500-char windows), scoring Atomic Quotability (AQS) with hierarchical heading context injection and expletive pronoun filtering (Round 2 Appendix B & C).
4. `filler_evaluator.py`: Evaluates substantive Lexical Density Ratio (LDR) against corporate buzzword fluff with hero-zone exemption and informational anchor gating (Round 2 Appendix F).

## Guardrails & Compliance
- **Recommend-Only**: Passive inspection of rendered static DOM.
- **Zero Destructive Actions**: Never submits forms, clicks links, or authenticates.
