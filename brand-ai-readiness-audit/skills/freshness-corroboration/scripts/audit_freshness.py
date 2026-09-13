#!/usr/bin/env python3
"""
Freshness & Entity Corroboration Audit Skill — Composed Orchestration
Coordinates schema_evaluator, entity_resolver, freshness_evaluator, and nontext_inspector
across homepage and crawled subpages.
"""

import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

CRAWL_SCRIPTS = os.path.abspath(os.path.join(CURRENT_DIR, "../../crawl-render-audit/scripts"))
if CRAWL_SCRIPTS not in sys.path:
    sys.path.insert(0, CRAWL_SCRIPTS)

from http_fetcher import fetch_target_bundle
from schema_evaluator import evaluate_schema
from entity_resolver import evaluate_entity
from freshness_evaluator import evaluate_freshness
from nontext_inspector import inspect_nontext

def audit_freshness(bundle: dict) -> list:
    """Execute all freshness, structured data, entity, and non-text checks."""
    findings = []
    html = bundle.get("html", "")
    headers = bundle.get("headers", {})
    subpages = bundle.get("subpages", [])
    home_status = bundle.get("status", 200)

    if home_status == 0 or (home_status >= 400 and home_status != 404):
        return []

    # 1. Multi-Page Schema.org Structured Data
    schema_findings, jsonld_blocks, types_found = evaluate_schema(html, subpages=subpages)
    findings.extend(schema_findings)

    # 2. Entity Disambiguation & Cross-Web Agreement (Appendix D)
    entity_findings = evaluate_entity(html, jsonld_blocks)
    findings.extend(entity_findings)

    # 3. 4-Way Freshness Corroboration
    freshness_findings = evaluate_freshness(html, headers, jsonld_blocks)
    findings.extend(freshness_findings)

    # 4. Non-Text Traps (Appendix C)
    nontext_findings = inspect_nontext(html)
    findings.extend(nontext_findings)

    return findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    bundle = fetch_target_bundle(target)
    findings = audit_freshness(bundle)
    print(json.dumps({"skill": "freshness-corroboration", "target": target, "findings": findings}, indent=2))
