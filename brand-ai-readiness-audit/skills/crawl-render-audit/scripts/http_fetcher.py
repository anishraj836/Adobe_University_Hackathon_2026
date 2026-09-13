"""
Resilient HTTP & Local Fixture Fetcher for Brand AI-Readiness Audit.
Supports dual-probe UA (Browser vs GPTBot), gzip decompression, redirects,
timeouts, and transparent local fixture/file:// ingestion.
"""

import os
import sys
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
    """Read target from local disk or fixture directory."""
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

        return {
            "status": 200,
            "url": f"file://{os.path.abspath(clean_path)}",
            "html": html_content,
            "robots_txt": robots_content,
            "sitemap_xml": sitemap_content,
            "llms_txt": llms_content,
            "headers": {"content-type": "text/html; charset=utf-8"},
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

def fetch_target_bundle(target: str) -> dict:
    """
    Fetch comprehensive site bundle:
    - Homepage via standard browser UA
    - Homepage probe via GPTBot UA (for cloaking / differential block check)
    - robots.txt
    - sitemap.xml
    - llms.txt
    """
    if is_local_target(target):
        return fetch_local(target)

    # Live target
    base_url = target if target.startswith("http") else f"https://{target}"
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Standard Homepage
    home_resp = fetch_url(base_url, user_agent=BROWSER_UA)
    
    # 2. GPTBot Probe
    bot_resp = fetch_url(base_url, user_agent=AI_BOT_UA)

    # 3. robots.txt
    robots_url = urljoin(origin, "/robots.txt")
    robots_resp = fetch_url(robots_url, user_agent=BROWSER_UA)

    # 4. sitemap.xml
    sitemap_url = urljoin(origin, "/sitemap.xml")
    sitemap_resp = fetch_url(sitemap_url, user_agent=BROWSER_UA)

    # 5. llms.txt
    llms_url = urljoin(origin, "/llms.txt")
    llms_resp = fetch_url(llms_url, user_agent=BROWSER_UA)

    return {
        "status": home_resp.get("status", 0),
        "url": home_resp.get("url", base_url),
        "origin": origin,
        "html": home_resp.get("html", ""),
        "headers": home_resp.get("headers", {}),
        "bot_probe_status": bot_resp.get("status", 0),
        "bot_probe_error": bot_resp.get("error"),
        "robots_txt": robots_resp.get("html", "") if robots_resp.get("status") == 200 else "",
        "sitemap_xml": sitemap_resp.get("html", "") if sitemap_resp.get("status") == 200 else "",
        "llms_txt": llms_resp.get("html", "") if llms_resp.get("status") == 200 else "",
        "is_local": False,
        "error": home_resp.get("error")
    }
