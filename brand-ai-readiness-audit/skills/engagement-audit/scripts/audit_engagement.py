#!/usr/bin/env python3
"""
Engagement & Friction Audit Skill — Composed Orchestration
Coordinates orientation_evaluator, hierarchy_evaluator, quotability_evaluator, and filler_evaluator.
"""

import os
import sys
import json
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

CRAWL_SCRIPTS = os.path.abspath(os.path.join(CURRENT_DIR, "../../crawl-render-audit/scripts"))
if CRAWL_SCRIPTS not in sys.path:
    sys.path.insert(0, CRAWL_SCRIPTS)

from http_fetcher import fetch_target_bundle
from audit_crawl import count_words
from orientation_evaluator import evaluate_orientation
from hierarchy_evaluator import evaluate_hierarchy
from quotability_evaluator import evaluate_quotability
from filler_evaluator import evaluate_filler, strip_chrome
from conversion_evaluator import evaluate_conversion

TRUST_KEYWORDS = ["privacy", "terms", "contact", "about", "security", "legal"]

def audit_engagement(bundle: dict) -> list:
    """Audit visitor orientation, referral retention, heading hierarchy, RAG quotability, and lexical density."""
    findings = []
    html = bundle.get("html", "")
    home_status = bundle.get("status", 200)

    if home_status == 0 or home_status >= 400:
        return []

    # 1. 5-Second Cognitive Orientation & Mobile Viewport
    orientation_findings, brand_hint = evaluate_orientation(html)
    findings.extend(orientation_findings)

    # 2. Heading Hierarchy & Citation Anchor Deep-Linking (Appendix B)
    hierarchy_findings = evaluate_hierarchy(html)
    findings.extend(hierarchy_findings)

    # 3. Substantive Content Density vs Boilerplate
    substantive_text = strip_chrome(html)
    substantive_words = count_words(substantive_text)

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

    # 5. Differentiator 1: Fact Quotability & Entity Binding (Round 2 Appendix B & C)
    quotability_eval = evaluate_quotability(html, brand_hint)
    if quotability_eval.get("flagged"):
        findings.append({
            "id": "F-ENGAGE-015",
            "title": "High RAG retrieval failure risk: Substantive facts lack self-contained entity binding",
            "severity": "medium",
            "evidence": quotability_eval.get("evidence"),
            "suggested_action": {
                "summary": "Refactor fragmented body copy into self-contained Subject-Predicate-Object propositions. Replace anaphoric pronouns with explicit brand/feature names in key declarations so neural RAG retrievers can extract isolated passages without context loss.",
                "priority": "medium"
            }
        })

    # 6. Differentiator 2: Fact-to-Filler Ratio & Summarizer Dropout Risk (Round 2 Appendix F)
    filler_eval = evaluate_filler(html)
    if filler_eval.get("flagged"):
        findings.append({
            "id": "F-ENGAGE-016",
            "title": "AI Summarizer Dropout Zone: High filler-to-fact ratio obscures core propositions (Appendix F)",
            "severity": "medium",
            "evidence": filler_eval.get("evidence"),
            "suggested_action": {
                "summary": "Front-load verifiable technical specifications and quantified performance benchmarks in primary sentences, stripping generic marketing superlatives that cause AI summarizers to drop the content.",
                "priority": "medium"
            }
        })

    # 7. User Journey & Conversion Friction Evaluation
    conversion_findings = evaluate_conversion(html)
    findings.extend(conversion_findings)

    # 8. Broken Internal Route Check (Dead-End AI Referral Risk)
    is_local = bundle.get("is_local", False)
    dead_subpages = [sp for sp in bundle.get("subpages", []) if sp.get("status") in (404, 500)]
    if not is_local and dead_subpages:
        paths = [sp.get("path") for sp in dead_subpages]
        findings.append({
            "id": "F-ENGAGE-017",
            "title": "High-priority internal navigation link returned HTTP error dead end",
            "severity": "medium",
            "evidence": f"Followed prioritized navigation routes from homepage; {len(dead_subpages)} link(s) returned HTTP error: {', '.join(paths)}.",
            "suggested_action": {
                "summary": "Fix broken internal links or deploy proper 301 redirects to avoid dead ends for AI crawlers and referred users.",
                "priority": "medium"
            }
        })

    return findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    bundle = fetch_target_bundle(target)
    findings = audit_engagement(bundle)
    print(json.dumps({"skill": "engagement-audit", "target": target, "findings": findings}, indent=2))
