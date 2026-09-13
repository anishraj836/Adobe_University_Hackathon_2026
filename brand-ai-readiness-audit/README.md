# Brand AI-Readiness Audit Marketplace

**Adobe University Hackathon 2026 — Round 3: Build the Agent Skill Marketplace**  
An `agentskills.io`-compliant Agent Skill Marketplace enabling general AI agents to automatically audit any website for:
1. **Off-site AI Discoverability**: Why a brand isn't found, trusted, or cited by AI search engines (ChatGPT, Claude, Perplexity, Gemini).
2. **On-site Engagement**: Why visitors referred from conversational AI bounce or fail to convert.

Emits a machine-readable, schema-compliant JSON report with concrete evidence, assigned severities (`critical`, `high`, `medium`), and prioritized suggested actions (including turnkey proactive improvements).

---

## 1. Technical Differentiators & Mechanism-Sound Heuristics

Unlike generic SEO checkers that merely look at legacy `<title>` tags or word counts, our marketplace directly implements the underlying mechanics from **Round 2 Appendices B, C, D, and F**:

### ★ Diff 1: Deterministic Passage Quotability & Reference Resolution Heuristic (Atomic Fact Self-Containment per Appendix B & C)
- **The Problem**: Search and retrieval systems chunk documents into ~500-character windows. If key facts rely on unresolved anaphora (*"It provides 99.9% uptime"*, *"They feature zero-knowledge encryption"*), retrievers score the passage poorly and AI assistants refuse to cite the brand.
- **Safeguards**:
  - *Scope Gating*: Restricted strictly to technical documentation and informational containers (`<main>`, `<article>`, `[role="main"]`, `<dl>`, `<table>`, `.docs`, `.faq`), excluding narrative founder letters, team stories, and editorial blogs.
  - *Hierarchical Context Injection*: Every chunk is prepended with its nearest parent heading (`H1 > H2 > H3`), modeling passage-level retrieval and reference resolution so heading-anchored chunks pass cleanly.
  - *Expletive Pronoun Filter*: Excludes dummy subjects (*"It is essential that..."*, *"It takes 5 minutes..."*).

### ★ Diff 2: Substantive Lexical Density & Anti-Fluff Analysis (LDR per Appendix F)
- **The Problem**: Appendix F demonstrates that AI summarizers drop critical transactional facts when surrounded by low-value filler. On web pages, corporate fluff (*"seamlessly synergizing next-gen paradigms"*) dilutes substantive semantic density, causing LLM summarizers to drop core offerings.
- **Safeguards**:
  - *Hero Zone Exemption*: Hero sections, H1 headlines, and marketing banners are 100% exempt, fully preserving creative copywriting (Apple, Nike, Linear).
  - *Computational Linguistics*: Uses standard Lexical Density Ratio ($LDR = \frac{\text{content words}}{\text{total words}}$) rather than statistical character entropy.
  - *Informational Anchor Gate*: Only triggers if a technical/feature section contains **zero quantified tokens** (numbers, technical specs, protocols, currencies, percentages) AND is saturated with abstract buzzwords. A single concrete spec passes the section.

### ★ Diff 3: Entity Ambiguity & On-Site Disambiguation Posture (Round 2 Appendix D)
- **The Problem**: Appendix D states that identical/generic names cause AI systems to confuse entities (e.g. brands named "Pulse", "Forge", "Ramp", "Canvas").
- **Safeguards**:
  - *100% Offline & Deterministic*: Zero external API calls, zero SPARQL requests, zero rate-limit or firewall risks in sandboxes.
  - *On-Site Disambiguation Posture*: Audits what the webmaster directly controls: Schema.org `legalName`, explicit `@type` (`FinancialService` vs `SoftwareApplication`), `disambiguatingDescription`, and canonical `sameAs` entity links to official registry profiles. Homonym brands with proper on-site markup pass with flying colors.

### ★ Turnkey Suggested Action Synthesizer (`proactive_engine.py`)
- **Mechanism**: Rather than emitting passive, generic advice (*"Consider creating an llms.txt"*), the synthesizer delivers drop-in, turnkey code fixes nested cleanly inside `suggested_action.summary` via Markdown code blocks.
- **Safeguards**:
  - *Strict Schema Parity*: Suggested actions strictly adhere to Handout Page 2 (`summary` and `priority`). Root JSON schema retains exactly: `site`, `audited_at`, `summary`, and `findings`. Zero unsolicited root keys.
  - *Real Discovered Metadata*: Ingests real extracted page titles, meta descriptions, canonical URLs, and section headings, avoiding hallucinated placeholder text.

