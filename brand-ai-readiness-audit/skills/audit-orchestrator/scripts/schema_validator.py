#!/usr/bin/env python3
"""
Strict Schema Validator for Handout Page 2 Audit Report Compliance.
Enforces that summary contains total_findings, critical, high, medium (the Handout floor).
"""

import re

FINDING_SEVERITY_VALUES = {"critical", "high", "medium", "low"}
SUMMARY_FLOOR_SEVERITIES = {"critical", "high", "medium"}

def validate_report_schema(report: dict) -> tuple[bool, list[str]]:
    """
    Validate audit report dictionary against exact Adobe Handout Page 2 requirements.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # 1. Top-level keys: exact Handout Page 2 floor (required floor keys must exist)
    required_top_keys = ["site", "audited_at", "summary", "findings"]
    for req in required_top_keys:
        if req not in report:
            errors.append(f"Missing required top-level key: '{req}'")

    if errors:
        return False, errors

    # 2. Field types
    if not isinstance(report["site"], str) or not report["site"].strip():
        errors.append("Field 'site' must be a non-empty string.")

    if not isinstance(report["audited_at"], str):
        errors.append("Field 'audited_at' must be an ISO-8601 string.")
    else:
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', report["audited_at"]):
            errors.append(f"Field 'audited_at' has invalid ISO-8601 format: {report['audited_at']}")

    # 3. Summary object: Required Handout Page 2 floor keys must exist
    summary = report["summary"]
    if not isinstance(summary, dict):
        errors.append("Field 'summary' must be an object/dict.")
    else:
        for req in ["total_findings", "critical", "high", "medium"]:
            if req not in summary:
                errors.append(f"Summary missing required key: '{req}'")
            elif not isinstance(summary[req], int) or summary[req] < 0:
                errors.append(f"Summary key '{req}' must be a non-negative integer.")

    # 4. Findings array
    findings = report["findings"]
    if not isinstance(findings, list):
        errors.append("Field 'findings' must be an array/list.")
    else:
        total = summary.get("total_findings", 0)
        if total != len(findings):
            errors.append(f"Summary total_findings ({total}) does not match findings length ({len(findings)}).")

        severity_counts = {"critical": 0, "high": 0, "medium": 0}

        for idx, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(f"Finding [{idx}] must be a dict.")
                continue

            for f_key in ["id", "title", "severity", "evidence", "suggested_action"]:
                if f_key not in finding:
                    errors.append(f"Finding [{idx}] missing required key: '{f_key}'")

            sev = finding.get("severity")
            if sev not in FINDING_SEVERITY_VALUES:
                errors.append(f"Finding [{idx}] has invalid severity '{sev}'; must be one of {FINDING_SEVERITY_VALUES}")
            else:
                # Per Handout Page 2 summary floor: fold low into medium for summary tally
                tally_sev = "medium" if sev == "low" else sev
                severity_counts[tally_sev] += 1

            action = finding.get("suggested_action")
            if not isinstance(action, dict):
                errors.append(f"Finding [{idx}] suggested_action must be a dict.")
            else:
                for a_key in ["summary", "priority"]:
                    if a_key not in action:
                        errors.append(f"Finding [{idx}] suggested_action missing required key: '{a_key}'")
                prio = action.get("priority")
                if prio not in FINDING_SEVERITY_VALUES:
                    errors.append(f"Finding [{idx}] suggested_action priority '{prio}' invalid.")

        # Check category counts
        for sev in ["critical", "high", "medium"]:
            if summary.get(sev, 0) != severity_counts[sev]:
                errors.append(f"Summary {sev} count ({summary.get(sev)}) does not match finding tally ({severity_counts[sev]}).")

    return len(errors) == 0, errors

if __name__ == "__main__":
    sample = {
        "site": "example.com",
        "audited_at": "2026-09-20T14:32:00Z",
        "summary": {"total_findings": 6, "critical": 1, "high": 2, "medium": 3},
        "findings": [
            {
                "id": "F-001",
                "title": "No JSON-LD structured data on product pages",
                "severity": "high",
                "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
                "suggested_action": {"summary": "Add Product/Offer JSON-LD to every product page.", "priority": "high"}
            }
        ]
    }
    # Note: total_findings mismatch is expected for dummy sample since 6 != 1
    valid, errs = validate_report_schema(sample)
    print("Self-test check:", errs)
