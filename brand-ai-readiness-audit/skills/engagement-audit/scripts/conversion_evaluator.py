#!/usr/bin/env python3
"""
Dedicated User Journey & Conversion Friction Evaluator.
Audits:
1. Primary Call to Action (CTA) presence and clarity (buttons, inputs, styled links, conversion forms).
2. Trust proof signals (testimonials, customer quotes, client logos, certifications, review ratings).
3. Essential commercial conversion routing (/pricing, /contact, /demo, /docs, /signup).
4. Discoverable support / FAQ paths for high-intent AI referrals.
"""

import os
import re
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRICTION_PATTERNS_PATH = os.path.join(CURRENT_DIR, "../references/friction_patterns.json")

# Default pattern sets with fallback
DEFAULT_CTA_TERMS = [
    r"get\s+started", r"sign\s+up", r"book\s+a\s+demo", r"request\s+a\s+demo",
    r"try\s+for\s+free", r"start\s+(?:your\s+)?free\s+trial", r"buy\s+now",
    r"contact\s+us", r"contact\s+support", r"contact\s+sales", r"schedule\s+a\s+demo",
    r"talk\s+to\s+sales", r"get\s+in\s+touch", r"order\s+now", r"claim\s+free",
    r"create\s+account", r"join\s+(?:for\s+)?free", r"start\s+building", r"start\s+free",
    r"add\s+to\s+cart", r"checkout", r"shop\s+now", r"shop\s+collection"
]

DEFAULT_COMMERCIAL_ROUTES = [
    "/pricing", "/contact", "/demo", "/docs", "/documentation",
    "/signup", "/sign-up", "/register", "/sales", "/buy",
    "/shop", "/cart", "/product", "/checkout"
]

