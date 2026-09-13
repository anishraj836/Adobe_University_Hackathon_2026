#!/usr/bin/env python3
"""
Crawl & Render Audit Skill
Audits off-site AI crawler access, RFC 9309 robots.txt bot rules (with explicit user-agent precedence),
meta tags, and SSR vs CSR gaps.
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
    clean = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', ' ', html, flags=re.IGNORECASE)
    clean = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', ' ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    return re.sub(r'\s+', ' ', clean).strip()

def parse_robots_records(robots_text: str) -> dict:
    """
    RFC 9309 parser: extracts records for each User-agent, recording both allow and disallow paths.
    Returns {agent: {"allow": [...], "disallow": [...]}, "__sitemaps__": [...]}
    """
    records = {}
    current_agents = []
    lines = robots_text.splitlines()

    for line in lines:
        line = line.split('#')[0].strip()
        if not line:
            continue
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip().lower()
            current_agents.append(agent)
            records.setdefault(agent, {"allow": [], "disallow": []})
        elif line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                records[agent]["disallow"].append(path)
        elif line.lower().startswith("allow:"):
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                records[agent]["allow"].append(path)
        elif line.lower().startswith("sitemap:"):
            records.setdefault("__sitemaps__", []).append(line.split(":", 1)[1].strip())
        else:
            # Unrecognized directives or separators reset current agent block if blank
            pass

    return records

def is_bot_blocked(bot: str, records: dict) -> tuple[bool, str]:
    """
    RFC 9309 precedence:
    1. Most specific User-Agent record takes complete precedence over User-agent: *.
    2. Inside the record, Allow overrides Disallow for equal or longer paths.
    """
    bot_lower = bot.lower()
    
    # 1. Check specific bot record
    if bot_lower in records:
        entry = records[bot_lower]
        allows = entry.get("allow", [])
        disallows = entry.get("disallow", [])
        if "/" in allows:
            return False, f"Explicitly permitted by 'User-agent: {bot}' Allow: /"
        if "/" in disallows:
            return True, f"Explicitly blocked by 'User-agent: {bot}' Disallow: /"
        dis_paths = [d for d in disallows if d]
        if dis_paths:
            return True, f"Blocked on path(s) ({', '.join(dis_paths[:3])}) by 'User-agent: {bot}'"
        return False, "Specific record does not disallow root or indexed paths"

    # 2. Fall back to wildcard *
    if "*" in records:
        wildcard = records["*"]
        allows = wildcard.get("allow", [])
        disallows = wildcard.get("disallow", [])
        if "/" in allows:
            return False, "Wildcard (*) explicitly allows root"
        if "/" in disallows:
            return True, "Blocked by wildcard 'User-agent: *' Disallow: /"
        dis_paths = [d for d in disallows if d]
        if dis_paths:
            return True, f"Blocked on path(s) ({', '.join(dis_paths[:3])}) by wildcard '*'"

    return False, "Default-allowed under RFC 9309"

def has_structured_state(content: str) -> bool:
    """Verifies that unparsed script content contains genuine structured key-value state, not arbitrary noise."""
    return ("{" in content or "[" in content) and bool(re.search(r'["\']?\w{2,}["\']?\s*:', content))

def detect_data_island(html: str) -> tuple:
    """
    Detects inline serialized state data islands (Next.js, Nuxt, generic application/json state).
    Returns (pattern_name, byte_size) or (None, 0).
    """
    # 1. Next.js __NEXT_DATA__
    next_match = re.search(
        r'<script\b[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>(.*?)<\/script>',
        html,
        re.I | re.DOTALL
    )
    if next_match:
        content = next_match.group(1).strip()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, (dict, list)) and len(parsed) > 0:
                return "__NEXT_DATA__", len(content.encode("utf-8"))
        except Exception:
            if has_structured_state(content):
                return "__NEXT_DATA__", len(content.encode("utf-8"))

    # 2. Nuxt __NUXT__ or __NUXT_DATA__
    nuxt_data_match = re.search(
        r'<script\b[^>]*\bid=["\']__NUXT_DATA__["\'][^>]*>(.*?)<\/script>',
        html,
        re.I | re.DOTALL
    )
    if nuxt_data_match:
        content = nuxt_data_match.group(1).strip()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, (dict, list)) and len(parsed) > 0:
                return "__NUXT_DATA__", len(content.encode("utf-8"))
        except Exception:
            if has_structured_state(content):
                return "__NUXT_DATA__", len(content.encode("utf-8"))

    nuxt_window_match = re.search(
        r'<script\b[^>]*>(?:[^<]*\b(?:window\.)?__NUXT__\s*=\s*([^\n<]+))',
        html,
        re.I | re.DOTALL
    )
    if nuxt_window_match:
        content = nuxt_window_match.group(1).strip()
        if has_structured_state(content):
            return "__NUXT__", len(content.encode("utf-8"))

    # 3. Standalone <script type="application/json"> (excluding schema.org application/ld+json)
    for match in re.finditer(
        r'<script\b([^>]*\btype=["\']application\/json["\'][^>]*)>(.*?)<\/script>',
        html,
        re.I | re.DOTALL
    ):
        attrs = match.group(1)
        if "application/ld+json" in attrs.lower() or "__NEXT_DATA__" in attrs or "__NUXT_DATA__" in attrs:
            continue
        content = match.group(2).strip()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, (dict, list)) and len(parsed) > 0:
                id_m = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
                name = id_m.group(1) if id_m else "application/json"
                return name, len(content.encode("utf-8"))
        except Exception:
            if has_structured_state(content):
                id_m = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
                name = id_m.group(1) if id_m else "application/json"
                return name, len(content.encode("utf-8"))

    return None, 0

def audit_crawl(bundle: dict) -> list[dict]:
    """Execute all crawl-render checks on the fetched site bundle."""
    findings = []
    html = bundle.get("html", "")
    robots_txt = bundle.get("robots_txt", "")
    headers = bundle.get("headers", {})
    bot_status = bundle.get("bot_probe_status", 200)
    home_status = bundle.get("status", 200)
    is_local = bundle.get("is_local", False)

    # 1. Site Reachability Root-Cause Check
    if home_status == 0 or home_status >= 400:
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
            "evidence": f"Dual-probe discrepancy: Browser UA succeeded (HTTP 200) while GPTBot UA received HTTP {bot_status}.",
            "suggested_action": {
                "summary": "Whitelist verified AI assistant IP ranges and user-agents in your WAF / Cloudflare configuration.",
                "priority": "critical"
            }
        })

    # 3. RFC 9309 Robots.txt Analysis for AI Crawlers
    if robots_txt:
        records = parse_robots_records(robots_txt)
        blocked_bots = []
        evidence_details = []

        for bot in AI_CRAWLERS:
            blocked, reason = is_bot_blocked(bot, records)
            if blocked:
                blocked_bots.append(bot)
                evidence_details.append(f"{bot} ({reason})")

        if blocked_bots:
            is_gpt_blocked = "gptbot" in blocked_bots
            findings.append({
                "id": "F-CRAWL-003",
                "title": "Robots.txt blocks AI assistant crawlers",
                "severity": "critical" if is_gpt_blocked else "high",
                "evidence": f"RFC 9309 evaluation identified {len(blocked_bots)} blocked AI crawler(s): {', '.join(blocked_bots)}.",
                "suggested_action": {
                    "summary": "Update robots.txt to permit indexing by conversational AI crawlers (GPTBot, ClaudeBot, PerplexityBot) on public content paths.",
                    "priority": "critical" if is_gpt_blocked else "high"
                }
            })
    else:
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
    body_match = re.search(r'<body\b[^>]*>(.*?)<\/body>', html, re.DOTALL | re.IGNORECASE)
    body_content = body_match.group(1) if body_match else html
    visible_text = strip_tags(body_content)
    words = visible_text.split()
    word_count = len(words)

    has_empty_root = bool(re.search(r'<div\s+id=["\'](root|app|__next)["\']\s*>\s*<\/div>', html, re.I))

    if has_empty_root and word_count < 50:
        data_island_name, data_island_bytes = detect_data_island(html)
        if data_island_name:
            findings.append({
                "id": "F-CRAWL-006",
                "title": "Client-Side Rendering (CSR) barrier locks content from AI crawlers",
                "severity": "medium",
                "evidence": f"Empty mount root with {word_count} visible words, but detected an inline `{data_island_name}` JSON data island ({data_island_bytes} bytes) that may expose structured facts to crawlers capable of parsing embedded JSON state.",
                "suggested_action": {
                    "summary": "Expose the data currently locked in the client-side JSON state block as static, crawlable HTML/JSON-LD, or implement full SSR so plain-text crawlers can read it directly.",
                    "priority": "medium"
                }
            })
        else:
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