---

## 2. Marketplace Architecture & Composition

The marketplace contains four narrowly-scoped, autonomous skills with genuine separation of concerns:

```text
brand-ai-readiness-audit/
├── marketplace.json                   # Contest manifest (designates entrypoint: true)
├── README.md                          # This architecture & usage guide
├── test_audit.py                      # Automated regression suite (< 0.03s execution)
├── fixtures/                          # 5 synthetic offline HTML/robots.txt test suites
├── references/                        # Empirical research & concrete contrast benchmarks
│   ├── field_research.md             # Empirical wild site contrasts (Cloudflare, NYT, Stripe, Linear)
│   └── worked_examples.md            # Bad vs Good text examples (Quotability & Fact-to-Filler)
└── skills/
    ├── audit-orchestrator/            # [ENTRYPOINT] Composes sub-skills, shields errors, emits JSON
    │   ├── SKILL.md
    │   ├── scripts/ (run_audit.py, schema_validator.py, proactive_engine.py)
    │   └── references/ (report_schema.json, scoring_rubric.md)
    ├── crawl-render-audit/            # Evaluates AI crawler access, robots.txt, and SSR/CSR gaps
    │   ├── SKILL.md
    │   ├── scripts/ (audit_crawl.py, http_fetcher.py)
    │   └── references/ (ai_crawlers.json, spa_signatures.json)
    ├── freshness-corroboration/       # Audits JSON-LD, entity ambiguity, multi-source freshness
    │   ├── SKILL.md
    │   ├── scripts/ (audit_freshness.py, schema_evaluator.py, entity_resolver.py, freshness_evaluator.py, nontext_inspector.py)
    │   └── references/ (jsonld_templates.json, authority_registries.json, polysemy_dictionary.json)
    └── engagement-audit/              # Audits 5s orientation, passage quotability, lexical density, conversion friction
        ├── SKILL.md
        ├── scripts/ (audit_engagement.py, orientation_evaluator.py, hierarchy_evaluator.py, quotability_evaluator.py, filler_evaluator.py, conversion_evaluator.py)
        └── references/ (orientation_rubric.md, friction_patterns.json, filler_lexicon.json)
```

---

## 3. Quickstart & CLI Usage

### Prerequisites
- Python 3.10+
- Zero mandatory external dependencies (pure standard library with automatic acceleration if `requests`/`bs4` present).

### Running an Audit
```bash
# 1. Audit a live website (emits clean JSON to stdout)
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com

# 2. Output formatted Markdown summary
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --format markdown

# 3. Audit an offline test fixture
python3 skills/audit-orchestrator/scripts/run_audit.py fixtures/blocked_site

# 4. Save output to a file
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --output audit_report.json

# 5. Explain mode (telemetry and scope-gate decisions printed to stderr)
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --explain
```

### Running Autonomous Sub-Skills Standalone
```bash
python3 skills/crawl-render-audit/scripts/audit_crawl.py https://example.com
python3 skills/freshness-corroboration/scripts/audit_freshness.py https://example.com
python3 skills/engagement-audit/scripts/audit_engagement.py https://example.com
```

### Running the Test & Benchmark Suites
```bash
# Automated regression unit tests (20 tests in ~0.04s)
python3 test_audit.py

# Full 5-step benchmark scorecard (latency percentiles, ground truth accuracy)
python3 benchmark_suite.py
```
*Low-overhead bounded execution: sub-second offline processing (~0.002s typical), bounded stream fetching live.*

---

## 4. Anti-False-Positive Safeguards & Scope Gates

