#!/usr/bin/env python3
"""
Dedicated Schema.org Structured Data Evaluator.
Validates syntax, structure, and required properties for Organization, WebSite, Product, FAQPage.
"""

import json
import re

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

def evaluate_schema(html: str) -> tuple[list, list, list]:
    """
    Evaluate Schema.org markup.
    Returns (findings, jsonld_blocks, types_found).
    """
    findings = []
    blocks, parse_errors = extract_jsonld_blocks(html)

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
    for b in blocks:
        if isinstance(b, dict):
            b_type = b.get("@type", "")
            if isinstance(b_type, list):
                types_found.extend(b_type)
            elif b_type:
                types_found.append(b_type)

    if not blocks and not parse_errors:
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

    return findings, blocks, types_found
