# Brand AI-Readiness Audit Marketplace

**Adobe University Hackathon 2026 — Round 3: Build the Agent Skill Marketplace**  
An `agentskills.io`-compliant Agent Skill Marketplace enabling general AI agents to automatically audit any website for:
1. **Off-site AI Discoverability**: Why a brand isn't found, trusted, or cited by AI search engines (ChatGPT, Claude, Perplexity, Gemini).
2. **On-site Engagement**: Why visitors referred from conversational AI bounce or fail to convert.

Emits a machine-readable, schema-compliant JSON report with concrete evidence, assigned severities (`critical`, `high`, `medium`), and prioritized suggested actions (including turnkey proactive improvements).

### The Core Problem: Retrieval vs. Browsing
AI search engines (ChatGPT, Claude, Perplexity) do not browse websites like human visitors—they retrieve, extract, and synthesize evidence from chunked DOM structures. A brand's AI readiness typically breaks down across five failure modes:
- **Crawler Access**: Blocked at `robots.txt` or obscured behind empty Client-Side Rendering (CSR) mounts.
- **Passage Extraction**: Facts rely on dangling pronouns (*"It provides..."*), causing retrieval systems to lose entity attribution.
- **Entity Ambiguity**: Common-word brand names lack on-site Schema.org disambiguation (`legalName`, `sameAs`).
- **Temporal Freshness**: Conflicting signals (> 180 days drift between headers and markup) can reduce confidence in freshness signals.
- **Conversion Friction**: High-intent visitors referred from conversational queries hit dead-ends lacking next-step CTAs.

This marketplace deterministically audits these structural failure modes and synthesizes drop-in, turnkey code remediations.

---

## 1. Technical Differentiators & Mechanism-Sound Heuristics

Unlike generic SEO checkers that merely look at legacy `<title>` tags or word counts, our marketplace directly implements the underlying mechanics from **Round 2 Appendices B, C, D, and F**:

### ★ Diff 1: Deterministic Passage Quotability & Reference Resolution Heuristic (Atomic Fact Self-Containment per Appendix B & C)
- **The Problem**: Retrieval and passage-ranking systems often slice documents into ~500-character windows. If key capability claims rely on unresolved anaphora (*"It provides 99.9% uptime"*, *"They feature zero-knowledge encryption"*), the extracted chunk lacks self-contained subject context, reducing retrieval relevance scores and increasing the risk of attribution loss in AI-generated answers.
- **Safeguards**:
  - *Scope Gating*: Restricted strictly to technical documentation and informational containers (`<main>`, `<article>`, `[role="main"]`, `<dl>`, `<table>`, `.docs`, `.faq`), excluding narrative founder letters, team stories, and editorial blogs.
  - *Hierarchical Context Injection*: Every chunk is prepended with its nearest parent heading (`H1 > H2 > H3`), modeling passage-level retrieval and reference resolution so heading-anchored chunks pass cleanly.
  - *Expletive Pronoun Filter*: Excludes dummy subjects (*"It is essential that..."*, *"It takes 5 minutes..."*).

### ★ Diff 2: Substantive Lexical Density & Anti-Fluff Analysis (LDR per Appendix F)
- **The Problem**: Appendix F notes that dense text summarizers often omit critical transactional details when surrounded by low-value filler. On web pages, boilerplate corporate jargon (*"seamlessly synergizing next-gen paradigms"*) dilutes substantive semantic density, increasing the risk that key product specifications and offerings are lost during extraction and summarization.
- **Safeguards**:
  - *Hero Zone Exemption*: Hero sections, H1 headlines, and marketing banners are 100% exempt, fully preserving creative copywriting (Apple, Nike, Linear).
  - *Computational Linguistics*: Uses standard Lexical Density Ratio ($LDR = \frac{\text{content words}}{\text{total words}}$) rather than statistical character entropy.
  - *Informational Anchor Gate*: Only triggers if a technical/feature section contains **zero quantified tokens** (numbers, technical specs, protocols, currencies, percentages) AND is saturated with abstract buzzwords. A single concrete spec passes the section.

### ★ Diff 3: Entity Ambiguity & On-Site Disambiguation Posture (Round 2 Appendix D)
- **The Problem**: Appendix D highlights that identical or generic homonym names create entity ambiguity, increasing the likelihood that automated indexers conflate distinct organizations sharing names like "Pulse", "Forge", "Ramp", or "Canvas".
- **Safeguards**:
  - *100% Offline & Deterministic*: Zero external API calls, zero SPARQL requests, zero rate-limit or firewall risks in sandboxes.
  - *On-Site Disambiguation Posture*: Audits what the webmaster directly controls: Schema.org `legalName`, explicit `@type` (`FinancialService` vs `SoftwareApplication`), `disambiguatingDescription`, and canonical `sameAs` entity links to official registry profiles. Homonym brands with proper on-site markup pass without ambiguity warnings.

