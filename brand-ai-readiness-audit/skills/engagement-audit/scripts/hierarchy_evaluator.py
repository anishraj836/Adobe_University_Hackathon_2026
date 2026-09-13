#!/usr/bin/env python3
"""
Dedicated Heading Hierarchy & Citation Anchor Evaluator (Round 2 Appendix B).
Evaluates heading structure and subheading deep-link ID anchors for AI citation navigation.
"""

import re

def evaluate_hierarchy(html: str) -> list:
    """Evaluate heading hierarchy and citation anchor attributes."""
    findings = []
    subheadings = re.findall(r'<h[2-4]\b([^>]*)>(.*?)<\/h[2-4]>', html, re.I | re.DOTALL)
    if subheadings:
        anchored_count = sum(1 for attrs, _ in subheadings if re.search(r'\bid=["\'][^"\']+["\']', attrs, re.I))
        pct_anchored = (anchored_count / len(subheadings)) * 100
        if pct_anchored < 25:
            findings.append({
                "id": "F-ENGAGE-005",
                "title": "Subheadings lack persistent citation anchor IDs",
                "severity": "medium",
                "evidence": f"[Confidence: 92%] Only {anchored_count}/{len(subheadings)} (H2-H4) subheadings possess HTML id attributes for fragment deep-linking.",
                "suggested_action": {
                    "summary": "Attach persistent semantic id attributes (e.g., id='features', id='pricing') to all H2/H3 headers so AI assistants can cite and deep-link directly to factual claims.",
                    "priority": "medium"
                }
            })
    return findings
