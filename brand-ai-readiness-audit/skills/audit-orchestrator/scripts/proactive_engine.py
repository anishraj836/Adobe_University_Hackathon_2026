#!/usr/bin/env python3
"""
Proactive Beyond-Defect Engine — Turnkey Artifact Synthesis (Diff 4)
Synthesizes ready-to-deploy code and markdown artifacts (/llms.txt, Schema.org JSON-LD,
semantic citation anchors) directly within suggested_action.summary, strictly conforming
to Handout Page 2 JSON schema.
"""

import re
from urllib.parse import urlparse

def clean_tag(text: str) -> str:
    """Clean text from tags and excess whitespace."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()

def generate_proactive_actions(bundle: dict, existing_finding_ids: set) -> list:
    """Generate high-impact proactive recommendations with embedded turnkey code artifacts."""
    proactive = []
    html = bundle.get("html", "")
    llms_txt = bundle.get("llms_txt", "")
    url = bundle.get("url", "https://example.com")
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else "https://example.com"
    brand_host = parsed.netloc or parsed.path or "brand.com"

    # Extract real page title and meta description
    title_match = re.search(r'<title\b[^>]*>(.*?)<\/title>', html, re.I)
    page_title = clean_tag(title_match.group(1)) if title_match else brand_host

    meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    meta_desc = clean_tag(meta_match.group(1)) if meta_match else f"Official documentation and resources for {page_title}."

    # 1. Turnkey Artifact: Tailored /llms.txt Manifest
    if not llms_txt and "F-CRAWL-001" not in existing_finding_ids:
        llms_artifact = (
            f"# {page_title} AI Context Manifest\n"
            f"> {meta_desc}\n\n"
            f"## Canonical Resources\n"
            f"- {origin}: Official Homepage\n"
            f"- {origin}/docs: Developer & Product Documentation\n"
            f"- {origin}/llms-full.txt: Full uncompressed documentation for frontier models\n"
        )
        proactive.append({
            "id": "F-PROACT-001",
            "title": "[Proactive Opportunity] Deploy turnkey /llms.txt AI context manifest",
            "severity": "medium",
            "evidence": "No /llms.txt found at origin root; AI assistants must parse and summarize raw HTML payloads.",
            "suggested_action": {
                "summary": (
                    f"Deploy this turnkey /llms.txt manifest at your website root to provide frontier models with instant, structured context:\n\n"
                    f"```markdown\n{llms_artifact}```"
                ),
                "priority": "medium"
            }
        })

    # 2. Turnkey Artifact: Pre-Populated Conversational FAQPage JSON-LD
    has_faq_schema = "faqpage" in html.lower() or "qapage" in html.lower()
    if not has_faq_schema and "F-CRAWL-001" not in existing_finding_ids:
        faq_artifact = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "FAQPage",\n'
            f'  "mainEntity": [\n'
            f'    {{\n'
            f'      "@type": "Question",\n'
            f'      "name": "What core service does {page_title} provide?",\n'
            f'      "acceptedAnswer": {{\n'
            f'        "@type": "Answer",\n'
            f'        "text": "{meta_desc}"\n'
            f'      }}\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
            f'</script>'
        )
        proactive.append({
            "id": "F-PROACT-002",
            "title": "[Proactive Opportunity] Inject conversational FAQPage JSON-LD schema",
            "severity": "medium",
            "evidence": "Page lacks structured FAQPage or QAPage markup optimized for direct question answering.",
            "suggested_action": {
                "summary": (
                    f"Embed this pre-populated Schema.org FAQPage snippet directly in your HTML <head> to maximize inclusion in AI Overview and Perplexity direct answer cards:\n\n"
                    f"```html\n{faq_artifact}\n```"
                ),
                "priority": "medium"
            }
        })

    # 3. Turnkey Artifact: Entity Knowledge Graph Anchoring Graph
    has_sameas = "sameas" in html.lower()
    if not has_sameas and "F-CRAWL-001" not in existing_finding_ids:
        org_artifact = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "Organization",\n'
            f'  "name": "{page_title}",\n'
            f'  "url": "{origin}",\n'
            f'  "description": "{meta_desc}",\n'
            f'  "sameAs": [\n'
            f'    "https://www.linkedin.com/company/{brand_host.replace(".", "-")}",\n'
            f'    "https://www.crunchbase.com/organization/{brand_host.replace(".", "-")}",\n'
            f'    "https://github.com/{brand_host.replace(".", "-")}"\n'
            f'  ]\n'
            f'}}\n'
            f'</script>'
        )
        proactive.append({
            "id": "F-PROACT-003",
            "title": "[Proactive Opportunity] Bridge brand entity to Knowledge Graph registries",
            "severity": "low",
            "evidence": "No entity disambiguation links detected tying the domain to external canonical registries.",
            "suggested_action": {
                "summary": (
                    f"Anchor the brand identity across LLM parametric memory by embedding this Schema.org Organization template with populated sameAs URIs:\n\n"
                    f"```html\n{org_artifact}\n```"
                ),
                "priority": "low"
            }
        })

    # 4. Turnkey Artifact: Semantic Citation Anchor Snippet
    headings_with_id = len(re.findall(r'<h[2-4]\b[^>]*\bid=["\'][^"\']+["\']', html, re.I))
    if headings_with_id < 3 and "F-CRAWL-001" not in existing_finding_ids:
        anchor_example = (
            f'<!-- Example semantic citation anchors for AI deep-linking -->\n'
            f'<h2 id="overview">Platform Overview</h2>\n'
            f'<h2 id="capabilities">Core Capabilities & Specifications</h2>\n'
            f'<h2 id="pricing-tiers">Pricing & Commercial Terms</h2>'
        )
        proactive.append({
            "id": "F-PROACT-004",
            "title": "[Proactive Opportunity] Add semantic anchor IDs to key sections for direct AI citations",
            "severity": "low",
            "evidence": f"Found only {headings_with_id} subheadings with HTML id attributes; conversational AI agents cannot deep-link users directly to cited claims.",
            "suggested_action": {
                "summary": (
                    f"Attach persistent semantic id attributes to all major H2/H3 section headers so AI assistants can cite and deep-link directly to factual claims:\n\n"
                    f"```html\n{anchor_example}\n```"
                ),
                "priority": "low"
            }
        })

    return proactive

if __name__ == "__main__":
    sample_bundle = {
        "html": "<html><head><title>Apex Workflow</title><meta name='description' content='Apex powers autonomous data pipelines.'></head><body><h1>Apex</h1></body></html>",
        "url": "https://apexflow.io"
    }
    p = generate_proactive_actions(sample_bundle, set())
    print(f"Generated {len(p)} proactive actions with turnkey code blocks.")