### ★ Turnkey Suggested Action Synthesizer (`proactive_engine.py`)
- **Mechanism**: Rather than emitting passive, generic advice (*"Consider creating an llms.txt"*), the synthesizer delivers drop-in, turnkey code fixes nested cleanly inside `suggested_action.summary` via Markdown code blocks.
- **Safeguards**:
  - *Strict Schema Parity*: Suggested actions strictly adhere to Handout Page 2 (`summary` and `priority`). Root JSON schema retains exactly: `site`, `audited_at`, `summary`, and `findings`. Zero unsolicited root keys.
  - *Real Discovered Metadata*: Ingests real extracted page titles, meta descriptions, canonical URLs, and section headings, avoiding hallucinated placeholder text.

---

## 2. Marketplace Architecture & Composition

The execution pipeline coordinates audit dispatch sequentially with causal error shielding:

```text
Target URL / Local Fixture Path
        |
        v
audit-orchestrator (entrypoint: run_audit.py)
        |
        +--> [1] crawl-render-audit (causal shield halts cascade if blocked)
        +--> [2] freshness-corroboration
        +--> [3] engagement-audit
        |
        v
proactive_engine (evidence-conditioned turnkey fixes)
        |
        v
Unified Audit Report (schema-validated JSON)
```

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

### What Each Skill Does

1. **`audit-orchestrator` (`skills/audit-orchestrator`)** — *[Entrypoint Skill]*:
   - Central controller that coordinates end-to-end audits of target URLs or local fixtures.
   - Enforces **Causal Error Shielding**: immediately suppresses downstream content/schema checks if the site is unreachable or completely blocked at the network/robots layer, preventing cascade false positives.
   - Synthesizes turnkey, drop-in remediation code (`/llms.txt`, JSON-LD `FAQPage`, `sameAs` blocks) via `proactive_engine.py`.
   - Formats, prioritizes, and validates the final report against the strict Handout Page 2 JSON contract (`schema_validator.py`).

2. **`crawl-render-audit` (`skills/crawl-render-audit`)**:
   - Inspects network and crawler accessibility for 9 leading AI user-agents (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, etc.).
   - Parses RFC 9309 `robots.txt` records with full path-scoped (`/path/`) and root (`/`) matching.
   - Detects AI-selective bot cloaking via dual-probe User-Agent fetching (Standard Browser vs. `GPTBot`).
   - Identifies Client-Side Rendering (CSR) barriers (empty `#root` mount with `< 50` words) while allowing server-rendered SSR pages with hydration hooks to pass cleanly.
   - Validates XML Sitemap discoverability in `robots.txt` and origin paths.

3. **`freshness-corroboration` (`skills/freshness-corroboration`)**:
   - Validates multi-page Schema.org structured data (`Organization`, `WebSite`, `Product`, `FAQPage`) with recursive JSON-LD `@graph` unwrapping.
   - Resolves generic brand name ambiguity (Appendix D) using on-site disambiguation posture (`legalName`, `disambiguatingDescription`, and multi-registry `sameAs` links to Wikidata, Wikipedia, Crunchbase, LinkedIn).
   - Performs **4-Way Temporal Freshness Corroboration** across JSON-LD `dateModified`, OpenGraph `article:modified_time`, DOM `<time>`, and RFC 7231 HTTP `Last-Modified` headers. Detects both uniform staleness (> 365 days across all channels) and temporal signal drift (> 180 days inter-channel divergence).
   - Inspects non-text imagery traps (Appendix C) for missing descriptive `alt` attributes, explicitly filtering out purely decorative visuals (`role="presentation"`, `aria-hidden="true"`).

4. **`engagement-audit` (`skills/engagement-audit`)**:
   - Evaluates on-site visitor retention and conversion friction for high-intent AI-referred traffic.
   - Audits 5-second cognitive orientation (prominent `<h1>` tag within the hero zone and semantic token alignment with `<meta name="description">`).
   - Enforces sequential heading hierarchy (detecting skipped heading levels like `H1 -> H3`) and verifies fragment citation anchor IDs on subheadings.
   - Simulates neural retrieval passage slicing (500-char sliding windows) to compute the **Atomic Quotability Score (AQS)** and flag dangling pronouns (Appendix B & C), with narrative container scope-gating.
   - Measures Substantive Lexical Density (LDR anti-fluff analysis per Appendix F) with full hero-zone marketing exemptions.
   - Evaluates commercial conversion friction (primary CTAs, verifiable trust proof, commercial routing, and FAQ discovery) gated strictly by `has_commercial_intent()`.

