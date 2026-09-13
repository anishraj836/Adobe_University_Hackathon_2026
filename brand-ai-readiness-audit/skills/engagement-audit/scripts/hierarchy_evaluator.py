#!/usr/bin/env python3
"""
Dedicated Heading Hierarchy & Citation Anchor Evaluator (Round 2 Appendix B).
Evaluates heading structure and subheading deep-link ID anchors for AI citation navigation.
"""

import re

def evaluate_hierarchy(html: str) -> list:
    """Evaluate heading hierarchy progression and citation anchor attributes."""
    findings = []

    # 1. Heading Sequence Progression (Skipped Heading Level Check)
    heading_tags = re.findall(r'<(h[1-6])\b[^>]*>(.*?)</\1>', html, re.I | re.DOTALL)
    if heading_tags:
        levels = [int(tag[1]) for tag, _ in heading_tags]
        skipped_levels = []
        for i in range(len(levels) - 1):
            curr, nxt = levels[i], levels[i+1]
            if nxt > curr + 1:
                skipped_levels.append(f"H{curr} -> H{nxt}")

        if skipped_levels:
            findings.append({
                "id": "F-ENGAGE-008",
                "title": "Disjointed heading hierarchy (skipped heading levels)",
                "severity": "medium",
                "evidence": f"Detected {len(skipped_levels)} skipped heading level transition(s) ({', '.join(skipped_levels[:3])}); breaks document outline extraction for conversational AI systems.",
                "suggested_action": {
                    "summary": "Structure content sequentially (H1 -> H2 -> H3) without skipping heading levels to preserve semantic document outlines.",
                    "priority": "medium"
                }
            })

    # 2. Subheading Citation Anchor IDs
    subheadings = re.findall(r'<h[2-4]\b([^>]*)>(.*?)<\/h[2-4]>', html, re.I | re.DOTALL)
    if subheadings:
        anchored_count = sum(1 for attrs, _ in subheadings if re.search(r'\bid=["\'][^"\']+["\']', attrs, re.I))
        pct_anchored = (anchored_count / len(subheadings)) * 100
        if pct_anchored < 25:
            findings.append({
                "id": "F-ENGAGE-005",
                "title": "Subheadings lack persistent citation anchor IDs",
                "severity": "medium",
                "evidence": f"Only {anchored_count}/{len(subheadings)} (H2-H4) subheadings possess HTML id attributes for fragment deep-linking.",
                "suggested_action": {
                    "summary": "Attach persistent semantic id attributes (e.g., id='features', id='pricing') to all H2/H3 headers so AI assistants can cite and deep-link directly to factual claims.",
                    "priority": "medium"
                }
            })
    return findings
