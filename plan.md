# Brand AI-Readiness Audit Marketplace — Certified Execution Plan

**Adobe University Hackathon 2026 — Round 3: Build the Agent Skill Marketplace**  
**Document:** `plan.md`  
**Status:** Certified & Approved by Multi-Agent Consensus (Domain Expert, Red Team Critic, Fresh Eyes Lead Auditor)

---

## 1. Executive Summary & Challenge Overview

Round 3 tests encoding reasoning from Round 2 into a reusable, modular **Agent Skill Marketplace** authored in the standard `agentskills.io` format. When pointed at any website (or local test fixture), the marketplace automatically audits:
1. **Off-Site AI Discoverability**: Why the brand isn't found, trusted, or cited by AI assistants (ChatGPT, Claude, Perplexity, Gemini, AI search overviews).
2. **On-Site Engagement**: Why visitors who arrive via AI referrals bounce or fail to convert (cognitive orientation, context retention, friction traps).

The marketplace emits a single, machine-readable audit report adhering strictly to the required Handout Page 2 schema floor, containing:
- **Evidence-backed problems found** (Round 2 failure modes) with assigned severities (`critical`, `high`, `medium`).
- **Mechanism-sound, prioritized suggested actions** for every detected problem.
- **Evidence-conditioned proactive beyond-defect improvements** that strengthen AI discoverability and engagement.

---

## 2. Step 0: Empirical Field Research ("Learn from the Wild")

Per Handout Page 1 (*"go find real websites that AI assistants cite well versus ones they ignore or misrepresent, and work out what makes the difference"*), our heuristics are derived from observed real-world contrasts:

1. **AI Crawler Access (Cloudflare vs. NYTimes)**:
   - *Cloudflare* explicitly declares `Allow: /` for `GPTBot` and `PerplexityBot`. Its documentation and incident blogs are cited with high frequency across AI engines.
   - *NYTimes* blacklists `ClaudeBot`, `GPTBot`, `PerplexityBot` via `Disallow: /`. Assistants cannot cite live articles.
   - *Heuristic Derived*: Direct AI crawler permission cascade in `crawl-render-audit`.
2. **Structured Data & Entity Disambiguation (Stripe vs. Linear)**:
   - *Stripe* serves pre-rendered Schema.org `Organization` JSON-LD with verified `sameAs` links to LinkedIn, Crunchbase, and Wikipedia. AI assistants never confuse Stripe with homonyms.
   - *Linear* omits static `Organization` JSON-LD in raw HTML, creating entity collision risk with the mathematical term "linear".
   - *Heuristic Derived*: Detection of missing Organization schema and on-site disambiguation posture in `freshness-corroboration`.
3. **Gzipped Sitemap Indexes (Enterprise Publishers)**:
   - Large publishers serve `.xml.gz` sitemaps declared inside `robots.txt`.
   - *Heuristic Derived*: Automatic `.gz` stream decompression in sitemap checks.
4. **Deep-Link Citation Anchoring (MDN & Stripe Docs)**:
   - Sites frequently quoted by Perplexity attach persistent semantic HTML `id` attributes to every `<h2>`/`<h3>` heading (`<h2 id="create-charge">`), enabling paragraph-level deep citation links.
   - *Heuristic Derived*: Deep citation anchor audit and conditioned proactive injection.

---

## 3. Concrete Algorithms & Deterministic Thresholds

1. **AI Crawler Blacklist**: Scans `robots.txt` for 9 specific bot user-agents (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, `Applebot-Extended`, `Amazonbot`, `Bytespider`, `CCBot`). Flagged as `critical` if `*` or `GPTBot` is blocked; `high` for secondary crawlers.
2. **Modern SSR vs. Pure CSR**: Strips `<script>`, `<style>`, `<nav>`, `<footer>`. Counts visible body prose words:
   - Word count >= 250 words $\rightarrow$ **SSR PASS** (immune to Next.js App Router streaming scripts).
   - Word count < 50 words AND empty mount root (`#root`, `#app`, `#__next`) $\rightarrow$ **CSR Barrier** (`critical`).
3. **4-Way Freshness Corroboration**: Cross-checks timestamps across JSON-LD `dateModified`, OpenGraph `article:modified_time`, DOM `<time datetime>`, and HTTP `Last-Modified`.
   - Timestamp age > 365 days across all available signals $\rightarrow$ **Stale Content** (`medium`).
