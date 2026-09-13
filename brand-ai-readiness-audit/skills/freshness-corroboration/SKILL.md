---
name: freshness-corroboration
description: Audits Schema.org structured data (JSON-LD), cross-web entity disambiguation (sameAs links), multi-source temporal freshness, and facts locked in non-text imagery.
license: Apache-2.0
allowed-tools:
  - python
  - bash
---

# Freshness & Entity Corroboration Audit Skill

## When to use
Use when diagnosing why an AI assistant misrepresents, hallucinates about, or ignores brand facts due to missing structured data, uncorroborated identity, or stale information.

## Inputs
- `target`: URL or path to local fixture bundle.
- Executed directly via `scripts/audit_freshness.py <target>` or imported as a module by the orchestrator.

## Procedure & Modular Architecture
Composed of 4 dedicated sub-modules:
1. `schema_evaluator.py`: Validates syntax, structure, and required properties for `Organization`, `WebSite`, `Product`, `FAQPage`.
2. `entity_resolver.py`: Evaluates `sameAs` knowledge graph links and on-site disambiguation posture (Round 2 Appendix D) for homonym brands.
3. `freshness_evaluator.py`: Corroborates dates across JSON-LD `dateModified`, OpenGraph timestamps, `<time>` tags, and HTTP `Last-Modified`. Detects uniform staleness (> 365 days across all channels) and cross-channel temporal drift (> 180 days divergence).
4. `nontext_inspector.py`: Identifies uncaptioned informative imagery missing descriptive `alt` attributes.

## Guardrails & Compliance
- **Recommend-Only**: Passive analysis only.
- **Zero External APIs**: 100% offline, deterministic heuristic execution.
