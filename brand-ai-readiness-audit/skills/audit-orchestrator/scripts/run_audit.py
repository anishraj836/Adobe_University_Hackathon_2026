#!/usr/bin/env python3
"""
Audit Orchestrator — Designated Marketplace Entrypoint
Coordinates sub-skills, shields against cascading errors, synthesizes evidence-conditioned proactive opportunities,
enforces Handout Page 2 schema, and outputs clean machine-readable JSON.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from urllib.parse import urlparse

# Ensure local script directory and sub-skill directories are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))

sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, os.path.join(SKILLS_DIR, "crawl-render-audit/scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "freshness-corroboration/scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "engagement-audit/scripts"))

from http_fetcher import fetch_target_bundle
from audit_crawl import audit_crawl
from audit_freshness import audit_freshness
from audit_engagement import audit_engagement
from proactive_engine import generate_proactive_actions
from schema_validator import validate_report_schema

def synthesize_executive_narrative(summary: dict, findings: list) -> str:
    """Generate a high-signal 1-2 sentence plain-English strategic synthesis for non-technical executives."""
    crit = summary.get("critical", 0)
    high = summary.get("high", 0)
    total = summary.get("total_findings", 0)

    if total == 0:
        return "This website exhibits exceptional AI readiness across both off-site discoverability (open crawler access, rich Schema.org markup, verifiable entity corroboration) and on-site visitor conversion pathways."

    titles_lower = " ".join([f.get("title", "").lower() for f in findings])
    has_crawl_barrier = any(kw in titles_lower for kw in ["robots.txt", "crawler", "cloaking", "client-side rendering", "unreachable"])
    has_schema_gap = any(kw in titles_lower for kw in ["schema.org", "json-ld", "entity", "temporal", "freshness"])
    has_conversion_gap = any(kw in titles_lower for kw in ["cta", "conversion", "friction", "trust", "navigation", "orientation"])

    narrative_parts = []
    if crit > 0:
        if has_crawl_barrier:
            narrative_parts.append("This site suffers from severe architectural barriers (e.g. AI crawler restrictions or unrendered client-side mounts) that render its primary content invisible to real-time conversational search engines.")
        else:
            narrative_parts.append("This site suffers from critical discoverability defects that prevent conversational AI agents from reliably extracting core brand facts.")
    elif high > 0:
        if has_schema_gap:
            narrative_parts.append("While accessible to crawlers, this site lacks essential semantic data structures (Schema.org markup, entity corroboration, or explicit freshness signals) required for reliable citation in AI answers.")
        else:
            narrative_parts.append("This site is discoverable by AI indexers, but exhibits significant structural and content fidelity gaps that diminish AI citation confidence.")
    else:
        narrative_parts.append("This site maintains solid baseline accessibility and markup, but possesses moderate optimization gaps in visitor orientation, heading hierarchy, or conversion routing for AI-referred traffic.")

    if has_conversion_gap and (crit > 0 or high > 0):
        narrative_parts.append("Additionally, arriving AI referrals face on-site friction in post-click orientation or conversion routing, increasing bounce rates.")

    return " ".join(narrative_parts)

def build_markdown_report(report: dict) -> str:
    """Format audit report into clean, executive-ready markdown."""
    site = report.get("site", "unknown")
    audited_at = report.get("audited_at", "")
    summary = report.get("summary", {})
    findings = report.get("findings", [])

    md = []
    md.append(f"# Brand AI-Readiness Audit Report: `{site}`")
    md.append(f"**Audited At:** {audited_at}\n")
    md.append("## Executive Summary")
    md.append(f"> {synthesize_executive_narrative(summary, findings)}\n")
    md.append(f"- **Total Findings:** {summary.get('total_findings', 0)}")
    md.append(f"- **Critical:** {summary.get('critical', 0)}")
    md.append(f"- **High:** {summary.get('high', 0)}")
    md.append(f"- **Medium:** {summary.get('medium', 0)}\n")

    md.append("## Detailed Findings & Prioritized Actions\n")
    for f in findings:
        sev = f.get("severity", "medium").upper()
        md.append(f"### [{sev}] {f.get('id')}: {f.get('title')}")
        md.append(f"**Evidence:** {f.get('evidence')}")
        action = f.get("suggested_action", {})
        md.append(f"**Suggested Action (Priority: {action.get('priority', 'medium').upper()}):** {action.get('summary')}\n")

    return "\n".join(md)

def run_audit(target: str, explain: bool = False) -> dict:
    """Execute end-to-end brand AI-readiness audit."""
    sys.stderr.write(f"[*] Initiating Brand AI-Readiness Audit for: {target}\n")

    # 1. Fetch site bundle
    bundle = fetch_target_bundle(target)
    sys.stderr.write(f"[*] Fetched target bundle (Status: {bundle.get('status')})\n")

    # 2. Extract normalized site name
    if bundle.get("is_local"):
        site_name = os.path.basename(target.replace("file://", "").rstrip("/")) or "local-fixture"
    else:
        parsed = urlparse(bundle.get("url", target))
        site_name = parsed.netloc or parsed.path or target

    raw_findings = []

    # 3. Step 1: Crawl & Render Audit
    crawl_findings = audit_crawl(bundle)
    raw_findings.extend(crawl_findings)
    if explain:
        sys.stderr.write(f"[explain] Crawl & render audit: {len(crawl_findings)} finding(s) detected.\n")

    # 4. Causal Error Shielding
    # If the site is completely unreachable or blocked at network layer, suppress downstream false positives
    is_blocked = any(f.get("id") == "F-CRAWL-001" for f in crawl_findings)
    if not is_blocked:
        # Step 2: Freshness & Corroboration Audit
        fresh_findings = audit_freshness(bundle)
        raw_findings.extend(fresh_findings)
        if explain:
            sys.stderr.write(f"[explain] Freshness & corroboration audit: {len(fresh_findings)} finding(s) detected.\n")

        # Step 3: Engagement & Friction Audit
        engage_findings = audit_engagement(bundle)
        raw_findings.extend(engage_findings)
        if explain:
            sys.stderr.write(f"[explain] Engagement & user journey audit: {len(engage_findings)} finding(s) detected.\n")

        # Step 4: Conditioned Proactive Opportunities Engine
        existing_ids = {f.get("id") for f in raw_findings}
        proactive_findings = generate_proactive_actions(bundle, existing_ids)
        raw_findings.extend(proactive_findings)
        if explain:
            sys.stderr.write(f"[explain] Turnkey proactive actions: {len(proactive_findings)} drop-in code fix(es) synthesized.\n")
    else:
        sys.stderr.write("[!] Target is unreachable/blocked; activating causal error shielding.\n")
        if explain:
            sys.stderr.write("[explain] Causal shielding: suppressed downstream freshness and engagement checks to eliminate cascade false positives.\n")

    # 5. Deduplicate overlapping cross-skill root causes (e.g. thin content double-counting)
    # F-ENGAGE-006 (substantive body prose, high severity) supersedes F-CRAWL-007 (raw HTML text volume)
    if any(f.get("id") == "F-ENGAGE-006" for f in raw_findings):
        raw_findings = [f for f in raw_findings if f.get("id") != "F-CRAWL-007"]

    # 6. Format and re-index findings strictly adhering to Handout Page 2 sample
    ordered_findings = []
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    raw_findings.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 9))

    severity_counts = {"critical": 0, "high": 0, "medium": 0}

    for idx, f in enumerate(raw_findings, start=1):
        raw_sev = f.get("severity", "medium").lower()
        sev = raw_sev if raw_sev in {"critical", "high", "medium", "low"} else "medium"
        # Preserve 'low' on finding object; map to 'medium' in summary tally to guarantee
        # Handout floor contract (total_findings == critical + high + medium)
        tally_sev = "medium" if sev == "low" else sev
        severity_counts[tally_sev] += 1

        ordered_findings.append({
            "id": f"F-{idx:03d}",
            "title": f.get("title", "Untitled Finding"),
            "severity": sev,
            "evidence": f.get("evidence", "Observed during automated site audit."),
            "suggested_action": {
                "summary": f.get("suggested_action", {}).get("summary", "Review and remediate."),
                "priority": f.get("suggested_action", {}).get("priority", sev).lower()
            }
        })

    # 6. Build final report strictly matching Handout Page 2 schema floor
    audited_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "site": site_name,
        "audited_at": audited_at,
        "summary": {
            "total_findings": len(ordered_findings),
            "critical": severity_counts["critical"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"]
        },
        "findings": ordered_findings
    }

    # 7. Strict Schema Validation
    valid, errors = validate_report_schema(report)
    if not valid:
        sys.stderr.write(f"[!] Schema validation failed: {errors}\n")
    else:
        sys.stderr.write(f"[*] Schema validation PASSED with {len(ordered_findings)} findings.\n")

    return report

def main():
    parser = argparse.ArgumentParser(description="Brand AI-Readiness Audit Entrypoint")
    parser.add_argument("target", nargs="?", default=None, help="Target URL, domain, or local fixture path")
    parser.add_argument("--url", dest="url", default=None, help="Target website URL")
    parser.add_argument("--fixture", dest="fixture", default=None, help="Path to local fixture directory or file")
    parser.add_argument("--format", dest="format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    parser.add_argument("--output", dest="output", default=None, help="Write output to file instead of stdout")
    parser.add_argument("--explain", "--verbose", dest="explain", action="store_true", help="Print detailed diagnostic decisions and scope-gate telemetry to stderr")

    args = parser.parse_args()
    target = args.fixture or args.url or args.target

    if not target:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    report = run_audit(target, explain=args.explain)

    if args.format == "markdown":
        output_str = build_markdown_report(report)
    else:
        output_str = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        sys.stderr.write(f"[*] Report saved to {args.output}\n")
    else:
        # Emit clean JSON to stdout
        sys.stdout.write(output_str + "\n")

if __name__ == "__main__":
    main()
