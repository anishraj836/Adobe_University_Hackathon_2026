#!/usr/bin/env python3
"""
Dedicated Entity Disambiguation & Knowledge Graph Resolver.
Evaluates sameAs links and on-site disambiguation posture (Round 2 Appendix D).
"""

import os
import sys
import json
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POLYSEMY_PATH = os.path.join(CURRENT_DIR, "../references/polysemy_dictionary.json")
HOMONYMS = set()
if os.path.exists(POLYSEMY_PATH):
    try:
        with open(POLYSEMY_PATH, "r", encoding="utf-8") as f:
            HOMONYMS = set(json.load(f).get("common_homonyms", []))
    except Exception:
        pass

AUTHORITATIVE_DOMAINS = [
    "wikidata.org", "wikipedia.org", "linkedin.com", "crunchbase.com",
    "github.com", "x.com", "twitter.com", "google.com/maps"
]

def evaluate_entity(html: str, jsonld_blocks: list) -> list:
    """Evaluate cross-web entity corroboration and polysemy ambiguity."""
    findings = []
    sameas_links = []

    for b in jsonld_blocks:
        if isinstance(b, dict):
            sameas = b.get("sameAs", [])
            if isinstance(sameas, str):
                sameas_links.append(sameas)
            elif isinstance(sameas, list):
                sameas_links.extend([s for s in sameas if isinstance(s, str)])

    authoritative_mentions = []
    for link in sameas_links:
        for auth in AUTHORITATIVE_DOMAINS:
            if auth in link.lower() and auth not in authoritative_mentions:
                authoritative_mentions.append(auth)

    dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    for href in dom_hrefs:
        for auth in AUTHORITATIVE_DOMAINS:
            if auth in href.lower() and auth not in authoritative_mentions:
                authoritative_mentions.append(auth)

    if not authoritative_mentions:
        findings.append({
            "id": "F-FRESH-004",
            "title": "Lacks cross-web entity corroboration (sameAs links)",
            "severity": "medium",
            "evidence": "No sameAs links to authoritative registries (Wikidata, LinkedIn, Crunchbase, GitHub) found in structured data or DOM.",
            "suggested_action": {
                "summary": "Anchor the brand identity by linking official profiles (LinkedIn, Crunchbase, Wikidata, GitHub) inside schema sameAs properties.",
                "priority": "medium"
            }
        })

    # Polysemy / Homonym Ambiguity Check
    title_match = re.search(r'<title\b[^>]*>(.*?)<\/title>', html, re.I)
    title_text = title_match.group(1).strip() if title_match else ""
    first_word = title_text.split()[0].lower() if title_text else ""
    clean_brand = re.sub(r'[^a-zA-Z]', '', first_word)

    if clean_brand in HOMONYMS:
        has_disambiguation = False
        for b in jsonld_blocks:
            if isinstance(b, dict):
                if b.get("legalName") or b.get("disambiguatingDescription"):
                    has_disambiguation = True
                    break
                b_type = str(b.get("@type", ""))
                if b_type not in ("", "Thing", "WebPage") and len(authoritative_mentions) >= 2:
                    has_disambiguation = True
                    break
        if not has_disambiguation:
            findings.append({
                "id": "F-FRESH-008",
                "title": "High LLM Hallucination Risk: Generic brand identifier lacks on-site entity disambiguation (Appendix D)",
                "severity": "medium",
                "evidence": f"Brand identifier '{clean_brand.capitalize()}' carries high semantic polysemy in LLM parametric memory. Lacks Schema.org legalName, disambiguatingDescription, and multi-registry sameAs anchors. High risk of mistaken identity per Appendix D.",
                "suggested_action": {
                    "summary": "Inject Schema.org legalName, specialized @type, and disambiguatingDescription alongside verified sameAs registry links to resolve brand ambiguity in LLM parametric memory.",
                    "priority": "medium"
                }
            })

    return findings
