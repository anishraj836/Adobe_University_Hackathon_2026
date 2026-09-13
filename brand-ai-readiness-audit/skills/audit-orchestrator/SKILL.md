---
name: audit-orchestrator
description: Designated marketplace entrypoint that coordinates the full brand AI-readiness audit. Dispatches crawl, freshness, and engagement sub-skills, shields against cascading network errors, synthesizes evidence-conditioned proactive recommendations, enforces Handout Page 2 schema compliance, and emits a structured JSON audit report.
license: Apache-2.0
allowed-tools:
  - python
  - bash
---

# Audit Orchestrator (Marketplace Entrypoint)

## When to use
Use when a general AI agent or engineer needs to audit any website or local web fixture for AI discoverability (AEO/GEO) and on-site engagement problems, producing a standardized, prioritized report.

## Inputs
- `target`: A live URL (e.g., `https://example.com`), domain string, or path to a local fixture directory / HTML file.
- Optional arguments: `--format json|markdown`, `--output <file_path>`.

## Procedure
1. **Target Ingestion & Reachability**: Probe target via `scripts/run_audit.py`. Detect local fixture paths vs remote domains.
2. **Crawl & Render Audit**: Execute `crawl-render-audit` to evaluate robots.txt permissions for AI crawlers (GPTBot, ClaudeBot, PerplexityBot), meta robots restrictions, and client-side rendering (CSR) barriers.
3. **Causal Error Shielding**: If network access is blocked or the origin returns HTTP 403, log root-cause finding `F-CRAWL-001` and suppress downstream spurious content errors.
4. **Freshness & Entity Corroboration**: Execute `freshness-corroboration` (composing `schema_evaluator.py`, `entity_resolver.py`, `freshness_evaluator.py`, and `nontext_inspector.py`) to inspect Schema.org JSON-LD structured data, authoritative `sameAs` entity reconciliation, multi-source temporal freshness, and non-text alt attribute gaps.
5. **Engagement & Friction Audit**: Execute `engagement-audit` to evaluate 5-second cognitive orientation (hero H1, meta description), AI citation deep-linking anchors, content-to-boilerplate density, passage quotability, conversion CTAs, and trust signals.
6. **Turnkey Suggested Action Synthesis**: Call `scripts/proactive_engine.py` to synthesize drop-in code fixes inside suggested actions (`/llms.txt`, conversational `FAQPage` schema, section citation anchors, Wikidata knowledge graph bridges) strictly conditioned on observed site evidence.
7. **Schema Enforcement & Output**: Validate final report against Handout Page 2 schema floor using `scripts/schema_validator.py` and print clean JSON to stdout.

## Guardrails & Compliance
- **Recommend-Only**: 100% passive, read-only analysis. Zero live site mutations.
- **RFC 9309 Robots.txt Compliance**: Strictly respects disallow rules and polite crawling semantics.
- **Runtime Budget**: Low-overhead bounded execution: sub-second offline processing (~0.02s typical), bounded stream fetching live.
- **Self-Contained**: Requires zero external paid APIs, zero proprietary keys, and runs in completely air-gapped sandboxes.

## Output
Emits a single JSON report matching the Handout Page 2 specification:
```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3
  },
  "findings": [
    {
      "id": "F-001",
      "title": "No JSON-LD structured data on product pages",
      "severity": "high",
      "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
      "suggested_action": {
        "summary": "Add Product/Offer JSON-LD to every product page.",
        "priority": "high"
      }
    }
  ]
}
```
