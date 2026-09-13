#!/usr/bin/env python3
"""
Engagement & Friction Audit Skill
Audits 5-second cognitive orientation, referral landing, heading hierarchy, content density,
LLM RAG Quotability (Diff 1), and Lexical Density Anti-Filler (Diff 2).
"""

import os
import sys
import json
import re

# Ensure local script directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

CRAWL_SCRIPTS = os.path.abspath(os.path.join(CURRENT_DIR, "../../crawl-render-audit/scripts"))
if CRAWL_SCRIPTS not in sys.path:
    sys.path.insert(0, CRAWL_SCRIPTS)

from http_fetcher import fetch_target_bundle

TRUST_KEYWORDS = ["privacy", "terms", "contact", "about", "security", "legal"]

# Load filler lexicon
LEXICON_PATH = os.path.join(CURRENT_DIR, "../references/filler_lexicon.json")
FLUFF_WORDS = set()
QUANT_PATTERNS = []
if os.path.exists(LEXICON_PATH):
    try:
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            FLUFF_WORDS = set(data.get("fluff_words", []))
            QUANT_PATTERNS = [re.compile(p, re.I) for p in data.get("quantified_patterns", [])]
    except Exception:
        pass

def strip_chrome(html: str) -> str:
    """Strip navigation, headers, footers, scripts, and styles to isolate substantive content."""
    clean = re.sub(r'<(script|style|nav|header|footer|aside)\b[^<]*(?:(?!<\/\1>)<[^<]*)*<\/\1>', ' ', html, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    return re.sub(r'\s+', ' ', clean).strip()

def evaluate_rag_quotability(html: str, brand_hint: str = "") -> dict:
    """
    Differentiator 1: LLM RAG Quotability Engine.
    Simulates neural retrieval passage slicing (500 chars).
    Applies Battle-Hardened Safeguards:
    1. Scope Gating: Evaluates <main> or <article> containers, excluding editorial /blog and /story.
    2. Hierarchical Context Injection: Prepends nearest parent heading (H1 > H2 > H3).
    3. Expletive Pronoun Filter: Filters dummy subjects ('It is...', 'It was...').
    4. Bounded severity.
    """
    # Scope Gating: Extract main/article content
    main_match = re.search(r'<(main|article)\b[^>]*>(.*?)<\/\1>', html, re.DOTALL | re.IGNORECASE)
    eval_html = main_match.group(2) if main_match else html

    # Exclude editorial blog/story markers
    if re.search(r'\b(founder-letter|personal-story|blog-post|author-bio)\b', eval_html, re.I):
        return {"flagged": False, "score": 100, "evidence": "Narrative container exempted by scope gate."}

    # Extract sections with parent headings
    sections = re.split(r'(<h[1-4]\b[^>]*>.*?<\/h[1-4]>)', eval_html, flags=re.I | re.DOTALL)
    current_heading = "General"
    chunks = []

    for part in sections:
        part_clean = part.strip()
        if not part_clean:
            continue
        h_match = re.match(r'<h[1-4]\b[^>]*>(.*?)<\/h[1-4]>', part_clean, re.I | re.DOTALL)
        if h_match:
            current_heading = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
        else:
            prose = re.sub(r'<[^>]+>', ' ', part_clean)
            prose = re.sub(r'\s+', ' ', prose).strip()
            # Split into ~500 char chunks
            words = prose.split()
            buffer = []
            char_count = 0
            for w in words:
                buffer.append(w)
                char_count += len(w) + 1
                if char_count >= 500:
                    chunk_text = f"[{current_heading}] " + " ".join(buffer)
                    chunks.append(chunk_text)
                    buffer = []
                    char_count = 0
            if buffer and len(buffer) > 15:
                chunks.append(f"[{current_heading}] " + " ".join(buffer))

    if len(chunks) < 3:
        return {"flagged": False, "score": 100, "evidence": "Insufficient chunk volume for RAG simulation."}

    dangling_count = 0
    expletive_pattern = re.compile(r'\bit\s+(?:is|was|takes|seems|appears|has\s+been)\b', re.I)
    pronoun_start_pattern = re.compile(r'(?:^|[\.\?!]\s+)(?:it|they|this|these|the platform|the system)\b', re.I)

    for ch in chunks:
        # If chunk contains explicit brand hint, passes entity binding
        if brand_hint and brand_hint.lower() in ch.lower():
            continue
        # Check for dangling pronoun starts
        matches = pronoun_start_pattern.findall(ch)
        if matches:
            # Filter out expletive dummy subjects
            real_dangling = False
            for m in matches:
                # Find context around match
                idx = ch.lower().find(m.strip().lower())
                if idx >= 0:
                    surrounding = ch[idx:idx+35]
                    if not expletive_pattern.search(surrounding):
                        real_dangling = True
                        break
            if real_dangling:
                dangling_count += 1

    aqs = int(((len(chunks) - dangling_count) / len(chunks)) * 100)
    flagged = aqs < 50 and dangling_count >= 2

    return {
        "flagged": flagged,
        "score": aqs,
        "total_chunks": len(chunks),
        "dangling_chunks": dangling_count,
        "evidence": f"Simulated {len(chunks)} RAG retrieval chunks (500 chars); {dangling_count}/{len(chunks)} ({int((dangling_count/len(chunks))*100)}%) rely on dangling pronouns without explicit entity binding. AI Quotability Score: {aqs}/100."
    }

def evaluate_lexical_density(html: str) -> dict:
    """
    Differentiator 2: Substantive Lexical Density & Anti-Filler Engine (Appendix F).
    Applies Battle-Hardened Safeguards:
    1. Hero Zone Exemption: Strips hero headers and top headlines.
    2. Computational Lexical Density Ratio (LDR) over pseudo-scientific entropy.
    3. Informational Anchor Gate: Only triggers if zero quantified tokens AND high fluff concentration.
    """
    # Exclude hero section
    non_hero_html = re.sub(r'<(header|section\b[^>]*class=["\'][^"\']*(?:hero|banner|jumbotron)[^"\']*["\'])[^>]*>.*?<\/\1>', '', html, flags=re.I | re.DOTALL)
    prose = strip_chrome(non_hero_html)
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9\-\.%]+\b', prose)]

    if len(words) < 80:
        return {"flagged": False, "evidence": "Short content; hero exemption applied."}

    # Count quantified tokens
    quant_matches = 0
    for pat in QUANT_PATTERNS:
        quant_matches += len(pat.findall(prose))

    # Count fluff buzzwords
    fluff_count = sum(1 for w in words if w in FLUFF_WORDS)
    fluff_ratio = (fluff_count / len(words)) * 100

    # Informational Anchor Gate:
    # Only flag if ZERO quantified metrics AND fluff ratio > 4% of total words
    flagged = (quant_matches == 0) and (fluff_count >= 5) and (fluff_ratio > 3.5)

    return {
        "flagged": flagged,
        "fluff_count": fluff_count,
        "quant_matches": quant_matches,
        "fluff_ratio": fluff_ratio,
        "evidence": f"Analyzed substantive technical prose; detected {fluff_count} corporate buzzwords against {quant_matches} quantified metrics (buzzword saturation: {fluff_ratio:.1f}%). High risk of AI summarizer dropout per Appendix F."
    }

