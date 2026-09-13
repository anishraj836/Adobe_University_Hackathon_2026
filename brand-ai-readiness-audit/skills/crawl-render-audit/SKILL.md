---
name: crawl-render-audit
description: Audits technical crawlability, AI-specific crawler permissions in robots.txt, HTTP headers, meta robots tags (noai/noindex), and client-side JavaScript rendering barriers (CSR vs SSR).
license: Apache-2.0
allowed-tools:
  - python
  - bash
---

# Crawl & Render Audit Skill

## When to use
Use when diagnosing why an AI assistant cannot reach, fetch, or render the content of a website or web application.

## Inputs
- `target`: URL or path to local fixture bundle.
- Executed directly via `scripts/audit_crawl.py <target>` or imported as a module by the orchestrator.

## Procedure
1. **Network Probe**: Execute dual-probe fetch (Standard Browser UA + `GPTBot/1.2` UA) to detect AI-selective cloaking or WAF blocking.
2. **Robots.txt Analysis**: Parse RFC 9309 rules specifically checking for AI crawlers: `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, `Applebot-Extended`, `Amazonbot`, `Bytespider`, `CCBot`.
3. **Meta Restrictions**: Scan `<head>` for `<meta name="robots" content="noindex|noai|noimageai">` and inspect `X-Robots-Tag` headers.
4. **Modern SSR vs CSR Evaluation**: Measure visible prose word count in static HTML body. If >= 250 words, verify SSR PASS (immune to Next.js App Router RSC streaming scripts). Only flag CSR barrier if text < 50 words and empty mount root (`#root`, `#app`, `#__next`) is detected.
5. **Sitemap Discovery**: Verify presence of `/sitemap.xml` or `Sitemap:` directive in `robots.txt`, decompressing `.xml.gz` streams transparently.

## Guardrails & Compliance
- **Recommend-Only**: Non-destructive, read-only inspection.
- **RFC 9309 Compliance**: Honors robots.txt disallow directives.
- **Timeouts**: Bounded 6-second HTTP timeouts per request.