### How the Entry Point Composes Them

The orchestrator (`run_audit.py`) executes a sequential, causally-shielded pipeline:
1. **Target Ingestion & Multi-Page Discovery**: `fetch_target_bundle()` fetches the target URL or local fixture, probes `robots.txt` and sitemaps, discovers documentation and conversion subpages, and executes dual-probe User-Agent testing.
2. **Crawl & Render Layer**: Invokes `audit_crawl()`. If the target is unreachable (HTTP $\ge 400$) or blocks AI crawlers at the network layer (`F-CRAWL-001`), the orchestrator triggers **Causal Error Shielding**, immediately halting further skill execution to prevent alert pollution.
3. **Domain Evaluation Layer**: If reachability is verified, the orchestrator invokes `audit_freshness()` and `audit_engagement()` in sequence, collecting structured findings across metadata, markup, hierarchy, quotability, and conversion friction.
4. **Proactive Synthesis Layer**: Feeds observed site evidence into `proactive_engine.py` to synthesize copy-paste drop-in code fixes (`/llms.txt`, JSON-LD `FAQPage`, `sameAs` entity links).
5. **Report Normalization & Schema Enforcement**: Re-indexes all findings (`F-001`, `F-002`, ...), preserves individual `low` severities while folding counts into `medium` for summary compliance (`total_findings == critical + high + medium`), and enforces Handout Page 2 schema floor compliance via `schema_validator.py`.

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
# Automated regression unit tests (27 tests in ~0.04s)
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
| **CSR Inline Data-Island Downgrade** | Flags all thin-prose mount roots as critical barriers even when rich JSON state is serialized inline. | Detects `__NEXT_DATA__`, Nuxt state, and JSON blocks; downgrades finding to `medium` and identifies data payload byte size. | `test_21_csr_data_island_severity_downgrade_guard` |
| **Technical Prose Fluff Immunity** | Over-penalizes legitimate technical prose using literal words like "seamless" without quantified metrics. | Compound gate (`words >= 80`, `fluff >= 5`, `ratio > 3.5%`) prevents false positives on substantive engineering text. | `test_22_technical_prose_fluff_lexicon_no_false_positive` |
| **FAQ Sibling Answer Extraction** | Generates FAQ schema with generic page-level meta descriptions instead of the actual on-page answers. | Dynamically parses immediate sibling DOM elements (`<p>`, `<div>`, `<dd>`, `<ul>`) following question headings to extract substantive answers. | `test_23_faq_sibling_answer_extraction_guard` |
| **E-commerce CTA Recognition** | Only recognizes B2B/SaaS CTAs ("Book Demo", "Start Trial"), flagging e-commerce storefronts for missing CTAs. | Broadened transactional lexicon recognizes "Add to Cart", "Checkout", "Shop Now", and commerce routes (`/shop`, `/cart`). | `test_24_ecommerce_cta_recognition_guard` |
| **Decorative Image Exemption** | Flags all images without descriptive alt text, including decorative spacers, icons, and backgrounds. | Honors WCAG decorative markup (`role="presentation"`, `role="none"`, `aria-hidden="true"`), excluding decorative media while strictly flagging uncaptioned informative graphics. | `test_25_decorative_image_exemption_guard` |
| **Expletive Pronoun Filter** | Flags natural English dummy-subject idioms (*"It is essential..."*, *"It takes 30 seconds..."*) as dangling anaphora. | Regex lookahead pattern (`it\s+(?:is|was|takes|seems|appears|has\s+been)`) exempts standard expletive constructions from passage quotability penalties while flagging genuine unresolved pronouns. | `test_26_expletive_pronoun_filter_guard` |
| **Search Form CTA Exemption** | Treats any `<form>` with a submit button or `<button>` as a commercial conversion CTA, letting pages with only site search pass without CTAs. | Disqualifies search, query, and filter forms via `role="search"`, `action="...search..."`, and `name="q"`, accurately enforcing `F-ENGAGE-011` when zero actual conversion pathways exist. | `test_27_search_form_cta_exemption_guard` |

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
