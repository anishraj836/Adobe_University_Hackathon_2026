#!/usr/bin/env python3
"""
Crawl & Render Audit Skill
Audits off-site AI crawler access, robots.txt bot rules, meta tags, and SSR vs CSR gaps.
"""

import os
import sys
import json
import re
from urllib.parse import urlparse

# Ensure local script directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from http_fetcher import fetch_target_bundle, BROWSER_UA, AI_BOT_UA

AI_CRAWLERS = [
    "gptbot", "chatgpt-user", "claudebot", "perplexitybot", 
    "google-extended", "applebot-extended", "amazonbot", "bytespider", "ccbot"
]

def strip_tags(html: str) -> str:
    """Strip HTML tags, scripts, and styles to get raw visible text."""
    # Remove script and style tags
    clean = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', ' ', html, flags=re.IGNORECASE)
    clean = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', ' ', clean, flags=re.IGNORECASE)
    # Remove tags
    clean = re.sub(r'<[^>]+>', ' ', clean)
    # Collapse whitespace
    return re.sub(r'\s+', ' ', clean).strip()

def parse_robots_rules(robots_text: str) -> dict:
    """Parse robots.txt to extract per-user-agent disallow directives."""
    rules = {}
    current_agents = []
    lines = robots_text.splitlines()

    for line in lines:
        line = line.split('#')[0].strip()
        if not line:
            continue
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip().lower()
            current_agents.append(agent)
        elif line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                rules.setdefault(agent, []).append(path)
        elif line.lower().startswith("sitemap:"):
            rules.setdefault("__sitemaps__", []).append(line.split(":", 1)[1].strip())
        elif line.lower().startswith("allow:"):
            pass
        else:
            # Reset agent block on unrecognized directive if needed
            pass
    return rules

