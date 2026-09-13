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

## Procedure
1. **Schema.org Structured Data Extraction**: Parse all `<script type="application/ld+json">` blocks. Trap syntax errors gracefully and inspect for `Organization`, `WebSite`, `Product`, and `FAQPage`.
2. **Entity Disambiguation & Cross-Web Agreement**: Inspect `sameAs` links across authoritative registries (Wikidata, Wikipedia, LinkedIn, Crunchbase, GitHub, Google Business, Twitter/X) to resolve brand naming ambiguity.
3. **4-Way Freshness Corroboration**: Corroborate dates across JSON-LD `dateModified`/`datePublished`, OpenGraph `article:modified_time`, DOM `<time datetime>`, and HTTP `Last-Modified` headers. Flags staleness only if all available signals indicate content is > 365 days old.
4. **Non-Text Trap Inspection**: Inspect all `<img>` tags and flag informative graphics, diagrams, and feature cards missing descriptive `alt` attributes.

## Output
Returns a structured list of findings:
- `F-FRESH-001`: Syntax error in Schema.org JSON-LD.
- `F-FRESH-002`: Missing Schema.org structured data.
- `F-FRESH-003`: Missing root Organization or WebSite entity schema.
- `F-FRESH-004`: Lacks cross-web entity corroboration (`sameAs` links).
- `F-FRESH-005`: Stale temporal signals (> 1 year since update).
- `F-FRESH-007`: Brand information locked in uncaptioned images.
