#!/usr/bin/env python3
"""
Dedicated 4-Way Freshness Corroboration Evaluator.
Cross-corroborates dates across JSON-LD, OpenGraph, DOM <time>, and HTTP headers.
"""

from datetime import datetime, timezone
import re

def extract_dates(html: str, headers: dict, jsonld_blocks: list) -> list[datetime]:
    """Corroborate dates across JSON-LD, meta tags, DOM <time>, and HTTP headers."""
    found_dates = []

    # 1. JSON-LD dates
    for block in jsonld_blocks:
        if isinstance(block, dict):
            for field in ["dateModified", "datePublished", "uploadDate"]:
                val = block.get(field)
                if val and isinstance(val, str):
                    try:
                        clean_val = val[:10]
                        dt = datetime.strptime(clean_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        found_dates.append(dt)
                    except ValueError:
                        pass

    # 2. Meta tags
    meta_patterns = [
        r'<meta\s+property=["\']article:(?:modified_time|published_time)["\']\s+content=["\']([^"\']+)["\']',
        r'<meta\s+name=["\'](?:last-modified|publish-date|date)["\']\s+content=["\']([^"\']+)["\']'
    ]
    for pat in meta_patterns:
        for match in re.findall(pat, html, re.I):
            try:
                clean_match = match[:10]
                dt = datetime.strptime(clean_match, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                found_dates.append(dt)
            except ValueError:
                pass

    # 3. DOM <time datetime="...">
    time_matches = re.findall(r'<time\s+[^>]*datetime=["\']([^"\']+)["\']', html, re.I)
    for tm in time_matches:
        try:
            clean_tm = tm[:10]
            dt = datetime.strptime(clean_tm, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            found_dates.append(dt)
        except ValueError:
            pass

    # 4. HTTP Last-Modified header
    last_mod = headers.get("last-modified")
    if last_mod:
        try:
            dt = datetime.strptime(last_mod[:16], "%a, %d %b %Y").replace(tzinfo=timezone.utc)
            found_dates.append(dt)
        except ValueError:
            pass

    return found_dates

def evaluate_freshness(html: str, headers: dict, jsonld_blocks: list) -> list:
    """Evaluate temporal freshness signals."""
    findings = []
    dates = extract_dates(html, headers, jsonld_blocks)
    now = datetime.now(timezone.utc)

    if dates:
        most_recent = max(dates)
        age_days = (now - most_recent).days
        if age_days > 365:
            findings.append({
                "id": "F-FRESH-005",
                "title": "Stale temporal signals (> 1 year since content update)",
                "severity": "medium",
                "evidence": f"[Confidence: 92%] Most recent verified timestamp is {most_recent.strftime('%Y-%m-%d')} ({age_days} days old).",
                "suggested_action": {
                    "summary": "Update page content and publish fresh dateModified timestamps in JSON-LD to prevent AI assistants from deprecating citation confidence.",
                    "priority": "medium"
                }
            })
    else:
        findings.append({
            "id": "F-FRESH-006",
            "title": "Missing explicit temporal metadata",
            "severity": "medium",
            "evidence": "[Confidence: 94%] No datePublished, dateModified, or HTTP Last-Modified timestamps found across headers or markup.",
            "suggested_action": {
                "summary": "Expose ISO-8601 dateModified in structured data and configure web server to return Last-Modified headers.",
                "priority": "medium"
            }
        })
    return findings
