#!/usr/bin/env python3
"""
Dedicated Non-Text / Uncaptioned Media Inspector (Round 2 Appendix C).
Identifies informative imagery missing descriptive alt attributes.
"""

import re

def inspect_nontext(html: str) -> list:
    """Inspect images for missing or placeholder alt text on informative media."""
    findings = []
    img_tags = re.findall(r'<img\b[^>]*>', html, re.I)
    missing_alt_count = 0
    informative_imgs = 0
    LOW_SIGNAL_ALTS = {"image", "photo", "img", "screenshot", "graphic", "untitled", "banner", "pic"}

    for img in img_tags:
        # Exclude explicitly decorative elements per WCAG guidelines
        if re.search(r'role=["\'](?:presentation|none)["\']', img, re.I) or re.search(r'aria-hidden=["\']true["\']', img, re.I):
            continue

        informative_imgs += 1
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img, re.I)
        if not alt_match:
            missing_alt_count += 1
        else:
            alt_text = alt_match.group(1).strip()
            if not alt_text or alt_text.lower() in LOW_SIGNAL_ALTS:
                missing_alt_count += 1

    if informative_imgs > 0 and missing_alt_count > 0:
        pct = (missing_alt_count / informative_imgs) * 100
        if pct > 40:
            findings.append({
                "id": "F-FRESH-009",
                "title": "Brand information and diagrams locked in uncaptioned images",
                "severity": "medium",
                "evidence": f"{missing_alt_count}/{informative_imgs} ({pct:.0f}%) informative img elements lack descriptive alt attributes.",
                "suggested_action": {
                    "summary": "Add descriptive alt text to all informative images and diagram graphics so multimodal AI parsers can extract factual context.",
                    "priority": "medium"
                }
            })
    return findings