if os.path.exists(FRICTION_PATTERNS_PATH):
    try:
        with open(FRICTION_PATTERNS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            loaded_cta = data.get("cta_patterns", [])
            if loaded_cta:
                DEFAULT_CTA_TERMS = [re.escape(term).replace(r"\ ", r"\s+") for term in loaded_cta]
            loaded_routes = data.get("commercial_routes", [])
            if loaded_routes:
                DEFAULT_COMMERCIAL_ROUTES = loaded_routes
    except Exception:
        pass

CTA_REGEX = re.compile(r'\b(' + '|'.join(DEFAULT_CTA_TERMS) + r')\b', re.I)

TRUST_PATTERNS = [
    # Certifications & compliance standards
    r'\b(?:soc\s*2|soc-2|iso\s*27001|gdpr|hipaa|pci-dss|fedramp)\b',
    r'\b(?:accredited|certified|certifications?|security\s+badge|compliance\s+audit)\b',
    # Ratings and review authorities
    r'\b(?:trustpilot|g2|capterra|gartner|peer\s+insights)\b',
    r'\b[45](?:\.[0-9])?\s*(?:\/\s*5|\s*stars?)\b',
    # Testimonials and client quotes
    r'\b(?:testimonials?|what\s+our\s+customers?\s+say|customer\s+story|case\s+stud(?:y|ies))\b',
    r'\b(?:trusted\s+by|used\s+by\s+teams|enterprise\s+customers)\b'
]
TRUST_REGEX = re.compile(r'(' + '|'.join(TRUST_PATTERNS) + r')', re.I)

SUPPORT_FAQ_ROUTES = [
    "/faq", "/help", "/support", "/knowledge-base", "/kb", "/docs", "/documentation", "/contact"
]

COMMERCIAL_SCHEMA_TYPES = {
    "product", "offer", "service", "softwareapplication",
    "financialproduct", "store", "localbusiness", "organization", "corporation"
}

COMMERCIAL_KEYWORDS = [
    r"\bpricing\b", r"\bplans\b", r"\benterprise\b", r"\bsaas\b",
    r"\bsolutions\b", r"\bfree trial\b", r"\bget started\b", r"\bsubscription\b",
    r"\bplatform\b", r"\bcustomers\b", r"\bdemo\b",
    r"\badd to cart\b", r"\bcheckout\b", r"\bshop\b", r"\bcart\b"
]

def has_commercial_intent(html: str) -> bool:
    """Determine if the page carries commercial / product intent."""
    # 1. Commercial Schema types in JSON-LD
    schema_matches = re.findall(r'["\']@type["\']\s*:\s*["\']([^"\']+)["\']', html, re.I)
    for s in schema_matches:
        if s.lower() in COMMERCIAL_SCHEMA_TYPES:
            return True

    # 2. Commercial navigation routes
    dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    for href in dom_hrefs:
        lower_href = href.lower()
        if any(cr in lower_href for cr in ["/pricing", "/product", "/plans", "/demo", "/signup", "/buy", "/checkout", "/solutions", "/shop", "/cart"]):
            return True

    # 3. >= 2 commercial keywords in text
    lower_text = html.lower()
    kw_hits = sum(1 for kw in COMMERCIAL_KEYWORDS if re.search(kw, lower_text))
    return kw_hits >= 2

def check_primary_cta(html: str) -> tuple[bool, str]:
    """Check for primary Call to Action (CTA) presence and clarity."""
    # 1. Search buttons
    button_matches = re.findall(r'<button\b[^>]*>(.*?)<\/button>', html, re.I | re.DOTALL)
    for btn in button_matches:
        text = re.sub(r'<[^>]+>', ' ', btn).strip()
        if CTA_REGEX.search(text):
            return True, f"Found button CTA: '{text[:40]}'"

    # 2. Search input void elements (type="submit" or type="button")
    input_matches = re.findall(r'<input\b[^>]*type=["\'](?:submit|button)["\'][^>]*>', html, re.I)
    for inp in input_matches:
        val_match = re.search(r'value=["\']([^"\']+)["\']', inp, re.I)
        if val_match:
            val_text = val_match.group(1).strip()
            if CTA_REGEX.search(val_text):
                return True, f"Found input CTA: '{val_text[:40]}'"

    # 3. Search anchor tags (especially those styled as buttons/CTAs or with explicit CTA copy)
    anchor_matches = re.findall(r'<a\b([^>]*)>(.*?)<\/a>', html, re.I | re.DOTALL)
    for attrs, body in anchor_matches:
        text = re.sub(r'<[^>]+>', ' ', body).strip()
        if CTA_REGEX.search(text):
            return True, f"Found anchor CTA: '{text[:40]}'"
        if re.search(r'class=["\'][^"\']*(?:btn|button|cta)[^"\']*["\']', attrs, re.I) and len(text) > 2:
            if CTA_REGEX.search(text) or re.search(r'\b(start|try|demo|join|buy)\b', text, re.I):
                return True, f"Found styled CTA button: '{text[:40]}'"

    # 4. Search forms with submit controls, filtering out search/query/filter forms
    form_matches = re.findall(r'<form\b([^>]*)>(.*?)<\/form>', html, re.I | re.DOTALL)
    for attrs, form_body in form_matches:
        if re.search(r'role=["\']search["\']', attrs, re.I):
            continue
        if re.search(r'action=["\'][^"\']*(?:search|query|filter)[^"\']*["\']', attrs, re.I):
            continue
        if re.search(r'name=["\'](?:q|query|search|filter)["\']', form_body, re.I):
            continue
        if re.search(r'type=["\']submit["\']', form_body, re.I) or re.search(r'<button\b', form_body, re.I):
            return True, "Found interactive conversion form with submit control"

    return False, "0 primary conversion CTAs found"

def check_trust_signals(html: str) -> tuple[bool, str]:
    """Check for trust proof signals (testimonials, customer quotes, logos, certifications, review ratings)."""
    # 1. Inspect text for certifications, compliance, ratings, or testimonials
    trust_match = TRUST_REGEX.search(html)
    if trust_match:
        return True, f"Detected trust indicator: '{trust_match.group(1)}'"

    # 2. Inspect blockquotes or testimonial containers
    if re.search(r'<(?:blockquote|figure\b[^>]*class=["\'][^"\']*(?:testimonial|quote|review)[^"\']*["\'])', html, re.I):
        return True, "Found customer quote or blockquote container"

    # 3. Inspect client/partner logos in DOM using compound tokens (avoid bare brand logo)
    if re.search(r'<img\b[^>]*(?:alt|class|id)=["\'][^"\']*(?:client|customer|partner|trusted-by|client-logo|customer-logo|partner-logo)[^"\']*["\']', html, re.I):
        return True, "Found customer/partner proof logo asset"

    # 4. Inspect JSON-LD for Review, AggregateRating, or accreditation
    if re.search(r'["\']@type["\']\s*:\s*["\'](?:Review|AggregateRating)["\']', html, re.I):
        return True, "Found Schema.org Review or AggregateRating structured data"

    return False, "0 trust verification signals detected"

def check_commercial_routes(html: str) -> tuple[bool, list[str]]:
    """Check for essential commercial conversion routes (/pricing, /contact, /demo, /docs, /signup)."""
    dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    found_routes = []
    for href in dom_hrefs:
        lower_href = href.lower()
        for cr in DEFAULT_COMMERCIAL_ROUTES:
            if cr in lower_href and cr not in found_routes:
                found_routes.append(cr)
    return len(found_routes) > 0, found_routes

def check_support_faq_paths(html: str) -> tuple[bool, str]:
    """Check for discoverable support/FAQ paths for AI-referred visitors with high intent."""
    # 1. Check for FAQPage or Question in structured data
    if re.search(r'["\']@type["\']\s*:\s*["\'](?:FAQPage|QAPage|Question)["\']', html, re.I):
        return True, "Found Schema.org FAQPage / Question structured data"

    # 2. Check for details/summary accordion elements
    if re.search(r'<details\b[^>]*>\s*<summary\b', html, re.I):
        return True, "Found native <details><summary> interactive FAQ accordion"

    # 3. Check for FAQ / Support navigation routes
    dom_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.I)
    for href in dom_hrefs:
        lower_href = href.lower()
        for sr in SUPPORT_FAQ_ROUTES:
            if sr in lower_href:
                return True, f"Found support/FAQ route: '{sr}'"

    # 4. Check headings for FAQ / Frequently Asked Questions
    if re.search(r'<h[1-4]\b[^>]*>[^<]*(?:frequently\s+asked|faq|common\s+questions|support)[^<]*<\/h[1-4]>', html, re.I):
        return True, "Found prominent FAQ / support section heading"

    return False, "0 support or FAQ pathways detected"

