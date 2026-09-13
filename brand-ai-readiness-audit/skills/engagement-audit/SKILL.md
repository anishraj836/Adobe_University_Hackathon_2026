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
Composed of 5 dedicated sub-modules:
1. `orientation_evaluator.py`: Evaluates 5-second cognitive orientation (H1 presence/clarity, meta description alignment, mobile viewport presence).
2. `hierarchy_evaluator.py`: Analyzes heading hierarchy progression (H1 -> H2 -> H3) and deep citation anchor attributes (`id`) for paragraph-level referencing.
3. `quotability_evaluator.py`: Deterministic Passage Quotability & Reference Resolution Heuristic (Atomic Fact Self-Containment per Appendix B & C).
4. `filler_evaluator.py`: Substantive Lexical Density & Anti-Fluff Analysis (LDR per Appendix F).
5. `conversion_evaluator.py`: Evaluates user journey friction, primary Call to Action (CTA) clarity, trust proof signals (certifications/testimonials/ratings), commercial conversion routing, and discoverable support/FAQ paths.

## Guardrails & Compliance
- **Recommend-Only**: Passive inspection of rendered static DOM.
- **Zero Destructive Actions**: Never submits forms, clicks links, or authenticates.
