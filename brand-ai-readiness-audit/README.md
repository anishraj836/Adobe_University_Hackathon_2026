# Brand AI-Readiness Audit Marketplace

**Adobe University Hackathon 2026 — Round 3: Build the Agent Skill Marketplace**  
An `agentskills.io`-compliant Agent Skill Marketplace enabling general AI agents to automatically audit any website for:
1. **Off-site AI Discoverability**: Why a brand isn't found, trusted, or cited by AI search engines (ChatGPT, Claude, Perplexity, Gemini).
2. **On-site Engagement**: Why visitors referred from conversational AI bounce or fail to convert.

Emits a machine-readable, schema-compliant JSON report with concrete evidence, assigned severities (`critical`, `high`, `medium`, `low`), and prioritized suggested actions (including turnkey proactive improvements).

---

## 1. The 4 Battle-Hardened Key Differentiators

Unlike generic SEO checkers that merely look at legacy `<title>` tags or word counts, our marketplace directly implements the underlying mechanics from **Round 2 Appendices B, C, D, and F**:

### ★ Diff 1: LLM RAG Citation & Quotability Engine (Round 2 Appendix B & C)
- **The Problem**: Neural retrieval models (dense vector + BM25) chunk documents into ~500-character windows. If key facts rely on unresolved anaphora (*"It provides 99.9% uptime"*, *"They feature zero-knowledge encryption"*), retrieval models score the passage poorly and LLMs refuse to cite the brand.
- **Battle-Hardened Safeguards**:
  - *Scope Gating*: Restricted strictly to technical documentation and informational containers (`<main>`, `<article>`, `[role="main"]`, `<dl>`, `<table>`, `.docs`, `.faq`), excluding narrative founder letters, team stories, and editorial blogs.
  - *Hierarchical Context Injection*: Every chunk is prepended with its nearest parent heading (`H1 > H2 > H3`), modeling modern hierarchical retrieval (LangChain/LlamaIndex) so heading-anchored chunks pass cleanly.
  - *Expletive Pronoun Filter*: Excludes dummy subjects (*"It is essential that..."*, *"It takes 5 minutes..."*).

### ★ Diff 2: Substantive Lexical Density & Anti-Filler Engine (Round 2 Appendix F)
- **The Problem**: Appendix F demonstrates that AI summarizers drop critical transactional facts when surrounded by low-value filler. On web pages, corporate fluff (*"seamlessly synergizing next-gen paradigms"*) dilutes substantive semantic density, causing LLM summarizers to drop core offerings.
- **Battle-Hardened Safeguards**:
  - *Hero Zone Exemption*: Hero sections, H1 headlines, and marketing banners are 100% exempt, fully preserving creative copywriting (Apple, Nike, Linear).
  - *Computational Linguistics*: Uses standard Lexical Density Ratio ($LDR = \frac{\text{content words}}{\text{total words}}$) rather than statistical character entropy.
  - *Informational Anchor Gate*: Only triggers if a technical/feature section contains **zero quantified tokens** (numbers, technical specs, protocols, currencies, percentages) AND is saturated with abstract buzzwords. A single concrete spec passes the section.

### ★ Diff 3: Entity Ambiguity & On-Site Disambiguation Posture (Round 2 Appendix D)
- **The Problem**: Appendix D states that identical/generic names cause AI systems to confuse entities (e.g. brands named "Pulse", "Forge", "Ramp", "Canvas").
- **Battle-Hardened Safeguards**:
  - *100% Offline & Deterministic*: Zero external API calls, zero SPARQL requests, zero rate-limit or firewall risks in sandboxes.
  - *On-Site Disambiguation Posture*: Audits what the webmaster directly controls: Schema.org `legalName`, explicit `@type` (`FinancialService` vs `SoftwareApplication`), `disambiguatingDescription`, and canonical `sameAs` entity links to official registry profiles. Homonym brands with proper on-site markup pass with flying colors.

### ★ Diff 4: Turnkey Zero-Touch Artifact Synthesis (`proactive_engine.py`)
- **The Problem**: Legacy checkers emit passive text advice (*"Consider creating an llms.txt"*).
- **Battle-Hardened Safeguards**:
  - *Strict Schema Parity*: Generated code artifacts (tailored `/llms.txt`, full Schema.org JSON-LD graph, semantic heading citation IDs) are nested **cleanly inside `suggested_action.summary` via Markdown code blocks**. Root JSON schema retains exactly: `site`, `audited_at`, `summary`, and `findings`. Zero unsolicited root keys.
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
    └── engagement-audit/              # Audits 5s orientation, RAG quotability, lexical density
        ├── SKILL.md
        ├── scripts/ (audit_engagement.py, orientation_evaluator.py, hierarchy_evaluator.py, quotability_evaluator.py, filler_evaluator.py)
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
```

### Running Autonomous Sub-Skills Standalone
```bash
python3 skills/crawl-render-audit/scripts/audit_crawl.py https://example.com
python3 skills/freshness-corroboration/scripts/audit_freshness.py https://example.com
python3 skills/engagement-audit/scripts/audit_engagement.py https://example.com
```

### Running the Test Suite
```bash
python3 test_audit.py
```
*All 9 regression tests execute in `< 0.03 seconds` offline (< 1 second total offline, < 15 seconds live).*

---

## 4. Output Schema Parity (Handout Page 2)

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
