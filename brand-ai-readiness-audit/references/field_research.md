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
  - *Result*: Cloudflare documentation, blog posts, and incident reports are cited with extreme frequency and high factual accuracy across ChatGPT, Perplexity, and Claude.
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
  - *Result*: Conversational AI assistants cannot access fresh articles directly, falling back on secondary aggregator citations or refusing to quote current news.

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
  - *Result*: AI assistants never confuse Stripe with common homonyms (e.g., striped patterns, zebras, stripe cards) and quote exact corporate information without hallucination.
- **Linear (`linear.app`)**:
  - Uses client-side single-page architecture where root HTML omits static `Organization` JSON-LD.
  - *Result*: AI models without headless browser execution risk conflating "Linear" with the mathematical concept ("linear regression") unless explicitly prompted with "Linear app issue tracking".

### Heuristic Encoded
- **`F-FRESH-008` (Entity Ambiguity & On-Site Disambiguation Posture)**:
  - Evaluates brand name polysemy against dictionary homonyms (`Linear`, `Ramp`, `Atlas`, `Pulse`).
  - Asserts presence of Schema.org `legalName`, specialized `@type`, and outbound `sameAs` links.

---

## 3. Case Study 3: Gzipped Sitemaps & Index Architecture (Large Publishers)

### Observation
- Enterprise sites (`nytimes.com`, large e-commerce platforms) do not serve raw uncompressed XML at `/sitemap.xml`.
- They serve **Gzipped Sitemaps** (`sitemap.xml.gz`) or **Sitemap Indexes** (`<sitemapindex>`) declared exclusively inside `robots.txt`.
- Naive crawlers attempting raw XML parsing on `/sitemap.xml` throw binary decode exceptions or false-positive missing sitemap findings.

### Heuristic Encoded
- **`F-CRAWL-008` (XML Sitemap Resolution)**:
  - Parses `robots.txt` `Sitemap:` directives first.
  - Handles `.xml.gz` decompression via `gzip.decompress()` transparently.

---

## 4. Case Study 4: Deep Citation Anchoring (Perplexity Source Deep-Linking)

### Observation
- Sites that Perplexity Search and ChatGPT Search cite with paragraph-level jump links (e.g. MDN Web Docs, Stripe Documentation, Python Official Docs) attach semantic HTML `id` attributes to every substantive heading:
  ```html
  <h2 id="create-payment-intent">Create a PaymentIntent</h2>
  ```
- Sites lacking heading `id` attributes force AI assistants to link only to the top-level URL (`https://example.com`), causing arriving visitors to bounce because they cannot find the specific quoted passage.

### Heuristic Encoded
- **`F-ENGAGE-005` & Conditioned Proactive Trigger `F-PROACT-004`**:
  - Calculates percentage of `<h2>`/`<h3>` subheadings with persistent HTML `id` attributes.
  - Generates turnkey anchor ID injection templates.