def audit_crawl(bundle: dict) -> list:
    """Execute all crawl-render checks on the fetched site bundle."""
    findings = []
    html = bundle.get("html", "")
    robots_txt = bundle.get("robots_txt", "")
    headers = bundle.get("headers", {})
    bot_status = bundle.get("bot_probe_status", 200)
    home_status = bundle.get("status", 200)
    is_local = bundle.get("is_local", False)

    # 1. Site Reachability Root-Cause Check
    if home_status == 0 or (home_status >= 400 and home_status != 404):
        err = bundle.get("error") or f"HTTP status {home_status}"
        findings.append({
            "id": "F-CRAWL-001",
            "title": "Target website unreachable or blocking connections",
            "severity": "critical",
            "evidence": f"Connection probe failed with status: {err}.",
            "suggested_action": {
                "summary": "Ensure the origin server is online, accessible over HTTPS, and does not block automated requests.",
                "priority": "critical"
            }
        })
        return findings

    # 2. AI-Selective Bot Blocking / Cloaking Probe
    if not is_local and home_status == 200 and bot_status in (401, 403, 429, 503):
        findings.append({
            "id": "F-CRAWL-002",
            "title": "AI crawler user-agents selectively blocked at network layer",
            "severity": "critical",
            "evidence": f"Browser UA succeeded (HTTP 200) while GPTBot UA received HTTP {bot_status}.",
            "suggested_action": {
                "summary": "Whitelist verified AI assistant IP ranges and user-agents in your WAF / Cloudflare configuration.",
                "priority": "critical"
            }
        })

    # 3. Robots.txt Analysis for AI Crawlers
    if robots_txt:
        rules = parse_robots_rules(robots_txt)
        blocked_bots = []
        
        # Check wildcard disallow
        wildcard_disallows = rules.get("*", [])
        if "/" in wildcard_disallows or "" in wildcard_disallows and len(wildcard_disallows) == 1 and wildcard_disallows[0] == "/":
            blocked_bots.append("all crawlers (*)")

        for bot in AI_CRAWLERS:
            if bot in rules:
                bot_disallows = rules[bot]
                if "/" in bot_disallows:
                    blocked_bots.append(bot)

        if blocked_bots:
            findings.append({
                "id": "F-CRAWL-003",
                "title": "Robots.txt blocks AI assistant crawlers",
                "severity": "critical" if "all crawlers (*)" in blocked_bots or "gptbot" in blocked_bots else "high",
                "evidence": f"Disallow: / configured for: {', '.join(blocked_bots)} in robots.txt.",
                "suggested_action": {
                    "summary": "Update robots.txt to permit indexing by conversational AI crawlers (GPTBot, ClaudeBot, PerplexityBot) on public content paths.",
                    "priority": "critical" if "all crawlers (*)" in blocked_bots else "high"
                }
            })
    else:
        # Missing robots.txt is not a blocker (RFC 9309 allows crawl), but sitemap discovery is impacted
        if not is_local:
            findings.append({
                "id": "F-CRAWL-004",
                "title": "Missing robots.txt file",
                "severity": "medium",
                "evidence": "HTTP GET /robots.txt returned 404 or empty content.",
                "suggested_action": {
                    "summary": "Deploy a standard robots.txt declaring explicit permissions for AI search bots and linking your sitemap.",
                    "priority": "medium"
                }
            })

    # 4. Meta Robots & X-Robots-Tag Restrictions
    meta_robots_match = re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    x_robots_tag = headers.get("x-robots-tag", "")
    restrictions = []

    if meta_robots_match:
        content = meta_robots_match.group(1).lower()
        for token in ["noindex", "noai", "noimageai"]:
            if token in content:
                restrictions.append(f"meta robots={token}")

    if x_robots_tag:
        for token in ["noindex", "noai", "noimageai"]:
            if token in x_robots_tag.lower():
                restrictions.append(f"X-Robots-Tag: {token}")

    if restrictions:
        findings.append({
            "id": "F-CRAWL-005",
            "title": "Robots meta tags prohibit AI ingestion or indexing",
            "severity": "critical" if any("noindex" in r for r in restrictions) else "high",
            "evidence": f"Detected restrictive tags: {', '.join(restrictions)}.",
            "suggested_action": {
                "summary": "Remove noindex, noai, or noimageai directives from public indexable landing pages.",
                "priority": "high"
            }
        })

    # 5. Modern SSR vs Pure CSR Gap Detection
    # Strip scripts, styles, and extract body text
    body_match = re.search(r'<body\b[^>]*>(.*?)<\/body>', html, re.DOTALL | re.IGNORECASE)
    body_content = body_match.group(1) if body_match else html
    visible_text = strip_tags(body_content)
    words = visible_text.split()
    word_count = len(words)

    # Check for empty mount roots
    has_empty_root = bool(re.search(r'<div\s+id=["\'](root|app|__next)["\']\s*>\s*<\/div>', html, re.I))
    has_noscript = bool(re.search(r'<noscript>.*?javascript.*?</noscript>', html, re.I | re.DOTALL))

    if has_empty_root and word_count < 50:
        findings.append({
            "id": "F-CRAWL-006",
            "title": "Client-Side Rendering (CSR) barrier locks content from AI crawlers",
            "severity": "critical",
            "evidence": f"Raw HTML contains empty mount root (<div id='root'>) and only {word_count} visible text words without JS execution.",
            "suggested_action": {
                "summary": "Implement Server-Side Rendering (SSR) or Static Site Generation (SSG) so search crawlers receive pre-rendered HTML without executing client JavaScript bundles.",
                "priority": "critical"
            }
        })
    elif word_count < 100 and not has_empty_root and len(html) > 500:
        findings.append({
            "id": "F-CRAWL-007",
            "title": "Low static HTML content volume",
            "severity": "medium",
            "evidence": f"Page contains only {word_count} words of readable text in static HTML payload.",
            "suggested_action": {
                "summary": "Ensure key brand descriptions, value propositions, and FAQs are embedded directly in static HTML rather than fetched asynchronously via client-side APIs.",
                "priority": "medium"
            }
        })

    # 6. XML Sitemap Discoverability
    sitemap_xml = bundle.get("sitemap_xml", "")
    has_sitemap_directive = "sitemap:" in robots_txt.lower()
    if not sitemap_xml and not has_sitemap_directive:
        findings.append({
            "id": "F-CRAWL-008",
            "title": "No XML Sitemap found or referenced",
            "severity": "medium",
            "evidence": "Neither /sitemap.xml was accessible nor was a Sitemap: directive declared in robots.txt.",
            "suggested_action": {
                "summary": "Generate an automated sitemap.xml listing all canonical pages and declare its URL in robots.txt.",
                "priority": "medium"
            }
        })

    return findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    bundle = fetch_target_bundle(target)
    findings = audit_crawl(bundle)
    print(json.dumps({"skill": "crawl-render-audit", "target": target, "findings": findings}, indent=2))