def audit_engagement(bundle: dict) -> list:
    """Audit visitor orientation, referral retention, heading hierarchy, RAG quotability, and lexical density."""
    findings = []
    html = bundle.get("html", "")
    home_status = bundle.get("status", 200)

    if home_status == 0 or (home_status >= 400 and home_status != 404):
        return []

    # 1. 5-Second Cognitive Orientation (H1 & Meta Description)
    h1_matches = re.findall(r'<h1\b[^>]*>(.*?)<\/h1>', html, re.I | re.DOTALL)
    meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.I)

    brand_hint = ""
    if h1_matches:
        h1_text = re.sub(r'<[^>]+>', '', h1_matches[0]).strip()
        words = h1_text.split()
        if words:
            brand_hint = words[0]

    if not h1_matches:
        findings.append({
            "id": "F-ENGAGE-001",
            "title": "Missing primary <h1> heading for visitor orientation",
            "severity": "high",
            "evidence": "Crawled page; 0 <h1> heading tags detected in static DOM.",
            "suggested_action": {
                "summary": "Add a prominent <h1> tag within the hero section clearly stating what the company or product does.",
                "priority": "high"
            }
        })
    elif len(h1_matches) > 2:
        findings.append({
            "id": "F-ENGAGE-002",
            "title": "Multiple competing <h1> headings cause orientation ambiguity",
            "severity": "medium",
            "evidence": f"Found {len(h1_matches)} distinct <h1> tags, creating conflicting hierarchy signals for visitors and scrapers.",
            "suggested_action": {
                "summary": "Consolidate into a single clear <h1> representing the core proposition, demoting secondary headings to <h2>.",
                "priority": "medium"
            }
        })
    else:
        h1_text = re.sub(r'<[^>]+>', '', h1_matches[0]).strip()
        if len(h1_text) < 5:
            findings.append({
                "id": "F-ENGAGE-003",
                "title": "Vague or empty primary <h1> headline",
                "severity": "medium",
                "evidence": f"Primary <h1> is only {len(h1_text)} characters ('{h1_text}').",
                "suggested_action": {
                    "summary": "Refine the <h1> headline to communicate a specific, concise value proposition.",
                    "priority": "medium"
                }
            })

    if not meta_desc_match or not meta_desc_match.group(1).strip():
        findings.append({
            "id": "F-ENGAGE-004",
            "title": "Missing or empty meta description",
            "severity": "medium",
            "evidence": "No valid <meta name='description'> tag found in document <head>.",
            "suggested_action": {
                "summary": "Add a high-signal meta description (120-160 characters) summarizing page purpose for search snippets and AI overview cards.",
                "priority": "medium"
            }
        })

    # 2. AI Referral Landing & Deep-Link Citation Anchors (Appendix B)
    subheadings = re.findall(r'<h[2-4]\b([^>]*)>(.*?)<\/h[2-4]>', html, re.I | re.DOTALL)
    if subheadings:
        anchored_count = sum(1 for attrs, _ in subheadings if re.search(r'\bid=["\'][^"\']+["\']', attrs, re.I))
        pct_anchored = (anchored_count / len(subheadings)) * 100
        if pct_anchored < 25:
            findings.append({
                "id": "F-ENGAGE-005",
                "title": "Subheadings lack persistent citation anchor IDs",
                "severity": "medium",
                "evidence": f"Only {anchored_count}/{len(subheadings)} (H2-H4) subheadings possess HTML id attributes for fragment deep-linking.",
                "suggested_action": {
                    "summary": "Attach persistent semantic id attributes (e.g., id='features', id='pricing') to all H2/H3 headers so AI assistants can cite and deep-link directly to factual claims.",
                    "priority": "medium"
                }
            })

    # 3. Substantive Content Density vs Boilerplate
    substantive_text = strip_chrome(html)
    substantive_words = len(substantive_text.split())

    if substantive_words < 120 and len(html) > 800:
        findings.append({
            "id": "F-ENGAGE-006",
            "title": "Low substantive body content (thin landing experience)",
            "severity": "high",
            "evidence": f"Isolated only {substantive_words} words of substantive body prose after stripping UI chrome and navigation.",
            "suggested_action": {
                "summary": "Expand landing page body copy with concrete specifications, benefits, and FAQ answers to retain arriving AI-referred traffic.",
                "priority": "high"
            }
        })

    # 4. Trust & Compliance Signals
    dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    found_trust_signals = set()
    for href in dom_hrefs:
        lower_href = href.lower()
        for kw in TRUST_KEYWORDS:
            if kw in lower_href:
                found_trust_signals.add(kw)

    if len(found_trust_signals) < 2:
        findings.append({
            "id": "F-ENGAGE-007",
            "title": "Missing essential trust and compliance routes",
            "severity": "medium",
            "evidence": f"Identified only {len(found_trust_signals)} trust anchor(s) ({', '.join(found_trust_signals) or 'none'}); missing privacy policy, terms, or contact links.",
            "suggested_action": {
                "summary": "Provide explicit links to Privacy Policy, Terms of Service, and Contact/About information to establish brand legitimacy.",
                "priority": "medium"
            }
        })

    # 5. Differentiator 1: LLM RAG Quotability Engine
    rag_eval = evaluate_rag_quotability(html, brand_hint)
    if rag_eval.get("flagged"):
        findings.append({
            "id": "F-ENGAGE-008",
            "title": "High RAG retrieval failure risk: Substantive facts lack self-contained entity binding",
            "severity": "medium",
            "evidence": rag_eval.get("evidence"),
            "suggested_action": {
                "summary": "Refactor fragmented body copy into self-contained Subject-Predicate-Object propositions. Replace anaphoric pronouns with explicit brand/feature names in key declarations so neural RAG retrievers can extract isolated passages without context loss.",
                "priority": "medium"
            }
        })

    # 6. Differentiator 2: Substantive Lexical Density & Anti-Filler Engine (Appendix F)
    filler_eval = evaluate_lexical_density(html)
    if filler_eval.get("flagged"):
        findings.append({
            "id": "F-ENGAGE-009",
            "title": "AI Summarizer Dropout Zone: High filler-to-fact ratio obscures core propositions (Appendix F)",
            "severity": "medium",
            "evidence": filler_eval.get("evidence"),
            "suggested_action": {
                "summary": "Front-load verifiable technical specifications and quantified performance benchmarks in primary sentences, stripping generic marketing superlatives that cause AI summarizers to drop the content.",
                "priority": "medium"
            }
        })

    return findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    bundle = fetch_target_bundle(target)
    findings = audit_engagement(bundle)
    print(json.dumps({"skill": "engagement-audit", "target": target, "findings": findings}, indent=2))
