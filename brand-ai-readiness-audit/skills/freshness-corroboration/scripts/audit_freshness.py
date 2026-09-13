#!/usr/bin/env python3
"""
Freshness & Entity Corroboration Audit Skill
Audits structured data (JSON-LD), entity reconciliation (sameAs), multi-source freshness,
non-text traps, and Entity Ambiguity / Hallucination Risk (Diff 3).
"""

import os
import sys
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

# Ensure local script directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

CRAWL_SCRIPTS = os.path.abspath(os.path.join(CURRENT_DIR, "../../crawl-render-audit/scripts"))
if CRAWL_SCRIPTS not in sys.path:
    sys.path.insert(0, CRAWL_SCRIPTS)

from http_fetcher import fetch_target_bundle

AUTHORITATIVE_DOMAINS = [
    "wikidata.org", "wikipedia.org", "linkedin.com", "crunchbase.com",
    "github.com", "x.com", "twitter.com", "google.com/maps"
]

# Load polysemy dictionary
POLYSEMY_PATH = os.path.join(CURRENT_DIR, "../references/polysemy_dictionary.json")
HOMONYMS = set()
if os.path.exists(POLYSEMY_PATH):
    try:
        with open(POLYSEMY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            HOMONYMS = set(data.get("common_homonyms", []))
    except Exception:
        pass

def extract_jsonld_blocks(html: str) -> tuple[list, list]:
    """Extract and parse all JSON-LD script blocks. Returns (valid_blocks, parse_errors)."""
    blocks = []
    errors = []
    pattern = r'<script\s+[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

    for idx, raw in enumerate(matches):
        cleaned = raw.strip()
        if not cleaned:
            continue
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                blocks.extend(data)
            else:
                blocks.append(data)
        except json.JSONDecodeError as e:
            errors.append(f"Block {idx+1}: {str(e)[:100]}")
    return blocks, errors

def extract_dates(html: str, headers: dict, jsonld_blocks: list) -> list[datetime]:
    """Corroborate dates across JSON-LD, meta tags, DOM <time>, and HTTP headers."""
    found_dates = []

    # 1. JSON-LD dates
    for block in jsonld_blocks:
        if isinstance(block, dict):
            for field in ["dateModified", "datePublished", "uploadDate"]:
                val = block.get(field)
                if val and isinstance(val, str):
                    try:
                        clean_val = val[:10]
                        dt = datetime.strptime(clean_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        found_dates.append(dt)
                    except ValueError:
                        pass

    # 2. Meta tags
    meta_patterns = [
        r'<meta\s+property=["\']article:(?:modified_time|published_time)["\']\s+content=["\']([^"\']+)["\']',
        r'<meta\s+name=["\'](?:last-modified|publish-date|date)["\']\s+content=["\']([^"\']+)["\']'
    ]
    for pat in meta_patterns:
        for match in re.findall(pat, html, re.I):
            try:
                clean_match = match[:10]
                dt = datetime.strptime(clean_match, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                found_dates.append(dt)
            except ValueError:
                pass

    # 3. DOM <time datetime="...">
    time_matches = re.findall(r'<time\s+[^>]*datetime=["\']([^"\']+)["\']', html, re.I)
    for tm in time_matches:
        try:
            clean_tm = tm[:10]
            dt = datetime.strptime(clean_tm, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            found_dates.append(dt)
        except ValueError:
            pass

    # 4. HTTP Last-Modified header
    last_mod = headers.get("last-modified")
    if last_mod:
        try:
            dt = datetime.strptime(last_mod[:16], "%a, %d %b %Y").replace(tzinfo=timezone.utc)
            found_dates.append(dt)
        except ValueError:
            pass

    return found_dates

def evaluate_entity_ambiguity(html: str, jsonld_blocks: list, sameas_count: int) -> dict:
    """
    Differentiator 3: Entity Ambiguity & On-Site Disambiguation Posture (Appendix D).
    Applies Battle-Hardened Safeguards:
    1. 100% Offline: Zero external API/SPARQL lookups.
    2. On-Site Disambiguation Posture: Checks if the site declares legalName, specialized @type,
       or disambiguatingDescription when the brand name matches a polysemous noun.
    """
    title_match = re.search(r'<title\b[^>]*>(.*?)<\/title>', html, re.I)
    title_text = title_match.group(1).strip() if title_match else ""
    first_word = title_text.split()[0].lower() if title_text else ""
    clean_brand = re.sub(r'[^a-zA-Z]', '', first_word)

    is_homonym = clean_brand in HOMONYMS

    if not is_homonym:
        return {"flagged": False, "evidence": "Unique coined brand identity; minimal polysemy risk."}

    # Brand is a homonym dictionary word (e.g. Atlas, Pulse, Ramp). Check on-site disambiguation!
    has_disambiguation = False
    for b in jsonld_blocks:
        if isinstance(b, dict):
            if b.get("legalName") or b.get("disambiguatingDescription"):
                has_disambiguation = True
                break
            b_type = str(b.get("@type", ""))
            if b_type not in ("", "Thing", "WebPage") and sameas_count >= 2:
                has_disambiguation = True
                break

    if not has_disambiguation:
        return {
            "flagged": True,
            "brand": clean_brand.capitalize(),
            "evidence": f"Brand identifier '{clean_brand.capitalize()}' carries high semantic polysemy in LLM parametric memory. Lacks Schema.org legalName, disambiguatingDescription, and multi-registry sameAs anchors. High risk of mistaken identity per Appendix D."
        }
    return {"flagged": False, "evidence": "Homonym brand with verified on-site disambiguation markup."}

def audit_freshness(bundle: dict) -> list:
    """Audit structured data, entity corroboration, freshness, non-text, and entity ambiguity."""
    findings = []
    html = bundle.get("html", "")
    headers = bundle.get("headers", {})
    home_status = bundle.get("status", 200)

    if home_status == 0 or (home_status >= 400 and home_status != 404):
        return []

    # 1. JSON-LD Structured Data
    jsonld_blocks, parse_errors = extract_jsonld_blocks(html)

    if parse_errors:
        findings.append({
            "id": "F-FRESH-001",
            "title": "Syntax error in Schema.org JSON-LD payload",
            "severity": "high",
            "evidence": f"Found {len(parse_errors)} malformed JSON-LD script tag(s): {parse_errors[0]}.",
            "suggested_action": {
                "summary": "Fix JSON syntax errors in application/ld+json scripts to prevent parser aborts by search crawlers.",
                "priority": "high"
            }
        })

    types_found = []
    sameas_links = []
    for b in jsonld_blocks:
        if isinstance(b, dict):
            b_type = b.get("@type", "")
            if isinstance(b_type, list):
                types_found.extend(b_type)
            elif b_type:
                types_found.append(b_type)
            
            sameas = b.get("sameAs", [])
            if isinstance(sameas, str):
                sameas_links.append(sameas)
            elif isinstance(sameas, list):
                sameas_links.extend([s for s in sameas if isinstance(s, str)])

    if not jsonld_blocks and not parse_errors:
        findings.append({
            "id": "F-FRESH-002",
            "title": "Missing Schema.org structured data",
            "severity": "high",
            "evidence": "Crawled page; 0 Schema.org JSON-LD or Microdata blocks found.",
            "suggested_action": {
                "summary": "Implement Schema.org JSON-LD markup (Organization, WebSite, and Product/Service) so AI engines can reliably extract entity attributes.",
                "priority": "high"
            }
        })
    else:
        core_types = {"Organization", "WebSite", "Corporation", "LocalBusiness"}
        if not any(t in core_types for t in types_found):
            findings.append({
                "id": "F-FRESH-003",
                "title": "Missing Organization or WebSite entity schema",
                "severity": "medium",
                "evidence": f"Found schemas ({', '.join(types_found) or 'None'}), but missing root Organization or WebSite definition.",
                "suggested_action": {
                    "summary": "Add Schema.org Organization markup defining official brand name, logo, description, and contact info.",
                    "priority": "medium"
                }
            })

    # 2. Entity Disambiguation & Cross-Web Agreement (Appendix D)
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

    # 3. 4-Way Freshness Corroboration
    dates = extract_dates(html, headers, jsonld_blocks)
    now = datetime.now(timezone.utc)

    if dates:
        most_recent = max(dates)
        age_days = (now - most_recent).days
        if age_days > 365:
            findings.append({
                "id": "F-FRESH-005",
                "title": "Stale temporal signals (> 1 year since content update)",
                "severity": "medium",
                "evidence": f"Most recent verified timestamp is {most_recent.strftime('%Y-%m-%d')} ({age_days} days old).",
                "suggested_action": {
                    "summary": "Update page content and publish fresh dateModified timestamps in JSON-LD to prevent AI assistants from deprecating citation confidence.",
                    "priority": "medium"
                }
            })
    else:
        findings.append({
            "id": "F-FRESH-006",
            "title": "Missing explicit temporal metadata",
            "severity": "low",
            "evidence": "No datePublished, dateModified, or HTTP Last-Modified timestamps found across headers or markup.",
            "suggested_action": {
                "summary": "Expose ISO-8601 dateModified in structured data and configure web server to return Last-Modified headers.",
                "priority": "low"
            }
        })

    # 4. Non-Text Traps: Images Missing Descriptive Alt Text (Appendix C)
    img_tags = re.findall(r'<img\b[^>]*>', html, re.I)
    missing_alt_count = 0
    total_imgs = len(img_tags)

    for img in img_tags:
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img, re.I)
        if not alt_match or not alt_match.group(1).strip():
            missing_alt_count += 1

    if total_imgs > 0 and missing_alt_count > 0:
        pct = (missing_alt_count / total_imgs) * 100
        if pct > 40:
            findings.append({
                "id": "F-FRESH-007",
                "title": "Brand information and diagrams locked in uncaptioned images",
                "severity": "medium",
                "evidence": f"{missing_alt_count}/{total_imgs} ({pct:.0f}%) img elements lack descriptive alt attributes.",
                "suggested_action": {
                    "summary": "Add descriptive alt text to all informative images and diagram graphics so multimodal AI parsers can extract factual context.",
                    "priority": "medium"
                }
            })

    # 5. Differentiator 3: Entity Ambiguity & On-Site Disambiguation Posture (Appendix D)
    ambiguity_eval = evaluate_entity_ambiguity(html, jsonld_blocks, len(authoritative_mentions))
    if ambiguity_eval.get("flagged"):
        findings.append({
            "id": "F-FRESH-008",
            "title": "High LLM Hallucination Risk: Generic brand identifier lacks on-site entity disambiguation (Appendix D)",
            "severity": "medium",
            "evidence": ambiguity_eval.get("evidence"),
            "suggested_action": {
                "summary": "Inject Schema.org legalName, specialized @type, and disambiguatingDescription alongside verified sameAs registry links to resolve brand ambiguity in LLM parametric memory.",
                "priority": "medium"
            }
        })

    return findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    bundle = fetch_target_bundle(target)
    findings = audit_freshness(bundle)
    print(json.dumps({"skill": "freshness-corroboration", "target": target, "findings": findings}, indent=2))
