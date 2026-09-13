# Empirical Field Research: Learning from the Wild

**Methodology Mandate (Handout Page 1):**  
*"Go find real websites that AI assistants cite well versus ones they ignore or misrepresent, and work out what makes the difference. Distil those learnings — the concrete, repeatable signals that separate cited from uncited (the Round-2 failure modes) — into your skill, each with evidence and a severity."*

This document formalizes the empirical field research conducted across live commercial domains to ground our detection heuristics in observed web reality rather than textbook assumptions.

---

## 1. Case Study 1: AI Crawler Access & WAF Gates (Cloudflare vs. The New York Times)

### Observation
- **Cloudflare (`cloudflare.com/robots.txt`)**:
  - Explicitly declares permissive rules for AI crawlers:
    ```text
    User-agent: GPTBot
    Allow: /
    User-agent: PerplexityBot
    Allow: /
    ```
  - *Observed Pattern*: Permissive crawler rules allow retrieval engines to ingest technical documentation and incident reports directly, supporting direct citation and accurate retrieval across conversational assistants.
- **The New York Times (`nytimes.com/robots.txt`)**:
  - Explicitly blacklists AI search crawlers:
    ```text
    User-agent: ClaudeBot
    Disallow: /
    User-agent: GPTBot
    Disallow: /
    User-agent: PerplexityBot
    Disallow: /
    ```
  - *Observed Pattern*: Blocking AI crawlers at the robots.txt level prevents conversational assistants from accessing fresh article content directly, which can push citation toward secondary aggregators instead of the original source.

### Heuristic Encoded
- **`F-CRAWL-003` (Robots.txt Blocks AI Crawlers)**:
  - Scans `robots.txt` specifically for AI bot user-agents (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, `Applebot-Extended`, `Amazonbot`, `Bytespider`, `CCBot`).
  - Severity: `critical` if `*` or `GPTBot` is blocked; `high` for secondary crawlers.
  - Evidence: Exact disallow directives extracted.

---

## 2. Case Study 2: Structured Data & Entity Grounding (Stripe vs. Linear)

### Observation
- **Stripe (`stripe.com`)**:
  - Emits pre-rendered Schema.org `Organization` JSON-LD on static HTTP response with complete `sameAs` array linking to official LinkedIn, Crunchbase, Wikipedia, and Twitter profiles.
  - *Observed Pattern*: Stripe's complete Organization JSON-LD with sameAs links to LinkedIn, Crunchbase, Wikipedia, and Twitter reduces entity-ambiguity risk for retrieval systems resolving brand identity against common dictionary homonyms.
- **Linear (`linear.app`)**:
  - Uses client-side single-page architecture where root HTML omits static `Organization` JSON-LD.
  - *Observed Pattern*: When initial HTML omits static Organization markup, retrieval systems operating without headless browser execution have fewer authoritative on-site disambiguation signals, increasing the risk of entity confusion for generic polysemous names like "Linear".

### Heuristic Encoded
- **`F-FRESH-008` (Entity Ambiguity & On-Site Disambiguation Posture)**:
  - Evaluates brand name polysemy against dictionary homonyms (`Linear`, `Ramp`, `Atlas`, `Pulse`).
  - Asserts presence of Schema.org `legalName`, specialized `@type`, and outbound `sameAs` links.

---

## 3. Case Study 3: Gzipped Sitemaps & Index Architecture (Large Publishers)

### Observation
- Many large publishers and enterprise platforms (such as `nytimes.com`) frequently serve **Gzipped Sitemaps** (`sitemap.xml.gz`) or **Sitemap Indexes** (`<sitemapindex>`) declared in `robots.txt`, rather than a single raw XML file at the root path.
- Naive crawlers that assume uncompressed XML or rely solely on default `/sitemap.xml` paths risk binary decode errors or false-positive missing sitemap findings when inspecting compressed payloads.

### Heuristic Encoded
- **`F-CRAWL-008` (XML Sitemap Resolution)**:
  - Parses `robots.txt` `Sitemap:` directives first.
  - Handles `.xml.gz` decompression via `gzip.decompress()` transparently.

---

## 4. Case Study 4: Deep Citation Anchoring (Perplexity Source Deep-Linking)

### Observation
- Technical documentation sites that are frequently cited with section-level jump links (such as MDN Web Docs, Stripe Documentation, and Python Official Docs) typically attach semantic HTML `id` attributes to substantive headings:
  ```html
  <h2 id="create-payment-intent">Create a PaymentIntent</h2>
  ```
- When heading `id` attributes are absent, AI search interfaces typically can only link to the top-level page URL, increasing orientation friction for referred visitors trying to locate the specific quoted passage.

### Heuristic Encoded
- **`F-ENGAGE-005` & Conditioned Proactive Trigger `F-PROACT-004`**:
  - Calculates percentage of `<h2>`/`<h3>` subheadings with persistent HTML `id` attributes.
  - Generates turnkey anchor ID injection templates.

---

## 5. Case Study 5: Conversion Friction & User Journey Dead-Ends for AI Referrals

### Observation
- Conversational AI queries frequently direct high-intent users to specific informational landing pages (e.g., pricing questions, compliance checks, feature comparisons).
- When a target landing page lacks clear next steps — such as prominent CTAs, verifiable trust proof (compliance badges, customer quotes), commercial navigation (/pricing, /contact), or discoverable FAQ paths — visitors face higher conversion friction.
- Well-structured commercial domains commonly provide explicit conversion pathways and verifiable trust signals alongside their technical claims.

### Heuristic Encoded
- **`F-ENGAGE-011` through `F-ENGAGE-014` (`conversion_evaluator.py`)**:
  - Evaluates primary Call to Action (CTA) presence and clarity.
  - Audits trust proof signals (certifications, testimonials, review ratings).
  - Verifies commercial conversion routes (`/pricing`, `/contact`, `/demo`, `/docs`, `/signup`).
  - Audits discoverable self-serve FAQ/support paths.
