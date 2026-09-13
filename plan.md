# Brand AI-Readiness Audit Marketplace — Certified Execution Plan

**Adobe University Hackathon 2026 — Round 3: Build the Agent Skill Marketplace**  
**Document:** `plan.md`  
**Status:** Certified & Approved by Multi-Agent Consensus (Domain Expert, Red Team Critic, Fresh Eyes Lead Auditor)

---

## 1. Executive Summary & Challenge Overview

Round 3 tests encoding reasoning from Round 2 into a reusable, modular **Agent Skill Marketplace** authored in the standard `agentskills.io` format. When pointed at any website (or local test fixture), the marketplace automatically audits:
1. **Off-Site AI Discoverability**: Why the brand isn't found, trusted, or cited by AI assistants (ChatGPT, Claude, Perplexity, Gemini, AI search overviews).
2. **On-Site Engagement**: Why visitors who arrive via AI referrals bounce or fail to convert (cognitive orientation, context retention, friction traps).

The marketplace emits a single, machine-readable audit report adhering strictly to the required Handout Page 2 schema, containing:
- **Evidence-backed problems found** (Round 2 failure modes) with assigned severities (`critical`, `high`, `medium`, `low`).
- **Mechanism-sound, prioritized suggested actions** for every detected problem.
- **Proactive beyond-defect improvements** that strengthen AI discoverability and engagement even where no explicit defect exists.

---

## 2. Multi-Stage Audit & Consensus Record

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  Stage 1: Domain Expert │ ──> │   Stage 2: Red Team     │ ──> │   Stage 3: Fresh Eyes   │
│  (Rubric & Schema Spec) │     │ (Adversarial Critic)    │     │   (Final Sign-Off)      │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
  • Verified AEO/GEO mechanics    • Enforced 4 battle-hardened    • Certified 10/10 across all
  • Certified RAG Chunking &        safeguards against false        6 rubric criteria
    Lexical Density alignment       positives on creative copy    • Granted unconditional green
  • Approved 4 Differentiators    • Prohibited schema drift         light for implementation