To prevent alert fatigue and eliminate false positives on legitimate web patterns, every heuristic is bounded by explicit scope gates:
- **Commercial Intent Scope Gate (`conversion_evaluator.py`)**: Gated by `has_commercial_intent()` (detecting pricing, SaaS signup, demo, or transactional pathways). Developer documentation, open-source libraries, and personal portfolios are never penalized for missing "Book Demo" buttons or SOC2 badges.
- **Hero-Zone Exemption (`filler_evaluator.py`)**: Emotional branding and punchy headlines in top-level hero zones (`class="hero"`, `<header>`) are explicitly exempt from Lexical Density Ratio (LDR) fluff penalties.
- **Narrative Container Scope Gate (`quotability_evaluator.py`)**: Sliding-window quotation analysis operates strictly on substantive narrative elements (`<main>`, `<article>`, `<section>`), ignoring navigation trees, footers, and sidebars.
- **Polysemy Dictionary Gating (`entity_resolver.py`)**: Homonym ambiguity warnings fire only when the brand name matches a verified dictionary word (`references/polysemy_dictionary.json`) AND lacks Schema.org `legalName`, `disambiguatingDescription`, or `sameAs` knowledge graph links.
- **Causal Error Shielding (`run_audit.py`)**: If network-layer blocks or AI crawler bans are identified at the origin, downstream content and schema checks are shielded rather than emitting cascading false positives.

---

## 5. Adversarial Validation: Discriminating Tests

Every false-positive safeguard in this marketplace is backed by a bidirectional unit test in `test_audit.py` that verifies the check is discriminating—passing the legitimate edge case while flagging the truly defective one:

| Scenario | Naive Implementation (False Positive) | This Marketplace (Discriminating Guard) | Verified Test |
| :--- | :--- | :--- | :--- |
| **Common-Word Brand Identity** | Flags generic word brands (e.g. "Linear", "Atlas") as hallucination risks regardless of disambiguation. | Checks for Schema.org `legalName`, `disambiguatingDescription`, or authoritative `sameAs` registry links before flagging. | `test_15_common_word_brand_disambiguation_guard` |
| **Modern SSR Hydration Fallback** | Flags any page containing `<div id="root">` or `<div id="__next">` as an unindexable CSR barrier. | Verifies static body word count (>= 50 words threshold); pre-rendered SSR pages with hydration hooks pass cleanly. | `test_16_csr_ssr_hydration_guard` |
| **Documentation & Blog Pages** | Dings technical docs or engineering blogs for missing "Book a Demo" CTA buttons or pricing routes. | Gates all conversion and friction checks behind `has_commercial_intent()`; non-commercial pages receive 0 conversion warnings. | `test_17_docs_page_commercial_intent_guard` |
| **Editorial & Narrative Copy** | Flags founder letters, stories, and personal blogs for low passage quotability due to narrative pronouns. | Evaluator explicitly inspects container tokens (`founder-letter`, `personal-story`, `blog-post`) and exempts narrative copy. | `test_18_narrative_container_quotability_guard` |
| **Hero Zone Marketing Branding** | Flags punchy hero headlines for high corporate fluff or lack of quantified metrics. | Strips hero, banner, and jumbotron containers before evaluating Lexical Density Ratio (LDR); hero branding is exempt. | `test_19_hero_zone_filler_exemption_guard` |
| **RFC 9309 Path-Scoped Disallows** | Either assumes any `Disallow:` blocks the bot, or only checks for root `Disallow: /`. | Respects RFC 9309 semantics: empty `Disallow:` is permitted, while path-scoped rules (`Disallow: /private/`) are flagged as partial blocks. | `test_20_path_scoped_robots_disallow_guard` |

These tests demonstrate that the marketplace discriminates between genuine architectural barriers and intentional, standard web design patterns.

---

## 6. Known Scope Boundaries & Design Trade-offs

In strict adherence to the hackathon's < 5-minute runtime and zero-external-dependency constraints:
- **Static DOM vs. Heavy Headless Browser**: Pure Client-Side Rendered (CSR) SPAs are flagged statically by detecting empty mount roots (`#root`, `#app`) and JS script bundles without running a 300MB Chromium/Playwright instance.
- **Offline Knowledge Graph Posture**: External entity registries (Wikidata, Crunchbase) are audited via the brand's on-site knowledge graph bridge (`sameAs` links) rather than making outbound live SPARQL queries during offline evaluation.
- **Conjunctive Freshness & Drift**: Content is only flagged as stale when all available signals agree ($\max(\text{dates}) < \text{now} - 365\text{ days}$). Conflicting signals (> 180 days drift between headers and markup) are flagged as temporal divergence (`F-FRESH-007`). See `skills/freshness-corroboration/references/freshness_design_decisions.md`.
- **Live Empirical Validation**: See `references/live_validation.md` for live audit transcripts on production websites (`example.com`, `httpbin.org`, `python.org`).

---

## 7. Output Schema Parity (Handout Page 2)

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
