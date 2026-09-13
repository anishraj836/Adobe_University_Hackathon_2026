"""
Resilient HTTP & Local Fixture Fetcher for Brand AI-Readiness Audit.
Supports dual-probe UA (Browser vs GPTBot), multi-page subpage discovery,
gzip decompression, redirects, timeouts, RFC 9309 robots.txt respect,
and transparent local fixture/file:// ingestion.
"""

import os
import time
import gzip
import re
import warnings
warnings.filterwarnings("ignore")

from urllib.parse import urlparse, urljoin

# Browser UA to bypass basic WAFs
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# AI Bot UA to test differential bot-blocking / cloaking
AI_BOT_UA = "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)"

def is_local_target(target: str) -> bool:
    """Check if target is a local file path or fixture directory."""
    if target.startswith("file://"):
        return True
    if os.path.exists(target):
        return True
    parsed = urlparse(target)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        if os.path.exists(target) or os.path.exists(os.path.abspath(target)):
            return True
    return False

def fetch_local(target: str) -> dict:
    """Read target from local disk or fixture directory, including subpages."""
    clean_path = target.replace("file://", "")
    if os.path.isdir(clean_path):
        index_file = os.path.join(clean_path, "index.html")
        robots_file = os.path.join(clean_path, "robots.txt")
        sitemap_file = os.path.join(clean_path, "sitemap.xml")
        llms_file = os.path.join(clean_path, "llms.txt")
        html_content = ""
        robots_content = ""
        sitemap_content = ""
        llms_content = ""

        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
        if os.path.exists(robots_file):
            with open(robots_file, "r", encoding="utf-8", errors="ignore") as f:
                robots_content = f.read()
        if os.path.exists(sitemap_file):
            with open(sitemap_file, "r", encoding="utf-8", errors="ignore") as f:
                sitemap_content = f.read()
        if os.path.exists(llms_file):
            with open(llms_file, "r", encoding="utf-8", errors="ignore") as f:
                llms_content = f.read()

        # Check for sibling HTML subpages in fixture directory
        subpages = []
        for fname in os.listdir(clean_path):
            if fname.endswith(".html") and fname != "index.html":
                sub_path = os.path.join(clean_path, fname)
                with open(sub_path, "r", encoding="utf-8", errors="ignore") as f:
                    subpages.append({
                        "url": f"file://{os.path.abspath(sub_path)}",
                        "path": f"/{fname}",
                        "html": f.read(),
                        "status": 200
                    })

        return {
            "status": 200,
            "url": f"file://{os.path.abspath(clean_path)}",
            "html": html_content,
            "robots_txt": robots_content,
            "sitemap_xml": sitemap_content,
            "llms_txt": llms_content,
            "subpages": subpages,
            "headers": {"content-type": "text/html; charset=utf-8"},
            "canonical_url": extract_canonical_url(html_content),
            "is_local": True,
            "error": None
        }
    elif os.path.isfile(clean_path):
        with open(clean_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()
        parent = os.path.dirname(clean_path)
        robots_file = os.path.join(parent, "robots.txt")
        robots_content = ""
        if os.path.exists(robots_file):
            with open(robots_file, "r", encoding="utf-8", errors="ignore") as f:
                robots_content = f.read()
        return {
            "status": 200,
            "url": f"file://{os.path.abspath(clean_path)}",
            "html": html_content,
            "robots_txt": robots_content,
            "sitemap_xml": "",
            "canonical_url": extract_canonical_url(html_content),
            "subpages": [],
            "headers": {"content-type": "text/html; charset=utf-8"},
            "is_local": True,
            "error": None
        }
    return {
        "status": 404,
        "url": target,
        "html": "",
        "robots_txt": "",
        "sitemap_xml": "",
        "subpages": [],
        "headers": {},
        "is_local": True,
        "error": f"Local path not found: {target}"
    }

def fetch_url(url: str, user_agent: str = BROWSER_UA, timeout: int = 6) -> dict:
    """Fetch HTTP/HTTPS URL with graceful fallback and header extraction."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        import requests
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        return {
            "status": resp.status_code,
            "url": resp.url,
            "html": resp.text,
            "headers": {k.lower(): v for k, v in resp.headers.items()},
            "is_local": False,
            "error": None
        }
    except Exception as e:
        # Fallback to standard library urllib
        try:
            import urllib.request
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
                if headers.get("content-encoding") == "gzip":
                    raw = gzip.decompress(raw)
                encoding = response.headers.get_content_charset() or "utf-8"
                text = raw.decode(encoding, errors="ignore")
                return {
                    "status": response.status,
                    "url": response.geturl(),
                    "html": text,
                    "headers": headers,
                    "is_local": False,
                    "error": None
                }
        except Exception as inner_e:
            return {
                "status": 0,
                "url": url,
                "html": "",
                "headers": {},
                "is_local": False,
                "error": str(inner_e or e)
            }

def extract_canonical_url(html: str) -> str:
    """Extract canonical URL link element if declared in markup."""
    match = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.I)
    if not match:
        match = re.search(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html, re.I)
    return match.group(1).strip() if match else ""

def _rfc9309_pattern_matches(pattern: str, path: str) -> bool:
    """Check if path matches RFC 9309 robots.txt pattern (supporting * wildcards and $ end-anchors)."""
    if not pattern:
        return False
    try:
        has_end_anchor = pattern.endswith("$")
        clean = pattern[:-1] if has_end_anchor else pattern
        escaped = re.escape(clean).replace(r"\*", ".*")
        regex_str = "^" + escaped + ("$" if has_end_anchor else "")
        return bool(re.search(regex_str, path))
    except Exception:
        return path.startswith(pattern)

def parse_robots_records(robots_text: str) -> dict:
    """
    RFC 9309 compliant parser:
    Groups user-agent lines into distinct records, separated by blank lines
    or transitions from directive lines back to user-agent lines.
    Preserves rule order and supports multi-agent grouped declarations.
    """
    records = {}
    current_agents = []
    in_directives = False
    sitemaps = []

    lines = robots_text.splitlines()
    for raw_line in lines:
        line = raw_line.split('#')[0].strip()
        if not line:
            if in_directives:
                current_agents = []
                in_directives = False
            continue

        lower = line.lower()
        if lower.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip().lower()
            if in_directives:
                current_agents = []
                in_directives = False
            if agent:
                current_agents.append(agent)
                if agent not in records:
                    records[agent] = {"allow": [], "disallow": [], "rules": []}
        elif lower.startswith("disallow:"):
            in_directives = True
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                records[agent]["disallow"].append(path)
                records[agent]["rules"].append(("disallow", path, len(path)))
        elif lower.startswith("allow:"):
            in_directives = True
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                records[agent]["allow"].append(path)
                records[agent]["rules"].append(("allow", path, len(path)))
        elif lower.startswith("sitemap:"):
            sitemaps.append(line.split(":", 1)[1].strip())

    records["__sitemaps__"] = sitemaps
    return records

def is_path_allowed_by_robots(path: str, robots_text: str, user_agent: str = "*") -> bool:
    """
    RFC 9309 compliant path check:
    1. Finds the most specific user-agent group matching user_agent (fallback to '*').
    2. Collects all matching Allow and Disallow rules in that group.
    3. Longest-match precedence (RFC 9309 §2.2.2): The rule with the longest path pattern wins.
    4. Equal length tie-breaker: Allow overrides Disallow.
    5. If no rules match: Default ALLOW.
    """
    if not robots_text:
        return True

    records = parse_robots_records(robots_text)
    ua_clean = user_agent.lower().split("/")[0].strip()

    # 1. Select the most specific record group matching user_agent
    target_record = None
    if ua_clean in records:
        target_record = records[ua_clean]
    else:
        for k in records:
            if k != "__sitemaps__" and (k == ua_clean or k in ua_clean or ua_clean in k):
                target_record = records[k]
                break

    if target_record is None and "*" in records:
        target_record = records["*"]

    if not target_record:
        return True

    # 2. Collect matching rules for this path
    matching = []
    for r_type, pat, r_len in target_record.get("rules", []):
        if not pat:
            if r_type == "disallow":
                matching.append((0, "allow", ""))
            continue
        if _rfc9309_pattern_matches(pat, path):
            matching.append((r_len, r_type, pat))

    if not matching:
        return True

    # 3. Sort by length descending; tie-breaker: 'allow' beats 'disallow'
    matching.sort(key=lambda r: (r[0], 1 if r[1] == "allow" else 0), reverse=True)
    return matching[0][1] == "allow"

def discover_subpages(html: str, origin: str, robots_txt: str, max_subpages: int = 3) -> list:
    """Discover, prioritize, and fetch high-leverage internal subpages adhering to robots.txt."""
    if not html:
        return []
    
    # Extract candidate hrefs
    hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    candidates = set()

    # Prioritization buckets
    priority_keywords = ["/product", "/features", "/pricing", "/about", "/docs", "/api", "/solutions"]
    excluded_keywords = ["logout", "login", "signin", "signup", "cart", "checkout", "account", "auth", "terms", "privacy"]
    excluded_extensions = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".zip", ".css", ".js")

    for h in hrefs:
        h = h.strip()
        if not h or h.startswith("#") or h.startswith("mailto:") or h.startswith("tel:") or h.startswith("javascript:"):
            continue
        if any(h.lower().endswith(ext) for ext in excluded_extensions):
            continue
        if any(kw in h.lower() for kw in excluded_keywords):
            continue

        resolved = urljoin(origin, h)
        parsed = urlparse(resolved)
        parsed_origin = urlparse(origin)

        # Ensure same host
        if parsed.netloc.lower() == parsed_origin.netloc.lower():
            path = parsed.path or "/"
            if path != "/" and path != "":
                candidates.add((resolved, path))

    # Sort candidates by priority keywords
    sorted_candidates = sorted(
        candidates,
        key=lambda item: any(kw in item[1].lower() for kw in priority_keywords),
        reverse=True
    )

    subpages = []
    for full_url, path in sorted_candidates:
        if len(subpages) >= max_subpages:
            break
        # RFC 9309 check: Ensure path is permitted by robots.txt before crawling
        if not is_path_allowed_by_robots(path, robots_txt):
            continue
        sub_resp = fetch_url(full_url, user_agent=BROWSER_UA, timeout=4)
        sub_status = sub_resp.get("status", 0)
        if sub_status == 200:
            subpages.append({
                "url": full_url,
                "path": path,
                "html": sub_resp.get("html", ""),
                "status": 200
            })
        elif sub_status in (404, 500):
            subpages.append({
                "url": full_url,
                "path": path,
                "html": "",
                "status": sub_status
            })

    return subpages

def fetch_target_bundle(target: str) -> dict:
    """
    Fetch comprehensive site bundle:
    - Homepage via standard browser UA
    - Homepage probe via GPTBot UA (for cloaking check)
    - robots.txt
    - sitemap.xml
    - llms.txt
    - Up to 3 prioritized internal subpages (adhering to robots.txt)
    """
    if is_local_target(target):
        return fetch_local(target)

    # Live target
    base_url = target if target.startswith("http") else f"https://{target}"
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Standard Homepage
    home_resp = fetch_url(base_url, user_agent=BROWSER_UA)
    
    # 2. AI Bot Probe (with bounded 1-retry backoff for transient 429/503 rate limits or server blips)
    bot_resp = fetch_url(base_url, user_agent=AI_BOT_UA)
    if bot_resp.get("status") in (429, 503):
        time.sleep(0.75)
        retry_resp = fetch_url(base_url, user_agent=AI_BOT_UA)
        if retry_resp.get("status") not in (0,):
            bot_resp = retry_resp

    # 3. robots.txt
    robots_url = urljoin(origin, "/robots.txt")
    robots_resp = fetch_url(robots_url, user_agent=BROWSER_UA)
    robots_txt = robots_resp.get("html", "") if robots_resp.get("status") == 200 else ""

    # 4. sitemap.xml
    sitemap_url = urljoin(origin, "/sitemap.xml")
    sitemap_resp = fetch_url(sitemap_url, user_agent=BROWSER_UA)

    # 5. llms.txt
    llms_url = urljoin(origin, "/llms.txt")
    llms_resp = fetch_url(llms_url, user_agent=BROWSER_UA)

    # 6. Discover and crawl prioritized subpages
    subpages = []
    if home_resp.get("status") == 200:
        subpages = discover_subpages(home_resp.get("html", ""), origin, robots_txt, max_subpages=3)

    return {
        "status": home_resp.get("status", 0),
        "url": home_resp.get("url", base_url),
        "origin": origin,
        "canonical_url": extract_canonical_url(home_resp.get("html", "")),
        "html": home_resp.get("html", ""),
        "headers": home_resp.get("headers", {}),
        "bot_probe_status": bot_resp.get("status", 0),
        "bot_probe_error": bot_resp.get("error"),
        "robots_txt": robots_txt,
        "sitemap_xml": sitemap_resp.get("html", "") if sitemap_resp.get("status") == 200 else "",
        "llms_txt": llms_resp.get("html", "") if llms_resp.get("status") == 200 else "",
        "subpages": subpages,
        "is_local": False,
        "error": home_resp.get("error")
    }
