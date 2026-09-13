#!/usr/bin/env python3
"""
Dedicated 4-Way Freshness Corroboration Evaluator.
Cross-corroborates dates across JSON-LD, OpenGraph, DOM <time>, and HTTP headers.
"""

from datetime import datetime, timezone
import re

def extract_temporal_signals(html: str, headers: dict, jsonld_blocks: list) -> list[dict]:
    """Corroborate dates across JSON-LD, meta tags, DOM <time>, and HTTP headers with provenance."""
    signals = []

    # 1. JSON-LD dates
    for block in jsonld_blocks:
        if isinstance(block, dict):
            for field in ["dateModified", "datePublished", "uploadDate"]:
                val = block.get(field)
                if val and isinstance(val, str):
                    try:
                        clean_val = val[:10]
                        dt = datetime.strptime(clean_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        signals.append({"channel": f"JSON-LD ({field})", "date": dt})
                    except ValueError:
                        pass

    # 2. Meta tags
    meta_patterns = [
        (r'<meta\s+property=["\']article:(?:modified_time|published_time)["\']\s+content=["\']([^"\']+)["\']', "OpenGraph (article)"),
        (r'<meta\s+name=["\'](?:last-modified|publish-date|date)["\']\s+content=["\']([^"\']+)["\']', "Meta date")
    ]
    for pat, label in meta_patterns:
        for match in re.findall(pat, html, re.I):
            try:
                clean_match = match[:10]
                dt = datetime.strptime(clean_match, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                signals.append({"channel": label, "date": dt})
            except ValueError:
                pass

    # 3. DOM <time datetime="...">
    time_matches = re.findall(r'<time\s+[^>]*datetime=["\']([^"\']+)["\']', html, re.I)
    for tm in time_matches:
        try:
            clean_tm = tm[:10]
            dt = datetime.strptime(clean_tm, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            signals.append({"channel": "DOM <time>", "date": dt})
        except ValueError:
            pass

    # 4. HTTP Last-Modified header (RFC 7231 / RFC 2822 / RFC 850 compliant parsing)
    last_mod = headers.get("last-modified")
    if last_mod:
        try:
            import email.utils
            dt = email.utils.parsedate_to_datetime(last_mod)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            signals.append({"channel": "HTTP Last-Modified", "date": dt})
        except Exception:
            try:
                dt = datetime.strptime(last_mod[:16], "%a, %d %b %Y").replace(tzinfo=timezone.utc)
                signals.append({"channel": "HTTP Last-Modified", "date": dt})
            except Exception:
                pass

    return signals

def extract_dates(html: str, headers: dict, jsonld_blocks: list) -> list[datetime]:
    """Backward-compatible helper returning a flat list of datetimes."""
    return [s["date"] for s in extract_temporal_signals(html, headers, jsonld_blocks)]

def evaluate_freshness(html: str, headers: dict, jsonld_blocks: list) -> list:
    """Evaluate temporal freshness signals across 4 channels."""
    findings = []
    signals = extract_temporal_signals(html, headers, jsonld_blocks)
    now = datetime.now(timezone.utc)

    if signals:
        most_recent = max(s["date"] for s in signals)
        oldest = min(s["date"] for s in signals)
        age_days = (now - most_recent).days

        # Deduplicate signals for clean reporting
        unique_channels = {}
        for s in signals:
            ch = s["channel"]
            d_str = s["date"].strftime('%Y-%m-%d')
            unique_channels[f"{ch} ({d_str})"] = s["date"]
        channels_summary = ", ".join(unique_channels.keys())

        # Conjunctive staleness: if even the most recent timestamp is > 365 days old,
        # then every single corroborated source confirms content age > 1 year.
        if age_days > 365:
            findings.append({
                "id": "F-FRESH-005",
                "title": "Stale temporal signals (> 1 year since content update)",
                "severity": "medium",
                "evidence": f"All {len(unique_channels)} detected temporal channel(s) corroborate content age > 365 days: {channels_summary}. Most recent verified timestamp is {most_recent.strftime('%Y-%m-%d')} ({age_days} days old).",
                "suggested_action": {
                    "summary": "Update page content and publish fresh dateModified timestamps in JSON-LD to prevent AI assistants from deprecating citation confidence.",
                    "priority": "medium"
                }
            })
        elif (most_recent - oldest).days > 180:
            # Corroboration Conflict: Significant temporal drift between channels
            drift_days = (most_recent - oldest).days
            findings.append({
                "id": "F-FRESH-007",
                "title": "Temporal signal divergence across corroboration channels",
                "severity": "medium",
                "evidence": f"Conflicting temporal timestamps detected across channels ({channels_summary}). Temporal drift of {drift_days} days between sources causes citation depreciation in LLMs.",
                "suggested_action": {
                    "summary": "Synchronize Last-Modified HTTP response headers, OpenGraph metadata, and JSON-LD dateModified timestamps to prevent AI search engines from discounting temporal validity.",
                    "priority": "medium"
                }
            })
    else:
        findings.append({
            "id": "F-FRESH-006",
            "title": "Missing explicit temporal metadata",
            "severity": "medium",
            "evidence": "No datePublished, dateModified, or HTTP Last-Modified timestamps found across headers or markup.",
            "suggested_action": {
                "summary": "Expose ISO-8601 dateModified in structured data and configure web server to return Last-Modified headers.",
                "priority": "medium"
            }
        })
    return findings