def evaluate_conversion(html: str) -> list[dict]:
    """
    Evaluate user journey and conversion friction.
    Only evaluates pages carrying commercial / product intent to prevent false-positive warnings on blogs/docs.
    """
    if not has_commercial_intent(html):
        return []

    findings = []

    has_cta, cta_detail = check_primary_cta(html)
    if not has_cta:
        findings.append({
            "id": "F-ENGAGE-011",
            "title": "Missing primary Call to Action (CTA) for AI-referred visitor conversion",
            "severity": "medium",
            "evidence": "Scanned interactive elements across DOM; 0 primary conversion CTAs ('Get Started', 'Sign Up', 'Book a Demo', 'Contact Us') detected.",
            "suggested_action": {
                "summary": "Add clear, prominent primary Call to Action (CTA) buttons ('Get Started', 'Book a Demo', or 'Contact Us') above the fold and in closing sections to capture AI-referred visitor intent.",
                "priority": "medium"
            }
        })

    has_trust, trust_detail = check_trust_signals(html)
    if not has_trust:
        findings.append({
            "id": "F-ENGAGE-012",
            "title": "Absence of customer proof or trust verification signals",
            "severity": "medium",
            "evidence": "Analyzed DOM and body prose; 0 customer testimonials, client logos, industry certifications (SOC2/ISO/GDPR), or third-party review ratings detected.",
            "suggested_action": {
                "summary": "Incorporate verifiable trust proof signals (e.g. enterprise client logos, customer testimonials, third-party review ratings, or security/compliance certifications) to establish credibility for AI referrals.",
                "priority": "medium"
            }
        })

    has_commercial, commercial_routes = check_commercial_routes(html)
    if not has_commercial:
        findings.append({
            "id": "F-ENGAGE-013",
            "title": "Missing essential commercial conversion routing",
            "severity": "medium",
            "evidence": "Evaluated navigation and anchor links; 0 commercial conversion routes found matching essential paths (/pricing, /contact, /demo, /docs, /signup).",
            "suggested_action": {
                "summary": "Provide direct navigation routes to essential commercial destinations (/pricing, /contact, /demo, /docs, /signup) to enable AI-referred visitors to transition smoothly into the conversion funnel.",
                "priority": "medium"
            }
        })

    has_support, support_detail = check_support_faq_paths(html)
    if not has_support:
        findings.append({
            "id": "F-ENGAGE-014",
            "title": "Missing discoverable FAQ or self-serve support pathways",
            "severity": "medium",
            "evidence": "0 self-serve support routes, FAQ navigation links, or FAQPage structured data detected for high-intent AI referrals seeking quick verification.",
            "suggested_action": {
                "summary": "Implement an easily discoverable FAQ section or support routing to address pre-conversion evaluation questions commonly posed by AI-referred users.",
                "priority": "medium"
            }
        })

    return findings

if __name__ == "__main__":
    import sys
    sample = "<html><body><h1>Example</h1><a href='/pricing'>Pricing</a><p>SaaS platform with enterprise solutions.</p></body></html>"
    print(json.dumps(evaluate_conversion(sample), indent=2))
