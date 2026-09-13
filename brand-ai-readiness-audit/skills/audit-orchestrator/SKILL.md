---
name: audit-orchestrator
description: Designated marketplace entrypoint that coordinates the full brand AI-readiness audit. Dispatches crawl, freshness, and engagement sub-skills, shields against cascading network errors, synthesizes proactive beyond-defect recommendations, enforces Handout Page 2 schema compliance, and emits a structured JSON audit report.
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
4. **Freshness & Entity Corroboration**: Execute `freshness-corroboration` to inspect Schema.org JSON-LD structured data, authoritative `sameAs` entity reconciliation, multi-source temporal freshness, and non-text alt attribute gaps.
5. **Engagement & Friction Audit**: Execute `engagement-audit` to evaluate 5-second cognitive orientation (hero H1, meta description), AI citation deep-linking anchors, content-to-boilerplate density, and trust signals.
6. **Proactive Opportunities Synthesis**: Call `scripts/proactive_engine.py` to inject strategic improvements (`/llms.txt`, conversational `FAQPage` schema, section citation anchors, Wikidata knowledge graph bridges).
7. **Schema Enforcement & Output**: Validate final report against Handout Page 2 schema using `scripts/schema_validator.py` and print clean JSON to stdout.

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
    "medium": 3,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "Robots.txt blocks AI assistant crawlers",
      "severity": "critical",
      "evidence": "Disallow: / configured for: gptbot, claudebot in robots.txt.",
      "suggested_action": {
        "summary": "Update robots.txt to permit indexing by conversational AI crawlers.",
        "priority": "critical"
      }
    }
  ]
}
```
