#!/usr/bin/env python3
"""
Dedicated 5-Second Cognitive Orientation Evaluator.
Evaluates primary H1 presence/clarity, meta description alignment, and mobile viewport responsiveness.
"""

import re

def evaluate_orientation(html: str) -> tuple[list, str]:
    """
    Evaluate 5-second cognitive orientation.
    Returns (findings, brand_hint).
    """
    findings = []
    h1_matches = re.findall(r'<h1\b[^>]*>(.*?)<\/h1>', html, re.I | re.DOTALL)
    meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.I)

    brand_hint = ""
    if h1_matches:
        h1_text = re.sub(r'<[^>]+>', '', h1_matches[0]).strip()
        stopwords = {"the", "a", "an", "our", "your", "welcome", "how", "why", "what", "modern", "fast", "enterprise", "we", "all", "new"}
        words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in h1_text.split()]
        words = [w for w in words if w]
        for w in words:
            if w.lower() not in stopwords:
                brand_hint = w
                break
        if not brand_hint and words:
            brand_hint = words[0]

        if len(h1_matches) > 2:
            findings.append({
                "id": "F-ENGAGE-002",
                "title": "Multiple competing <h1> headings cause orientation ambiguity",
                "severity": "medium",
                "evidence": f"Found {len(h1_matches)} distinct <h1> tags across parsed DOM, creating conflicting hierarchy signals for visitors and scrapers.",
                "suggested_action": {
                    "summary": "Consolidate into a single clear <h1> representing the core proposition, demoting secondary headings to <h2>.",
                    "priority": "medium"
                }
            })
        elif len(h1_text) < 5:
            findings.append({
                "id": "F-ENGAGE-003",
                "title": "Vague or empty primary <h1> headline",
                "severity": "medium",
                "evidence": f"Primary <h1> is only {len(h1_text)} characters ('{h1_text}').",
                "suggested_action": {
                    "summary": "Refine the <h1> headline to communicate a specific, concise value proposition.",
                    "priority": "medium"
                }
            })
    else:
        findings.append({
            "id": "F-ENGAGE-001",
            "title": "Missing primary <h1> heading for visitor orientation",
            "severity": "high",
            "evidence": "Crawled page; 0 <h1> heading tags detected in static DOM.",
            "suggested_action": {
                "summary": "Add a prominent <h1> tag within the hero section clearly stating what the company or product does.",
                "priority": "high"
            }
        })

    if not meta_desc_match or not meta_desc_match.group(1).strip():
        findings.append({
            "id": "F-ENGAGE-004",
            "title": "Missing or empty meta description",
            "severity": "medium",
            "evidence": "No valid <meta name='description'> tag found in document <head>.",
            "suggested_action": {
                "summary": "Add a high-signal meta description (120-160 characters) summarizing page purpose for search snippets and AI overview cards.",
                "priority": "medium"
            }
        })
    elif h1_matches:
        desc_text = meta_desc_match.group(1).strip()
        h1_clean = re.sub(r'<[^>]+>', '', h1_matches[0]).strip().lower()
        h1_tokens = {w for w in re.findall(r'\b[a-z]{4,}\b', h1_clean) if w not in stopwords}
        desc_tokens = {w for w in re.findall(r'\b[a-z]{4,}\b', desc_text.lower()) if w not in stopwords}
        if h1_tokens and desc_tokens:
            common = h1_tokens.intersection(desc_tokens)
            if not common and len(h1_tokens) >= 2 and len(desc_tokens) >= 5:
                findings.append({
                    "id": "F-ENGAGE-009",
                    "title": "Cognitive mismatch between primary <h1> and meta description",
                    "severity": "medium",
                    "evidence": f"0 shared topical keywords between headline ('{h1_clean[:50]}') and meta description ('{desc_text[:60]}...'). Arriving AI referrals experience immediate cognitive disconnect.",
                    "suggested_action": {
                        "summary": "Align primary <h1> messaging with the meta description so visitors referred by conversational AI recognize the proposition immediately.",
                        "priority": "medium"
                    }
                })

    # Mobile viewport meta tag check
    viewport_match = re.search(r'<meta\s+name=["\']viewport["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    if not viewport_match:
        findings.append({
            "id": "F-ENGAGE-010",
            "title": "Missing mobile viewport meta tag (mobile AI referral bounce risk)",
            "severity": "medium",
            "evidence": "No <meta name='viewport'> tag detected in document <head>; mobile AI assistant referrals (ChatGPT/Perplexity iOS) receive unscaled desktop UI.",
            "suggested_action": {
                "summary": "Add <meta name='viewport' content='width=device-width, initial-scale=1'> to ensure responsive rendering for mobile AI referrals.",
                "priority": "medium"
            }
        })

    return findings, brand_hint
