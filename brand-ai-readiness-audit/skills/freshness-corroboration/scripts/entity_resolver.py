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

def _unwrap_blocks(blocks: list) -> list:
    """Recursively unwrap JSON-LD items and nested @graph containers."""
    flat = []
    for b in blocks:
        if isinstance(b, list):
            flat.extend(_unwrap_blocks(b))
        elif isinstance(b, dict):
            flat.append(b)
            if "@graph" in b and isinstance(b["@graph"], list):
                flat.extend(_unwrap_blocks(b["@graph"]))
    return flat

def evaluate_entity(html: str, jsonld_blocks: list) -> list:
    """Evaluate cross-web entity corroboration and polysemy ambiguity."""
    findings = []
    sameas_links = []
    jsonld_blocks = _unwrap_blocks(jsonld_blocks)

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
            "evidence": "Audited on-site knowledge graph bridge posture (offline sandbox boundary: external registries such as Wikidata/Crunchbase are not queried live). Found 0 sameAs outbound links or authoritative entity anchors (Wikidata, LinkedIn, Crunchbase, GitHub) in structured data or DOM markup.",
            "suggested_action": {
                "summary": "Anchor the brand identity by linking official profiles (LinkedIn, Crunchbase, Wikidata, GitHub) inside schema sameAs properties.",
                "priority": "medium"
            }
        })

    # Polysemy / Homonym Ambiguity Check
    DISAMBIGUATION_TYPES = {"Organization", "Corporation", "LocalBusiness", "Brand", "SoftwareApplication"}
    clean_brand = None

    # 1. Check JSON-LD Organization / Brand names
    for b in jsonld_blocks:
        if isinstance(b, dict):
            org_name = str(b.get("name", "")).strip()
            if org_name:
                for word in re.findall(r'\b[a-zA-Z]+\b', org_name):
                    if word.lower() in HOMONYMS:
                        clean_brand = word.lower()
                        break
        if clean_brand:
            break

    # 2. Split <title> across delimiters (| - — :)
    if not clean_brand:
        title_match = re.search(r'<title\b[^>]*>(.*?)<\/title>', html, re.I)
        if title_match:
            title_text = title_match.group(1).strip()
            segments = re.split(r'[|\-—:]', title_text)
            for seg in segments:
                for word in re.findall(r'\b[a-zA-Z]+\b', seg):
                    if word.lower() in HOMONYMS:
                        clean_brand = word.lower()
                        break
                if clean_brand:
                    break

    if clean_brand and clean_brand in HOMONYMS:
        has_disambiguation = False
        for b in jsonld_blocks:
            if isinstance(b, dict):
                if b.get("legalName") or b.get("disambiguatingDescription"):
                    has_disambiguation = True
                    break
                b_type = str(b.get("@type", ""))
                if b_type in DISAMBIGUATION_TYPES and len(authoritative_mentions) >= 2:
                    has_disambiguation = True
                    break
        if not has_disambiguation:
            findings.append({
                "id": "F-FRESH-008",
                "title": "High LLM Hallucination Risk: Generic brand identifier lacks on-site entity disambiguation (Appendix D)",
                "severity": "medium",
                "evidence": f"Audited on-site knowledge graph bridge posture under offline sandbox constraints. Brand identifier '{clean_brand.capitalize()}' carries high semantic polysemy in LLM parametric memory, yet page lacks Schema.org legalName, disambiguatingDescription, and multi-registry sameAs anchors. High risk of mistaken identity per Appendix D.",
                "suggested_action": {
                    "summary": "Inject Schema.org legalName, specialized @type, and disambiguatingDescription alongside verified sameAs registry links to resolve brand ambiguity in LLM parametric memory.",
                    "priority": "medium"
                }
            })

    return findings
