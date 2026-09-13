#!/usr/bin/env python3
"""
Dedicated Schema.org Structured Data Evaluator.
Evaluates structured data across homepage and discovered subpages,
producing quantified multi-page evidence matching Handout Page 2 specifications.
"""

import json
import re

def _flatten_jsonld(node) -> list:
    """Recursively unwrap JSON-LD items, lists, and @graph containers."""
    flat = []
    if isinstance(node, list):
        for item in node:
            flat.extend(_flatten_jsonld(item))
    elif isinstance(node, dict):
        flat.append(node)
        if "@graph" in node:
            flat.extend(_flatten_jsonld(node["@graph"]))
    return flat

def extract_jsonld_blocks(html: str) -> tuple[list, list]:
    """Extract and parse all JSON-LD script blocks, unwrapping @graph containers. Returns (valid_blocks, parse_errors)."""
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
            blocks.extend(_flatten_jsonld(data))
        except json.JSONDecodeError as e:
            errors.append(f"Block {idx+1}: {str(e)[:100]}")
    return blocks, errors

def evaluate_schema(html: str, subpages: list = None) -> tuple[list, list, list]:
    """
    Evaluate Schema.org markup across homepage and any discovered subpages.
    Returns (findings, root_jsonld_blocks, types_found).
    """
    findings = []
    all_pages = [{"path": "/", "html": html}]
    if subpages:
        for sp in subpages:
            if sp.get("html") and sp.get("status", 200) == 200:
                all_pages.append({"path": sp.get("path", "/subpage"), "html": sp.get("html", "")})

    total_pages = len(all_pages)
    pages_with_schema = 0
    all_blocks = []
    parse_errors = []
    types_found = []

    for idx, page in enumerate(all_pages):
        blocks, errors = extract_jsonld_blocks(page["html"])
        if blocks:
            pages_with_schema += 1
            all_blocks.extend(blocks)
            for b in blocks:
                if isinstance(b, dict):
                    b_type = b.get("@type", "")
                    if isinstance(b_type, list):
                        types_found.extend(b_type)
                    elif b_type:
                        types_found.append(b_type)
        if errors:
            parse_errors.extend([f"[{page['path']}] {err}" for err in errors])

    root_blocks, root_errors = extract_jsonld_blocks(html)

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

    # Quantified multi-page evidence matching Handout Page 2 sample
    paths_display = ", ".join([p["path"] for p in all_pages[:4]])
    if pages_with_schema == 0 and not parse_errors:
        findings.append({
            "id": "F-FRESH-002",
            "title": "Missing Schema.org structured data across crawled pages",
            "severity": "high",
            "evidence": f"Crawled {total_pages} page(s) ({paths_display}); {pages_with_schema}/{total_pages} contain schema.org markup.",
            "suggested_action": {
                "summary": "Implement Schema.org JSON-LD markup (Organization, WebSite, and Product/Service) so AI engines can reliably extract entity attributes.",
                "priority": "high"
            }
        })
    elif pages_with_schema < total_pages:
        missing_count = total_pages - pages_with_schema
        findings.append({
            "id": "F-FRESH-002",
            "title": "Incomplete Schema.org structured data coverage across site routes",
            "severity": "medium",
            "evidence": f"Crawled {total_pages} page(s) ({paths_display}); {missing_count}/{total_pages} lack schema.org structured data.",
            "suggested_action": {
                "summary": "Extend Schema.org JSON-LD markup across all key subpages so AI crawlers extract structured product and service offerings.",
                "priority": "medium"
            }
        })

    if all_blocks:
        core_types = {"Organization", "WebSite", "Corporation", "LocalBusiness"}
        if not any(t in core_types for t in types_found):
            findings.append({
                "id": "F-FRESH-003",
                "title": "Missing Organization or WebSite entity schema",
                "severity": "medium",
                "evidence": f"Found schemas ({', '.join(set(types_found)) or 'None'}), but missing root Organization or WebSite definition.",
                "suggested_action": {
                    "summary": "Add Schema.org Organization markup defining official brand name, logo, description, and contact info.",
                    "priority": "medium"
                }
            })

        # Qualitative Schema Completeness Checks (Type-Specific Structural Validation)
        for b in all_blocks:
            if not isinstance(b, dict):
                continue
            b_type = b.get("@type", "")
            type_str = b_type if isinstance(b_type, str) else str(b_type)

            # 1. Product Schema Completeness
            if "Product" in type_str:
                offers = b.get("offers")
                desc = b.get("description")
                has_valid_offer = isinstance(offers, dict) and bool(offers.get("price") or offers.get("priceCurrency") or offers.get("availability"))
                has_offer_list = isinstance(offers, list) and len(offers) > 0
                if not (has_valid_offer or has_offer_list or desc):
                    findings.append({
                        "id": "F-FRESH-010",
                        "title": "Incomplete Product schema: Missing pricing, offers, or description",
                        "severity": "medium",
                        "evidence": "Declared Schema.org Product markup lacks 'offers' (price/availability) and 'description' attributes required by AI shopping and comparison assistants.",
                        "suggested_action": {
                            "summary": "Populate Schema.org Product with 'offers' containing price, priceCurrency, and availability so conversational AI can quote real-time pricing.",
                            "priority": "medium"
                        }
                    })
                    break

            # 2. FAQPage Schema Completeness
            if "FAQPage" in type_str:
                main_entity = b.get("mainEntity")
                has_valid_qa = False
                if isinstance(main_entity, list) and len(main_entity) > 0:
                    has_valid_qa = any(
                        isinstance(q, dict) and q.get("acceptedAnswer")
                        for q in main_entity
                    )
                if not has_valid_qa:
                    findings.append({
                        "id": "F-FRESH-011",
                        "title": "Incomplete FAQPage schema: Missing structured Question/Answer pairs",
                        "severity": "medium",
                        "evidence": "Declared Schema.org FAQPage markup contains empty or invalid mainEntity list lacking structured Question and acceptedAnswer nodes.",
                        "suggested_action": {
                            "summary": "Ensure FAQPage mainEntity contains structured Question objects with nested acceptedAnswer Answer text.",
                            "priority": "medium"
                        }
                    })
                    break

            # 3. Article / Editorial Schema Completeness (E-E-A-T Author Signal)
            if any(t in type_str for t in ["Article", "BlogPosting", "NewsArticle"]):
                author = b.get("author")
                has_author = bool(author) and (isinstance(author, (dict, list, str)) and len(str(author).strip()) > 0)
                if not has_author:
                    findings.append({
                        "id": "F-FRESH-012",
                        "title": "Article schema missing author entity attribution (E-E-A-T trust signal)",
                        "severity": "medium",
                        "evidence": f"Declared Schema.org {type_str} lacks an explicit 'author' entity node. AI retrieval engines penalize uncredited editorial content.",
                        "suggested_action": {
                            "summary": "Attach an explicit Schema.org Person or Organization author attribute to editorial articles to establish E-E-A-T authority.",
                            "priority": "medium"
                        }
                    })
                    break

    return findings, all_blocks, types_found
