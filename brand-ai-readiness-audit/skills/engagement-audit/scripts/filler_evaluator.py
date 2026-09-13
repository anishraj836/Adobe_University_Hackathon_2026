#!/usr/bin/env python3
"""
Dedicated Fact-to-Filler Ratio & Summarizer Dropout Evaluator (Round 2 Appendix F).
Identifies substantive technical sections where key facts are diluted by high corporate fluff.
"""

import os
import re
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LEXICON_PATH = os.path.join(CURRENT_DIR, "../references/filler_lexicon.json")

FLUFF_WORDS = set()
QUANT_PATTERNS = []
if os.path.exists(LEXICON_PATH):
    try:
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            FLUFF_WORDS = set(data.get("fluff_words", []))
            QUANT_PATTERNS = [re.compile(p, re.I) for p in data.get("quantified_patterns", [])]
    except Exception:
        pass

from html.parser import HTMLParser

class SubstantiveProseExtractor(HTMLParser):
    """
    Standard-library HTMLParser that strips navigation, headers, footers, scripts,
    and hero/banner containers with robust tag nesting depth tracking.
    Solves regex non-greedy truncation bugs on nested <div> containers.
    """
    VOID_TAGS = {"img", "br", "hr", "input", "meta", "link", "source", "track", "wbr", "col", "area", "base"}
    SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "noscript"}
    HERO_CLASSES = ("hero", "banner", "jumbotron")

    def __init__(self):
        super().__init__()
        self.skip_stack = []
        self.prose_parts = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self.VOID_TAGS:
            return

        attr_dict = dict(attrs)
        class_val = attr_dict.get("class", "").lower()
        id_val = attr_dict.get("id", "").lower()

        is_chrome = tag_lower in self.SKIP_TAGS
        is_hero = any(hc in class_val or hc in id_val for hc in self.HERO_CLASSES)

        if self.skip_stack:
            self.skip_stack.append(tag_lower)
        elif is_chrome or is_hero:
            self.skip_stack.append(tag_lower)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.VOID_TAGS:
            return

        if self.skip_stack:
            if tag_lower in self.skip_stack:
                while self.skip_stack:
                    popped = self.skip_stack.pop()
                    if popped == tag_lower:
                        break
            else:
                self.skip_stack.pop()

    def handle_data(self, data):
        if not self.skip_stack:
            text = data.strip()
            if text:
                self.prose_parts.append(text)

    def get_prose(self) -> str:
        return " ".join(self.prose_parts)

def strip_chrome(html: str) -> str:
    """Strip navigation, headers, footers, scripts, and styles to isolate substantive content."""
    clean = re.sub(r'<(script|style|nav|header|footer|aside)\b[^<]*(?:(?!<\/\1>)<[^<]*)*<\/\1>', ' ', html, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    return re.sub(r'\s+', ' ', clean).strip()

def extract_substantive_prose(html: str) -> str:
    """Extract substantive prose stripping chrome and hero sections with full tag nesting support."""
    try:
        extractor = SubstantiveProseExtractor()
        extractor.feed(html)
        extractor.close()
        prose = extractor.get_prose()
        if prose:
            return prose
    except Exception:
        pass
    # Resilient fallback
    non_hero = re.sub(r'<(section|div)\b[^>]*class=["\'][^"\']*(?:hero|banner|jumbotron)[^"\']*["\'][^>]*>.*?<\/\1>', '', html, flags=re.I | re.DOTALL)
    return strip_chrome(non_hero)

def evaluate_filler(html: str) -> dict:
    """
    Evaluates Fact-to-Filler ratio.
    Grounded in Appendix F: 'when the genuinely important lines are surrounded by low-value filler —
    the summary has little to work with, and the important part can simply disappear.'
    Safeguards:
    1. Hero Zone Exemption: Headers, banners, and hero sections (including nested divs) are 100% exempt.
    2. Informational Anchor Gate: Only flags if ZERO quantified metrics AND fluff ratio > 3.5%.
    """
    prose = extract_substantive_prose(html)
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9\-\.%]+\b', prose)]

    if len(words) < 80:
        return {"flagged": False, "evidence": "Short content; hero exemption applied."}

    quant_matches = 0
    for pat in QUANT_PATTERNS:
        quant_matches += len(pat.findall(prose))

    fluff_count = sum(1 for w in words if w in FLUFF_WORDS)
    fluff_ratio = (fluff_count / len(words)) * 100

    flagged = (quant_matches == 0) and (fluff_count >= 5) and (fluff_ratio > 3.5)

    return {
        "flagged": flagged,
        "fluff_count": fluff_count,
        "quant_matches": quant_matches,
        "fluff_ratio": fluff_ratio,
        "evidence": f"Analyzed substantive technical prose; detected {fluff_count} corporate buzzwords against {quant_matches} quantified metrics (buzzword saturation: {fluff_ratio:.1f}%). High risk of AI summarizer dropout per Appendix F."
    }