4. **Non-Text Imagery Trap**: Scans `<img>` tags. If > 40% of informative images lack meaningful `alt` attributes $\rightarrow$ **Non-Text Trap** (`medium`).
5. **5-Second Orientation**: Primary `<h1>` must exist in top 3,000 characters and contain 5 to 150 characters, aligned with `<meta name="description">`.
6. **Deterministic Passage Quotability & Reference Resolution Heuristic (Atomic Fact Self-Containment per Appendix B & C)**: Evaluates 500-char sliding windows in `<main>`/`<article>`. If Atomic Quotability Score (AQS) < 50 with >= 2 dangling pronoun chunks $\rightarrow$ **Quotability & Reference Resolution Risk** (`medium`).
7. **Substantive Lexical Density & Anti-Fluff Analysis (LDR per Appendix F)**: Hero zone exempt. If a technical/feature section contains 0 quantified metrics AND > 3.5% corporate fluff buzzwords $\rightarrow$ **Summarizer Dropout Zone** (`medium`).
8. **Entity Ambiguity**: If brand name matches dictionary homonym list (`references/polysemy_dictionary.json`) and lacks `legalName`, specialized `@type`, or `sameAs` $\rightarrow$ **Hallucination Risk** (`medium`).

---

## 4. Turnkey Suggested Action Synthesizer (Evidence-Conditioned Action Synthesis)

Delivering drop-in code fixes inside suggested actions rather than generic advice, strictly conditioned on observed site evidence:
- **`/llms.txt`**: Conditioned on discovering documentation, guide, or API routes (`/docs`, `/api`, `/developers`) while lacking `/llms.txt`.
- **`FAQPage` Schema**: Conditioned on detecting natural question patterns or FAQ headings in body copy without structured markup.
- **Citation Anchors**: Conditioned on detecting multiple subheadings (`>= 2`) where < 25% have HTML `id` attributes.
- **`sameAs` Knowledge Graph Bridge**: Conditioned on observing commercial entity signals (`/pricing`, `/product`) without external entity links.

---

## 5. Output JSON Schema Floor (Handout Page 2 Contract)

Strictly matches the Handout Page 2 floor:
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
*Note*: `total_findings == critical + high + medium`.

---

## 6. Modular Decomposition & Engineering Architecture

```text
brand-ai-readiness-audit/
├── marketplace.json                   # Contest manifest (entrypoint: audit-orchestrator)
├── README.md                          # Comprehensive documentation
├── test_audit.py                      # Regression test suite (0.015s offline)
├── fixtures/                          # 5 synthetic offline HTML/robots.txt test suites
├── references/
│   ├── field_research.md             # Empirical wild site contrast analysis
│   └── worked_examples.md            # Bad vs Good contrast benchmarks (Quotability & Filler)
└── skills/
    ├── audit-orchestrator/            # [ENTRYPOINT]
    │   ├── SKILL.md                   # Declares allowed-tools, RFC 9309 compliance
    │   ├── scripts/
    │   │   ├── run_audit.py           # Clean JSON to stdout, stderr diagnostics
    │   │   ├── schema_validator.py    # Enforces Handout Page 2 schema floor
    │   │   └── proactive_engine.py    # Evidence-conditioned artifact synthesis
    │   └── references/ (report_schema.json, scoring_rubric.md, field_research.md)
    ├── crawl-render-audit/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── audit_crawl.py         # Autonomous crawl/render CLI
    │   │   └── http_fetcher.py        # Dual-probe UA (Chrome Desktop + GPTBot)
    │   └── references/ (ai_crawlers.json, spa_signatures.json)
    ├── freshness-corroboration/       # Decomposed into 4 single-responsibility modules:
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── schema_evaluator.py    # Schema.org structured data validator
    │   │   ├── entity_resolver.py     # sameAs & on-site disambiguation posture
    │   │   ├── freshness_evaluator.py # 4-way temporal date corroboration
    │   │   ├── nontext_inspector.py   # Uncaptioned media & alt-text inspector
    │   │   └── audit_freshness.py     # Autonomous composed runner CLI
    │   └── references/ (jsonld_templates.json, authority_registries.json, polysemy_dictionary.json)
    └── engagement-audit/              # Decomposed into 5 single-responsibility modules:
        ├── SKILL.md
        ├── scripts/
        │   ├── orientation_evaluator.py # 5-second orientation, viewport & meta description
        │   ├── hierarchy_evaluator.py   # Heading hierarchy & deep citation anchors
        │   ├── quotability_evaluator.py # Passage slicing & Atomic Quotability (Appendix B/C)
        │   ├── filler_evaluator.py      # Lexical Density & Fact-to-Filler Ratio (Appendix F)
        │   ├── conversion_evaluator.py  # User journey, CTAs, trust proof & conversion friction
        │   └── audit_engagement.py      # Autonomous composed runner CLI
        └── references/ (orientation_rubric.md, friction_patterns.json, filler_lexicon.json)
```

---

## 7. Guardrails & Compliance Checklist

- **Recommend-Only**: 100% passive, read-only inspection. Zero live site mutations.
- **RFC 9309 Robots.txt Compliance**: Strictly respects disallow rules.
- **Runtime Budget**: Low-overhead bounded execution: sub-second offline processing (~0.02s typical), bounded stream fetching live (well under 5-minute ceiling).
- **Package Size**: < 2 MB including all fixtures and references (Ceiling: < 50 MB; no binary model weights).
- **Zero External Dependencies**: Pure Python standard library reliability with automatic acceleration if `requests`/`bs4` present.