```

---

## 3. The 4 Impressive Key Differentiators & Battle-Hardened Safeguards

### ★ Differentiator 1: LLM RAG Citation & Quotability Engine (Round 2 Appendix B & C)
- **Problem Solved**: AI search agents (Perplexity, ChatGPT Search) slice documents into ~500-character embedding chunks. If key propositions rely on unresolved third-person pronouns (*"It provides 99.9% uptime"*, *"They feature zero-knowledge encryption"*), neural retrieval models score the passage poorly and generation models refuse to quote it.
- **Battle-Hardened Safeguards**:
  1. *Scope Gating*: Restricted strictly to technical documentation and informational containers (`<main>`, `<article>`, `[role="main"]`, `<dl>`, `<table>`, `.docs`, `.faq`). Narrative founder letters, team journeys, and personal blogs are explicitly excluded.
  2. *Hierarchical Context Injection*: Every chunk is prepended with its nearest parent heading (`H1 > H2 > H3`), modeling modern hierarchical retrieval (LangChain/LlamaIndex) so heading-anchored chunks pass cleanly.
  3. *Expletive Pronoun Filter*: Distinguishes true referential anaphora from dummy/pleonastic subjects (*"It is essential that..."*, *"It takes 5 minutes..."*).
  4. *Severity Bounded*: Capped at `medium` or `low` to avoid drowning out critical crawl blocks.

### ★ Differentiator 2: Substantive Lexical Density & Anti-Filler Engine (Round 2 Appendix F)
- **Problem Solved**: Appendix F shows that AI summarizers drop critical information when surrounded by low-value filler. On web pages, generic corporate fluff (*"seamlessly synergizing next-gen paradigms"*) dilutes substantive semantic density, causing LLM summarizers to drop core offerings.
- **Battle-Hardened Safeguards**:
  1. *Hero Zone Exemption*: Hero sections, H1 headlines, and marketing banners are 100% exempt, fully preserving creative copywriting (e.g. Apple, Nike, Linear).
  2. *Computational Linguistics*: Uses standard Lexical Density Ratio ($LDR = \frac{\text{content words}}{\text{total words}}$) rather than pseudo-scientific character entropy.
  3. *Informational Anchor Gate*: Only triggers if a technical/feature section contains **zero quantified tokens** (numbers, technical specs, protocols, currencies, percentages) AND is saturated with abstract buzzwords. A single concrete spec passes the section.
  4. *Constructive Remediation*: Suggests adding quantified performance benchmarks or comparison tables.

### ★ Differentiator 3: Entity Ambiguity & On-Site Disambiguation Posture (Round 2 Appendix D)
- **Problem Solved**: Appendix D states that identical/generic names cause AI systems to confuse entities (e.g. brands named "Pulse", "Forge", "Ramp", "Canvas").
- **Battle-Hardened Safeguards**:
  1. *100% Offline & Deterministic*: Zero external API calls, zero SPARQL requests, zero rate-limit or firewall risks in sandboxes.
  2. *On-Site Disambiguation Posture*: Audits what the webmaster directly controls: Schema.org `legalName`, explicit `@type` (`FinancialService` vs `SoftwareApplication`), `disambiguatingDescription`, and canonical `sameAs` entity links to official registry profiles. Homonym brands with proper on-site markup pass with flying colors.

### ★ Differentiator 4: Turnkey Zero-Touch Artifact Synthesis (`proactive_engine.py`)
- **Problem Solved**: Rather than offering passive text advice, the orchestrator auto-generates copy-paste ready artifacts tailored to the audited site.
- **Battle-Hardened Safeguards**:
  1. *Strict Schema Parity*: Generated code artifacts (tailored `/llms.txt`, full Schema.org JSON-LD graph, semantic heading citation IDs) are nested **cleanly inside `suggested_action.summary` via Markdown code blocks**. Root JSON schema retains exactly: `site`, `audited_at`, `summary`, and `findings`. Zero unsolicited root keys.
  2. *Real Discovered Metadata*: Ingests real extracted page titles, meta descriptions, canonical URLs, and section headings, avoiding hallucinated placeholder text.
  3. *Recommend-Only Discipline*: Fully passive, read-only inspection.

---

## 4. Architecture & Marketplace Layout

```text
brand-ai-readiness-audit/
├── marketplace.json                   # Contest manifest (lists all skills, entrypoint: true)
├── README.md                          # Architecture, skill decomposition, and CLI usage
├── test_audit.py                      # Automated test suite running offline in < 0.05 seconds
├── fixtures/                          # 5 synthetic offline HTML/robots.txt test cases
│   ├── blocked_site/
│   ├── pure_csr_spa/
│   ├── modern_nextjs_ssr/
│   ├── stale_and_uncorroborated/
│   └── high_performing_brand/
└── skills/
    ├── audit-orchestrator/            # [ENTRYPOINT] Orchestration, causal shielding, report synthesis
    │   ├── SKILL.md                   # agentskills.io spec with YAML frontmatter
    │   ├── scripts/
    │   │   ├── run_audit.py           # Top-level CLI entrypoint
    │   │   ├── schema_validator.py    # Handout Page 2 schema compliance validator
    │   │   └── proactive_engine.py    # Turnkey artifact synthesis (llms.txt, Schema.org graph)
    │   └── references/ (report_schema.json, scoring_rubric.md)
    ├── crawl-render-audit/            # Technical crawlability & JS-render gaps
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── audit_crawl.py         # Autonomous CLI for crawl & render audit
    │   │   └── http_fetcher.py        # Dual-probe fetcher (Browser UA + GPTBot UA)
    │   └── references/ (ai_crawlers.json, spa_signatures.json)
    ├── freshness-corroboration/       # Structured data, entity disambiguation & temporal staleness
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── audit_freshness.py     # Entity ambiguity matrix & 4-way freshness corroboration
    │   └── references/ (jsonld_templates.json, authority_registries.json)
    └── engagement-audit/              # On-site visitor orientation, heading hierarchy & friction
        ├── SKILL.md
        ├── scripts/
        │   └── audit_engagement.py    # RAG quotability engine & Lexical Density Anti-Filler engine
        └── references/ (orientation_rubric.md, friction_patterns.json, filler_lexicon.json)
```

---

## 5. Output JSON Schema Contract

Strictly adheres to Handout Page 2:
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
      "title": "Robots.txt blocks AI crawler user-agents",
      "severity": "critical",
      "evidence": "Robots.txt contains Disallow: / for GPTBot, ClaudeBot.",
      "suggested_action": {
        "summary": "Update robots.txt to explicitly allow GPTBot and ClaudeBot on public content routes.",
        "priority": "critical"
      }
    }
  ]
}
```
