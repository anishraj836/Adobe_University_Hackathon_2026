#!/usr/bin/env python3
"""
Turnkey Suggested Action Synthesizer — Strictly Evidence-Conditioned
Delivers drop-in code fixes inside suggested actions rather than generic advice,
ONLY when triggered by concrete observed site evidence, avoiding blanket emissions (padding).
Strictly adheres to Handout Page 2 schema floor.
"""

import os
import sys
import json
import re
from urllib.parse import urlparse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGAGE_SCRIPTS = os.path.abspath(os.path.join(CURRENT_DIR, "../../engagement-audit/scripts"))
if ENGAGE_SCRIPTS not in sys.path:
    sys.path.insert(0, ENGAGE_SCRIPTS)

try:
    from conversion_evaluator import has_commercial_intent
except ImportError:
    def has_commercial_intent(html: str) -> bool:
        schema_matches = re.findall(r'["\']@type["\']\s*:\s*["\']([^"\']+)["\']', html, re.I)
        for s in schema_matches:
            if s.lower() in {"product", "offer", "service", "softwareapplication", "financialproduct", "store", "localbusiness"}:
                return True
        dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
        for href in dom_hrefs:
            if any(cr in href.lower() for cr in ["/pricing", "/product", "/plans", "/demo", "/signup", "/buy", "/checkout", "/solutions", "/shop", "/cart"]):
                return True
        lower_text = html.lower()
        commercial_kw = [r"\bpricing\b", r"\bplans\b", r"\benterprise\b", r"\bsaas\b", r"\bsolutions\b", r"\bfree trial\b", r"\bget started\b", r"\bsubscription\b", r"\bdemo\b", r"\badd to cart\b", r"\bcheckout\b", r"\bshop\b", r"\bcart\b"]
        return sum(1 for kw in commercial_kw if re.search(kw, lower_text)) >= 2

TEMPLATES_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../freshness-corroboration/references/jsonld_templates.json"))
JSONLD_TEMPLATES = {}
if os.path.exists(TEMPLATES_PATH):
    try:
        with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
            JSONLD_TEMPLATES = json.load(f)
    except Exception:
        pass

