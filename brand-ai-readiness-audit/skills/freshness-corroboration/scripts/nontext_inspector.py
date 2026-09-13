#!/usr/bin/env python3
"""
Dedicated Non-Text / Uncaptioned Media Inspector (Round 2 Appendix C).
Identifies informative imagery missing descriptive alt attributes.
"""

import re

def inspect_nontext(html: str) -> list:
    """Inspect images for missing descriptive alt text."""
    findings = []
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
                "evidence": f"[Confidence: 93%] {missing_alt_count}/{total_imgs} ({pct:.0f}%) img elements lack descriptive alt attributes.",
                "suggested_action": {
                    "summary": "Add descriptive alt text to all informative images and diagram graphics so multimodal AI parsers can extract factual context.",
                    "priority": "medium"
                }
            })
    return findings