def clean_tag(text: str) -> str:
    """Clean text from tags and excess whitespace."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()

def format_doc_title(d: str) -> str:
    """Format a clean markdown link title for doc paths or absolute URLs."""
    clean = d.split("?")[0].split("#")[0].rstrip("/")
    if clean.lower().endswith(".html") or clean.lower().endswith(".htm"):
        clean = clean.rsplit(".", 1)[0]
    if clean.startswith("http://") or clean.startswith("https://"):
        p = urlparse(clean)
        path = p.path.strip("/")
        if path:
            seg = path.split("/")
            last = seg[-1].replace("-", " ").replace("_", " ").title()
            return last if len(last) > 1 and not last.isdigit() else (seg[-2].title() if len(seg) > 1 else "Documentation")
        elif p.netloc:
            parts = p.netloc.split(".")
            meaningful = [part.capitalize() for part in parts if part.lower() not in ("www", "org", "com", "io", "net")]
            return " ".join(meaningful) or "Documentation"
    path = clean.strip("/")
    segments = [s for s in path.split("/") if s]
    if segments:
        last = segments[-1].replace("-", " ").replace("_", " ").title()
        return last if len(last) > 1 and not last.isdigit() else (segments[-2].title() if len(segments) > 1 else "Documentation")
    return "Documentation"

def generate_proactive_actions(bundle: dict, existing_finding_ids: set) -> list:
    """
    Generate non-obvious proactive recommendations strictly conditioned on observed site evidence:
    1. FAQPage: ONLY if text contains un-marked Q&A patterns or FAQ sections.
    2. Citation Anchors: ONLY if H2/H3 subheadings exist but lack HTML id attributes.
    3. llms.txt: ONLY if documentation / API / guide routes are observed on-site.
    4. sameAs Bridge: ONLY if commercial entity signals exist but entity ambiguity is detected.
    """
    proactive = []
    html = bundle.get("html", "")
    llms_txt = bundle.get("llms_txt", "")
    url = bundle.get("url", "")
    parsed = urlparse(url)
    canonical = bundle.get("canonical_url", "").strip()

    if canonical.startswith("http"):
        canon_parsed = urlparse(canonical)
        origin = f"{canon_parsed.scheme}://{canon_parsed.netloc}"
        brand_host = canon_parsed.netloc
    elif parsed.netloc:
        origin = f"{parsed.scheme}://{parsed.netloc}"
        brand_host = parsed.netloc
    else:
        origin = ""
        brand_host = "brand.com"

    # If the site is blocked at network level, suppress all proactive suggestions
    if "F-CRAWL-001" in existing_finding_ids:
        return []

    # Extract clean brand/page title (preferring og:site_name, application-name, then cleaned <title>)
    og_name = re.search(r'<meta\s+property=["\']og:site_name["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    if not og_name:
        og_name = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:site_name["\']', html, re.I)
    app_name = re.search(r'<meta\s+name=["\']application-name["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    if not app_name:
        app_name = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']application-name["\']', html, re.I)

    title_match = re.search(r'<title\b[^>]*>(.*?)<\/title>', html, re.I)
    raw_title = clean_tag(title_match.group(1)) if title_match else brand_host

    if og_name and og_name.group(1).strip():
        brand_name = clean_tag(og_name.group(1))
    elif app_name and app_name.group(1).strip():
        brand_name = clean_tag(app_name.group(1))
    else:
        # Strip common boilerplates like "Welcome to ", " - Home", " | Official Site"
        clean = re.sub(r'^(?:Welcome\s+to\s+|Home\s+[-|]\s+)', '', raw_title, flags=re.I)
        clean = re.sub(r'\s+[-|].*$', '', clean)
        brand_name = clean.strip() or raw_title

    page_title = brand_name

    meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    meta_desc = clean_tag(meta_match.group(1)) if meta_match else f"Official documentation and resources for {page_title}."

    # Scan DOM links for documentation / guide / API routes and deduplicate preserving order
    dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    raw_doc_links = [h for h in dom_hrefs if any(k in h.lower() for k in ["/docs", "/doc", "/api", "/guide", "/developers", "/help", "/reference"])]
    seen_links = set()
    doc_links = []
    for d in raw_doc_links:
        clean_d = d.strip()
        if clean_d and clean_d not in seen_links:
            seen_links.add(clean_d)
            doc_links.append(clean_d)

    # 1. Conditioned Proactive Trigger: Markdown-First /llms.txt manifest
    # Condition: Discovered doc/API routes exist, BUT site has no /llms.txt file
    if doc_links and not llms_txt:
        # Generate turnkey llms.txt snippet
        doc_entries = []
        for d in doc_links[:5]:
            full_doc_url = d if d.startswith("http") else (f"{origin.rstrip('/')}/{d.lstrip('/')}" if origin else f"/{d.lstrip('/')}")
            clean_title = format_doc_title(d)
            doc_entries.append(f"- [{clean_title}]({full_doc_url}): Core developer and API documentation.")
        
        docs_block = "\n".join(doc_entries)
        full_index_url = f"{origin}/llms-full.txt" if origin else "/llms-full.txt"
        llms_artifact = (
            f"# {page_title}\n\n"
            f"> {meta_desc}\n\n"
            f"## Documentation Endpoints\n\n"
            f"{docs_block}\n\n"
            f"## Optional\n\n"
            f"- [{page_title} Full Index]({full_index_url}): Complete unpaginated markdown documentation context.\n"
        )
        proactive.append({
            "id": "F-PROACT-001",
            "title": "[Proactive Opportunity] Deploy /llms.txt manifest for discovered documentation assets",
            "severity": "medium",
            "evidence": f"Discovered {len(doc_links)} documentation/API route(s) (e.g. '{doc_links[0]}'), but no /llms.txt file exists at origin root to guide AI inference engines.",
            "suggested_action": {
                "summary": (
                    f"Deploy this turnkey /llms.txt manifest at your website root to index your {len(doc_links)} documentation routes for instant frontier model ingestion:\n\n"
                    f"```markdown\n{llms_artifact}```"
                ),
                "priority": "medium"
            }
        })
    elif llms_txt:
        # Validate existing /llms.txt conforms to standard structure
        has_h1 = bool(re.search(r'^#\s+.+', llms_txt, re.MULTILINE))
        has_links = bool(re.search(r'-\s+\[.+\]\(.+\)', llms_txt))
        if not (has_h1 and has_links):
            proactive.append({
                "id": "F-PROACT-005",
                "title": "[Proactive Opportunity] Enhance existing /llms.txt structure for frontier AI ingest",
                "severity": "medium",
                "evidence": "Observed /llms.txt file at origin root lacks recommended standard structure (H1 title or markdown link list).",
                "suggested_action": {
                    "summary": "Structure /llms.txt following the standard convention with an H1 page title, a blockquote summary (> ...), and a curated list of markdown links (- [Title](URL)) pointing to clean markdown or HTML documentation endpoints.",
                    "priority": "medium"
                }
            })

    # 2. Conditioned Proactive Trigger: Conversational FAQPage JSON-LD
    # Condition: Page contains actual Q&A questions/FAQ in text, BUT lacks Schema.org FAQPage/QAPage
    has_faq_schema = "faqpage" in html.lower() or "qapage" in html.lower()
    # Find natural question sentences in text and extract immediate sibling answer
    question_matches = []
    extracted_answer = None
    sample_q = None

    for q_match in re.finditer(r'(?:<h[2-4]\b[^>]*>|<p><strong>|<dt>)([^<]*\?)(?:<\/h[2-4]>|<\/strong><\/p>|<\/dt>)', html, re.I):
        q_text = q_match.group(1).strip()
        question_matches.append(q_text)
        if sample_q is None:
            sample_q = q_text
            # Check immediate sibling element following this question
            post_html = html[q_match.end():].lstrip()
            sib_match = re.match(r'<(p|div|dd|ul)\b[^>]*>(.*?)<\/\1>', post_html, re.I | re.DOTALL)
            if sib_match:
                candidate_ans = clean_tag(sib_match.group(2))
                if len(candidate_ans) >= 15 and not candidate_ans.startswith("<h"):
                    extracted_answer = candidate_ans

    has_faq_keyword = bool(re.search(r'\b(frequently asked questions|faq|common questions)\b', html, re.I))

    if (question_matches or has_faq_keyword) and not has_faq_schema:
        if not sample_q:
            sample_q = f"What does {page_title} do?"

        answer_text = extracted_answer if extracted_answer else meta_desc
        answer_escaped = answer_text.replace('\\', '\\\\').replace('"', '\\"')
        sample_q_escaped = sample_q.replace('\\', '\\\\').replace('"', '\\"')

        faq_artifact = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "FAQPage",\n'
            f'  "mainEntity": [\n'
            f'    {{\n'
            f'      "@type": "Question",\n'
            f'      "name": "{sample_q_escaped}",\n'
            f'      "acceptedAnswer": {{\n'
            f'        "@type": "Answer",\n'
            f'        "text": "{answer_escaped}"\n'
            f'      }}\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
            f'</script>'
        )
        proactive.append({
            "id": "F-PROACT-002",
            "title": "[Proactive Opportunity] Structure discovered Q&A content into FAQPage JSON-LD",
            "severity": "medium",
            "evidence": f"Detected {len(question_matches)} natural question(s) in body copy (e.g. '{sample_q}'), but page lacks structured FAQPage markup.",
            "suggested_action": {
                "summary": (
                    f"Embed this pre-populated Schema.org FAQPage snippet in your HTML <head> to enable zero-shot answer extraction in Perplexity and ChatGPT Search:\n\n"
                    f"```html\n{faq_artifact}\n```"
                ),
                "priority": "medium"
            }
        })

    # 3. Conditioned Proactive Trigger: Knowledge Graph sameAs Bridge
    # Condition: Commercial entity signals observed, BUT missing sameAs links
    has_sameas = "sameas" in html.lower()
    is_commercial = has_commercial_intent(html)

    if is_commercial and not has_sameas:
        org_url = origin if origin else (canonical if canonical else "https://brand.example.com")
        org_artifact = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "Organization",\n'
            f'  "name": "{page_title}",\n'
            f'  "url": "{org_url}",\n'
            f'  "description": "{meta_desc}",\n'
            f'  "sameAs": [\n'
            f'    "https://www.linkedin.com/company/<YOUR_LINKEDIN_SLUG>",\n'
            f'    "https://www.crunchbase.com/organization/<YOUR_CRUNCHBASE_SLUG>",\n'
            f'    "https://github.com/<YOUR_GITHUB_ORG>"\n'
            f'  ]\n'
            f'}}\n'
            f'</script>'
        )
        proactive.append({
            "id": "F-PROACT-003",
            "title": "[Proactive Opportunity] Bridge commercial brand entity to Knowledge Graph registries",
            "severity": "medium",
            "evidence": "Commercial product/pricing signals detected, but no Schema.org sameAs links ground the brand to external knowledge graph registries.",
            "suggested_action": {
                "summary": (
                    f"Anchor the brand identity across LLM parametric memory by embedding this Schema.org Organization template in your HTML <head> (replace `<YOUR_*_SLUG>` placeholder tokens with your verified registry URLs):\n\n"
                    f"```html\n{org_artifact}\n```"
                ),
                "priority": "medium"
            }
        })

    # 4. Conditioned Proactive Trigger: Semantic Citation Anchor IDs
    # Condition: Multiple subheadings (>=2) exist, BUT < 25% have HTML id attributes
    subheadings = re.findall(r'<h[2-4]\b([^>]*)>(.*?)<\/h[2-4]>', html, re.I | re.DOTALL)
    if len(subheadings) >= 2 and "F-ENGAGE-005" not in existing_finding_ids:
        anchored_count = sum(1 for attrs, _ in subheadings if re.search(r'\bid=["\'][^"\']+["\']', attrs, re.I))
        pct_anchored = (anchored_count / len(subheadings)) * 100
        if pct_anchored < 25:
            anchor_example = (
                '<!-- Example semantic citation anchors for AI deep-linking -->\n'
                '<h2 id="overview">Platform Overview</h2>\n'
                '<h2 id="features">Core Capabilities & Specifications</h2>\n'
                '<h2 id="pricing">Pricing & Commercial Terms</h2>'
            )
            proactive.append({
                "id": "F-PROACT-004",
                "title": "[Proactive Opportunity] Add semantic anchor IDs to key sections for direct AI citations",
                "severity": "medium",
                "evidence": f"Found {len(subheadings)} section headings, but only {anchored_count} ({pct_anchored:.0f}%) possess HTML id attributes; conversational AI agents cannot deep-link users directly to cited claims.",
                "suggested_action": {
                    "summary": (
                        f"Attach persistent semantic id attributes to your {len(subheadings)} section headers so AI assistants can cite and deep-link directly to factual claims:\n\n"
                        f"```html\n{anchor_example}\n```"
                    ),
                    "priority": "medium"
                }
            })

    return proactive

if __name__ == "__main__":
    sample_bundle = {
        "html": "<html><head><title>Apex Workflow</title></head><body><h1>Apex</h1><a href='/docs'>Docs</a><h2>Overview</h2><p>How do I start?</p></body></html>",
        "url": "https://apexflow.io"
    }
    p = generate_proactive_actions(sample_bundle, set())
    print(f"Conditioned proactive suggestions generated: {len(p)}")
    for item in p:
        print(" -", item["title"])
