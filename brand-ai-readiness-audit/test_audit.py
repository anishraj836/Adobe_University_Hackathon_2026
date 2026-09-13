#!/usr/bin/env python3
"""
Automated Test Suite for Brand AI-Readiness Audit Marketplace.
Validates detection accuracy, schema conformity, causal shielding,
conversion friction evaluation, and execution speed.
"""

import os
import sys
import time
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORCHESTRATOR_SCRIPTS = os.path.join(BASE_DIR, "skills/audit-orchestrator/scripts")
sys.path.insert(0, ORCHESTRATOR_SCRIPTS)
sys.path.insert(0, os.path.join(BASE_DIR, "skills/crawl-render-audit/scripts"))
sys.path.insert(0, os.path.join(BASE_DIR, "skills/freshness-corroboration/scripts"))
sys.path.insert(0, os.path.join(BASE_DIR, "skills/engagement-audit/scripts"))

from run_audit import run_audit, build_markdown_report
from schema_validator import validate_report_schema
from proactive_engine import generate_proactive_actions
from freshness_evaluator import evaluate_freshness
from schema_evaluator import evaluate_schema
from entity_resolver import evaluate_entity
from audit_crawl import audit_crawl, parse_robots_records, is_bot_blocked, count_words
from conversion_evaluator import evaluate_conversion, has_commercial_intent, check_primary_cta
from quotability_evaluator import evaluate_quotability
from filler_evaluator import evaluate_filler
from nontext_inspector import inspect_nontext

# ==============================================================================
# Adversarial Validation Framework
#
# Tests in this suite are organized to verify both true-positive detection of
# real architectural barriers and false-positive avoidance on legitimate web
# designs. This paired validation pattern covers:
# 1. robots.txt crawler evaluation (RFC 9309 specific-agent precedence & path scoping)
# 2. CSR vs SSR detection (word-count thresholds & hydration hook tolerance)
# 3. CSR data-island severity calibration (Next.js/Nuxt state downgrades)
# 4. Entity disambiguation (common-word brand legalName/sameAs gating)
# 5. Commercial-intent conversion gating (protecting docs/blogs from friction flags)
# 6. E-commerce CTA recognition (transactional buttons and commerce routes)
# 7. Passage quotability container scoping (narrative/editorial container exemptions)
# 8. Hero-zone filler exemption & technical prose immunity (anti-fluff LDR gating)
# 9. FAQ sibling-answer extraction (DOM sibling text vs meta-description fallback)
# 10. Decorative image exemption (WCAG role="presentation" & aria-hidden="true")
# 11. Expletive pronoun / dummy-subject filter in quotability analysis
# 12. Search / query form exemption from primary conversion CTA detection
# ==============================================================================

class TestBrandAIReadinessAudit(unittest.TestCase):

    def setUp(self):
        self.fixtures_dir = os.path.join(BASE_DIR, "fixtures")

    def test_01_blocked_site_detection(self):
        """False-negative guard: Explicit AI crawler bans in robots.txt (GPTBot, ClaudeBot) must trigger critical findings, preventing missed crawler blocks."""
        fixture = os.path.join(self.fixtures_dir, "blocked_site")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")
        
        # Verify AI robots disallow is detected
        titles = [f["title"].lower() for f in report["findings"]]
        self.assertTrue(any("robots.txt blocks ai" in t for t in titles))
        self.assertGreaterEqual(report["summary"]["critical"], 1)

    def test_02_pure_csr_spa_detection(self):
        """False-negative guard: Unrendered client-side SPAs with empty mount roots and zero static text must be flagged as critical CSR barriers."""
        fixture = os.path.join(self.fixtures_dir, "pure_csr_spa")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        # Verify CSR barrier is flagged
        titles = [f["title"].lower() for f in report["findings"]]
        self.assertTrue(any("client-side rendering" in t for t in titles))

    def test_03_modern_nextjs_ssr_pass(self):
        """False-positive guard: Modern pre-rendered SSR pages containing React/Next.js hydration scripts must NOT be incorrectly flagged as CSR barriers."""
        fixture = os.path.join(self.fixtures_dir, "modern_nextjs_ssr")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        # Ensure modern SSR with React flight scripts is NOT flagged as CSR barrier
        titles = [f["title"].lower() for f in report["findings"]]
        self.assertFalse(any("client-side rendering" in t for t in titles), "False positive: Modern SSR flagged as CSR!")
        self.assertEqual(report["summary"]["critical"], 0)

    def test_04_stale_and_uncorroborated_detection(self):
        """False-negative guard: Uncorroborated multi-channel stale dates, missing image alt text, and absent H1 headers must be reliably flagged without misses."""
        fixture = os.path.join(self.fixtures_dir, "stale_and_uncorroborated")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        titles = [f["title"].lower() for f in report["findings"]]
        self.assertTrue(any("stale temporal signals" in t for t in titles))
        self.assertTrue(any("uncaptioned images" in t for t in titles))
        self.assertTrue(any("missing primary <h1>" in t for t in titles))

    def test_05_high_performing_brand_benchmark(self):
        """False-positive guard: Well-structured, fully-optimized brand pages must receive a clean bill of health with zero critical or high findings."""
        fixture = os.path.join(self.fixtures_dir, "high_performing_brand")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        # Should have zero critical and zero high findings
        self.assertEqual(report["summary"]["critical"], 0)
        self.assertEqual(report["summary"]["high"], 0)

    def test_06_differentiator_evidence_conditioned_proactive_engine(self):
        """Anti-padding guard: Proactive engine must emit zero suggestions on minimal pages without evidence, while synthesizing turnkey code only when relevant Q&A or documentation signals exist."""
        # 1. Blank page: must NOT emit blanket proactive suggestions (Anti-padding verification)
        blank_bundle = {
            "html": "<html><body><h1>Minimal</h1><p>Hello world.</p></body></html>",
            "url": "https://minimal.com"
        }
        blank_proactive = generate_proactive_actions(blank_bundle, set())
        self.assertEqual(len(blank_proactive), 0, "Proactive engine must not blanket-emit without evidence")

        # 2. Rich page with documentation and Q&A content: MUST trigger conditioned suggestions
        rich_bundle = {
            "html": """
            <html>
            <head><title>Enterprise Flow</title><meta name='description' content='High-throughput streaming'></head>
            <body>
              <nav><a href='/docs'>Documentation</a> <a href='/api'>API Reference</a></nav>
              <main>
                <h1>Enterprise Flow</h1>
                <p>High throughput event streaming engine.</p>
                <h3>How does batching work?</h3>
                <p>Events are grouped into micro-batches of 500 records.</p>
                <h2>Performance Specs</h2>
                <h2>Security Architecture</h2>
              </main>
            </body>
            </html>
            """,
            "url": "https://enterpriseflow.io"
        }
        rich_proactive = generate_proactive_actions(rich_bundle, set())
        self.assertGreaterEqual(len(rich_proactive), 2)
        
        # Verify markdown code blocks are present in suggested actions
        titles = [p["title"] for p in rich_proactive]
        self.assertTrue(any("/llms.txt" in t for t in titles), "Must suggest llms.txt when doc links observed")
        self.assertTrue(any("FAQPage" in t for t in titles), "Must suggest FAQPage when question patterns observed")
        for p in rich_proactive:
            self.assertIn("```", p["suggested_action"]["summary"], "Proactive actions must embed turnkey code blocks")

    def test_07_execution_speed_under_3_seconds(self):
        """Performance regression guard: Full end-to-end multi-skill audit across 5 diverse fixtures must execute within 3.0 seconds, avoiding runtime budget bloat."""
        start = time.time()
        for fixture_name in ["blocked_site", "pure_csr_spa", "modern_nextjs_ssr", "stale_and_uncorroborated", "high_performing_brand"]:
            fixture_path = os.path.join(self.fixtures_dir, fixture_name)
            report = run_audit(fixture_path)
            self.assertIsNotNone(report)
        elapsed = time.time() - start
        print(f"\n[*] Audited 5 test fixtures in {elapsed:.3f} seconds (< 3.0s limit).")
        self.assertLess(elapsed, 3.0)


    def test_08_rfc_9309_specific_agent_precedence(self):
        """False-positive guard: Specific User-agent allow records must override wildcard (*) disallows per RFC 9309 §2.2.1, preventing false crawler block alarms."""
        # Cloudflare pattern: Wildcard disallowed, but GPTBot explicitly allowed
        from audit_crawl import parse_robots_records, is_bot_blocked
        robots_txt = """
        User-agent: *
        Disallow: /

        User-agent: GPTBot
        Allow: /
        """
        records = parse_robots_records(robots_txt)
        blocked, reason = is_bot_blocked("GPTBot", records)
        self.assertFalse(blocked, "RFC 9309 precedence: Specific Allow: / must override wildcard Disallow: /")

    def test_09_multi_page_subpage_evidence(self):
        """Evidence fidelity guard: Multi-page structured data evaluation across subpages must accurately aggregate crawl counts and ratio evidence without phantom findings."""
        from schema_evaluator import evaluate_schema
        html_home = "<html><body><h1>Home</h1></body></html>"
        subpages = [
            {"path": "/pricing", "html": "<html><body><h1>Pricing</h1></body></html>"},
            {"path": "/about", "html": "<html><body><h1>About</h1></body></html>"}
        ]
        findings, blocks, types = evaluate_schema(html_home, subpages)
        self.assertGreaterEqual(len(findings), 1)
        evidence = findings[0]["evidence"]
        self.assertIn("Crawled 3 page(s)", evidence)
        self.assertIn("0/3 contain schema.org markup", evidence)

    def test_10_conversion_friction_evaluation(self):
        """False-positive & false-negative guard: Commercial SaaS pages lacking CTAs must trigger all 4 friction findings, while editorial pages and fully converted pages pass cleanly."""
        from conversion_evaluator import evaluate_conversion

        # 1. Unconverted commercial / SaaS product page (triggers all 4 friction findings)
        friction_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Enterprise Cloud Platform</title>
          <meta name="description" content="High performance cloud software platform for enterprise teams.">
        </head>
        <body>
          <main>
            <h1>Distributed Cache Platform</h1>
            <p>Our enterprise cloud platform provides sub-millisecond key-value storage across multiple cloud regions.</p>
          </main>
        </body>
        </html>
        """
        findings = evaluate_conversion(friction_html)
        self.assertEqual(len(findings), 4)
        finding_ids = {f["id"] for f in findings}
        self.assertIn("F-ENGAGE-011", finding_ids)
        self.assertIn("F-ENGAGE-012", finding_ids)
        self.assertIn("F-ENGAGE-013", finding_ids)
        self.assertIn("F-ENGAGE-014", finding_ids)

        # 2. Non-commercial personal blog / recipe page: MUST return 0 friction findings (Anti-false-positive scope gate)
        blog_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Traditional Pasta Recipe</title></head>
        <body>
          <article>
            <h1>How to make fresh tagliatelle</h1>
            <p>Combine 200g of flour with two eggs and knead for ten minutes until silky.</p>
          </article>
        </body>
        </html>
        """
        blog_findings = evaluate_conversion(blog_html)
        self.assertEqual(len(blog_findings), 0, "Non-commercial editorial pages must NOT trigger commercial friction warnings")

        # 3. Page with clear CTA, SOC2 certification, /pricing route, and FAQPage structured data
        converted_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Converted SaaS Platform</title>
          <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
          }
          </script>
        </head>
        <body>
          <header>
            <nav>
              <a href="/pricing">Pricing</a>
              <a href="/contact">Contact</a>
              <a href="/signup" class="btn">Get Started</a>
            </nav>
          </header>
          <main>
            <h1>Autonomous AI Infrastructure</h1>
            <p>SOC2 Type II accredited with end-to-end encryption.</p>
            <button>Book a Demo</button>
          </main>
        </body>
        </html>
        """
        clean_findings = evaluate_conversion(converted_html)
        self.assertEqual(len(clean_findings), 0, f"Expected 0 findings on fully converted page, got: {clean_findings}")

    def test_11_http_404_error_gating(self):
        """Causal error shielding guard: HTTP 404 reachability errors must be isolated at root, cleanly gating out downstream freshness and engagement audits to prevent cascading false positives."""
        from audit_crawl import audit_crawl
        from audit_freshness import audit_freshness
        from audit_engagement import audit_engagement

        bundle_404 = {"status": 404, "html": "<html><body><h1>Not Found</h1></body></html>", "url": "https://example.com"}

        crawl_findings = audit_crawl(bundle_404)
        self.assertTrue(any(f["id"] == "F-CRAWL-001" for f in crawl_findings), "404 must trigger F-CRAWL-001 unreachable finding")

        freshness_findings = audit_freshness(bundle_404)
        self.assertEqual(len(freshness_findings), 0, "404 must cleanly gate out freshness audit without false positives")

        engagement_findings = audit_engagement(bundle_404)
        self.assertEqual(len(engagement_findings), 0, "404 must cleanly gate out engagement audit without false positives")

    def test_12_proactive_anchor_suppression(self):
        """Deduplication guard: Proactive heading anchor suggestion (F-PROACT-004) must be suppressed if diagnostic finding F-ENGAGE-005 exists, preventing redundant report noise."""
        rich_bundle = {
            "html": """
            <html>
            <head><title>Heading Test</title></head>
            <body>
              <h2>Subheading Alpha</h2>
              <h2>Subheading Beta</h2>
            </body>
            </html>
            """,
            "url": "https://example.com"
        }
        # Without F-ENGAGE-005: proactive engine suggests F-PROACT-004
        proactive_without = generate_proactive_actions(rich_bundle, set())
        self.assertTrue(any(p["id"] == "F-PROACT-004" for p in proactive_without))

        # With F-ENGAGE-005: proactive engine must suppress F-PROACT-004
        proactive_with = generate_proactive_actions(rich_bundle, {"F-ENGAGE-005"})
        self.assertFalse(any(p["id"] == "F-PROACT-004" for p in proactive_with), "F-PROACT-004 must be suppressed if F-ENGAGE-005 already exists")

    def test_13_strict_schema_validation(self):
        """Contract compliance guard: Rejects malformed reports missing Handout Page 2 floor keys while safely permitting valid extension properties."""
        valid_report = {
            "site": "example.com",
            "audited_at": "2026-09-20T14:32:00Z",
            "summary": {
                "total_findings": 1,
                "critical": 1,
                "high": 0,
                "medium": 0
            },
            "findings": [
                {
                    "id": "F-001",
                    "title": "Robots block",
                    "severity": "critical",
                    "evidence": "Observed block",
                    "suggested_action": {"summary": "Fix robots.txt", "priority": "critical"}
                }
            ]
        }
        valid, errs = validate_report_schema(valid_report)
        self.assertTrue(valid, f"Valid report failed: {errs}")

        # Missing required floor key must fail
        missing_top = dict(valid_report)
        del missing_top["summary"]
        valid, errs = validate_report_schema(missing_top)
        self.assertFalse(valid)
        self.assertTrue(any("Missing required top-level key" in e for e in errs))

        # Missing summary floor key must fail
        missing_sum = dict(valid_report)
        missing_sum["summary"] = {"total_findings": 1, "critical": 1, "high": 0} # missing 'medium'
        valid, errs = validate_report_schema(missing_sum)
        self.assertFalse(valid)
        self.assertTrue(any("Summary missing required key" in e for e in errs))

        # Extension fields are allowed per handout spec ("floor, not a ceiling")
        ext_report = dict(valid_report)
        ext_report["crawl_duration_ms"] = 14.2
        valid, errs = validate_report_schema(ext_report)
        self.assertTrue(valid, f"Extension field rejected contrary to floor spec: {errs}")

    def test_14_multichannel_freshness_and_temporal_drift(self):
        """Temporal discrimination guard: Stale findings (F-FRESH-005) require corroboration across all channels, while inter-channel divergence (>180 days) triggers drift (F-FRESH-007)."""
        # Case A: Multi-channel corroboration of stale dates (> 365 days across all channels)
        stale_html = """
        <html>
        <head>
          <meta property="article:modified_time" content="2021-06-01">
        </head>
        <body>
          <time datetime="2021-05-15">May 15, 2021</time>
        </body>
        </html>
        """
        stale_headers = {"last-modified": "Tue, 01 Jun 2021 12:00:00 GMT"}
        stale_jsonld = [{"dateModified": "2021-06-01"}]

        stale_findings = evaluate_freshness(stale_html, stale_headers, stale_jsonld)
        self.assertTrue(any(f["id"] == "F-FRESH-005" for f in stale_findings))
        f_stale = next(f for f in stale_findings if f["id"] == "F-FRESH-005")
        self.assertIn("All 4 detected temporal channel(s) corroborate", f_stale["evidence"])

        # Case B: Temporal drift / desynchronization between channels (e.g. fresh HTTP header vs stale JSON-LD)
        drift_html = """
        <html>
        <head>
          <meta property="article:modified_time" content="2026-09-01">
        </head>
        <body></body>
        </html>
        """
        drift_headers = {"last-modified": "Mon, 01 Sep 2026 12:00:00 GMT"}
        drift_jsonld = [{"dateModified": "2021-01-10"}] # 5-year gap!

        drift_findings = evaluate_freshness(drift_html, drift_headers, drift_jsonld)
        self.assertTrue(any(f["id"] == "F-FRESH-007" for f in drift_findings))
        f_drift = next(f for f in drift_findings if f["id"] == "F-FRESH-007")
        self.assertIn("Conflicting temporal timestamps", f_drift["evidence"])

    def test_15_common_word_brand_disambiguation_guard(self):
        """False-positive & false-negative guard: Common-word brand with legalName and sameAs passes, while ambiguous brand without disambiguation fails."""
        # Safe Case: "Linear" with legalName and authoritative sameAs links
        safe_html = "<html><head><title>Linear | Issue Tracking</title></head><body></body></html>"
        safe_jsonld = [{
            "@type": "Organization",
            "name": "Linear",
            "legalName": "Linear Orbit Inc.",
            "sameAs": [
                "https://www.wikidata.org/wiki/Q100",
                "https://en.wikipedia.org/wiki/Linear"
            ]
        }]
        safe_findings = evaluate_entity(safe_html, safe_jsonld)
        self.assertFalse(any(f["id"] == "F-FRESH-008" for f in safe_findings), "False positive: Disambiguated brand flagged for hallucination risk!")

        # Unsafe Case: "Linear" with NO legalName, NO disambiguatingDescription, and NO sameAs links
        unsafe_html = "<html><head><title>Linear | Issue Tracking</title></head><body></body></html>"
        unsafe_jsonld = [{"@type": "Organization", "name": "Linear"}]
        unsafe_findings = evaluate_entity(unsafe_html, unsafe_jsonld)
        self.assertTrue(any(f["id"] == "F-FRESH-008" for f in unsafe_findings), "True positive missed: Ambiguous generic brand was not flagged!")

    def test_16_csr_ssr_hydration_guard(self):
        """False-positive & false-negative guard: Server-rendered page with empty mount root passes via static word count, while unrendered client-only root fails."""
        # Safe Case: <div id="root"> mount root present, but body contains 260 words of pre-rendered HTML
        safe_prose = " ".join(["enterprise"] * 260)
        safe_bundle = {
            "html": f"<html><body><div id='root'></div><article><p>{safe_prose}</p></article></body></html>",
            "is_local": True
        }
        safe_findings = audit_crawl(safe_bundle)
        self.assertFalse(any(f["id"] == "F-CRAWL-006" for f in safe_findings), "False positive: Pre-rendered SSR page flagged as CSR barrier!")

        # Unsafe Case: <div id="root"> mount root with only 10 words of visible text (< 50 words threshold)
        unsafe_bundle = {
            "html": "<html><body><div id='root'></div><p>Loading application scripts please wait.</p></body></html>",
            "is_local": True
        }
        unsafe_findings = audit_crawl(unsafe_bundle)
        self.assertTrue(any(f["id"] == "F-CRAWL-006" for f in unsafe_findings), "True positive missed: Blank CSR root was not flagged!")

    def test_17_docs_page_commercial_intent_guard(self):
        """False-positive & false-negative guard: Informational documentation page passes via commercial-intent scope gate, while commercial SaaS page lacking CTA fails."""
        # Safe Case: Technical documentation page with no pricing, demo, or signup intent
        docs_html = """
        <html>
        <body>
          <h1>Developer Documentation</h1>
          <p>Complete API reference detailing parameter schemas, error codes, and request retry strategies.</p>
          <a href="/guide">Getting Started Guide</a>
          <a href="/sdk">Python SDK</a>
        </body>
        </html>
        """
        docs_findings = evaluate_conversion(docs_html)
        self.assertEqual(len(docs_findings), 0, "False positive: Non-commercial docs page received commercial conversion findings!")

        # Unsafe Case: Commercial SaaS landing page with /pricing route and commercial copy, but 0 CTA buttons
        saas_html = """
        <html>
        <body>
          <h1>Enterprise AI Platform</h1>
          <p>Modern SaaS platform delivering enterprise subscription solutions with guaranteed SLA.</p>
          <a href="/pricing">View Pricing Plans</a>
        </body>
        </html>
        """
        saas_findings = evaluate_conversion(saas_html)
        self.assertTrue(any(f["id"] == "F-ENGAGE-011" for f in saas_findings), "True positive missed: Commercial SaaS page lacking CTA was not flagged!")

    def test_18_narrative_container_quotability_guard(self):
        """False-positive & false-negative guard: Narrative blog-post container passes via container-type scope gate, while technical spec with dangling pronouns fails."""
        # Generate 4 passage chunks (each ~500 chars) starting with dangling pronouns
        chunks_html = ""
        for verb in ["delivers", "processes", "executes", "orchestrates"]:
            chunks_html += f"<p>It {verb} " + "unbound enterprise factual operations " * 12 + ".</p>"

        # Safe Case: Wrapped in editorial/narrative container class="blog-post"
        safe_html = f"<article class='blog-post'>{chunks_html}</article>"
        safe_res = evaluate_quotability(safe_html)
        self.assertFalse(safe_res["flagged"], "False positive: Editorial blog-post container was not exempted by scope gate!")
        self.assertIn("Narrative container exempted", safe_res["evidence"])

        # Unsafe Case: Wrapped in non-exempt technical specification container class="spec"
        unsafe_html = f"<article class='spec'>{chunks_html}</article>"
        unsafe_res = evaluate_quotability(unsafe_html)
        self.assertTrue(unsafe_res["flagged"], "True positive missed: Technical prose with dangling pronouns was not flagged!")
        self.assertLess(unsafe_res["score"], 50)

    def test_19_hero_zone_filler_exemption_guard(self):
        """False-positive & false-negative guard: Marketing fluff inside hero container is exempt from LDR penalties, while identical fluff in technical sections fails."""
        fluff_copy = "World-class seamless synergy empowering disruptive next-gen paradigm holistic solutions. " * 10

        # Safe Case: Marketing buzzwords placed inside <section class="hero"> alongside substantive technical body copy
        safe_html = f"""
        <html>
        <body>
          <section class="hero"><p>{fluff_copy}</p></section>
          <main><p>Our vector search engine reduces latency to 42ms with 99.9% uptime across 10,000 requests per second.</p></main>
        </body>
        </html>
        """
        safe_res = evaluate_filler(safe_html)
        self.assertFalse(safe_res["flagged"], "False positive: Hero zone marketing copy was not exempted from fluff ratio!")

        # Unsafe Case: Identical buzzword copy placed inside non-hero <section class="features"> without quantified metrics
        unsafe_html = f"""
        <html>
        <body>
          <section class="features"><p>{fluff_copy}</p></section>
        </body>
        </html>
        """
        unsafe_res = evaluate_filler(unsafe_html)
        self.assertTrue(unsafe_res["flagged"], "True positive missed: Fluff-heavy technical section lacking metrics was not flagged!")

    def test_20_path_scoped_robots_disallow_guard(self):
        """False-positive guard: Path-scoped Disallow rules (/private/, /webstats/) do NOT flag site as blocked, while root Disallow: / correctly triggers block."""
        # Case A: Specific record with empty Disallow (RFC 9309 allow-all)
        safe_robots = "User-agent: ClaudeBot\nDisallow:\n"
        safe_records = parse_robots_records(safe_robots)
        blocked_safe, _ = is_bot_blocked("claudebot", safe_records)
        self.assertFalse(blocked_safe, "False positive: Explicitly permitted bot with empty Disallow was flagged as blocked!")

        # Case B: Specific record with path-scoped Disallow: /private/ (site remains indexable!)
        path_scoped_robots = "User-agent: ClaudeBot\nDisallow: /private/\n"
        path_records = parse_robots_records(path_scoped_robots)
        blocked_path, reason_path = is_bot_blocked("claudebot", path_records)
        self.assertFalse(blocked_path, "False positive: Narrow path-scoped Disallow: /private/ must not flag site as blocked!")
        self.assertIn("/private/", reason_path)

        # Case C: True positive: Root Disallow: / blocks the crawler
        root_blocked_robots = "User-agent: ClaudeBot\nDisallow: /\n"
        root_records = parse_robots_records(root_blocked_robots)
        blocked_root, reason_root = is_bot_blocked("claudebot", root_records)
        self.assertTrue(blocked_root, "True positive missed: Root Disallow: / must flag as blocked!")
        self.assertIn("Disallow: /", reason_root)

    def test_21_csr_data_island_severity_downgrade_guard(self):
        """Severity calibration guard: Empty mount root with __NEXT_DATA__ JSON state downgrades from critical to medium, while non-JSON garbage scripts retain critical severity."""
        # Safe-ish Case: Empty mount root (<div id="root"></div>) and thin prose (<50 words), but with non-trivial __NEXT_DATA__ JSON
        next_json = '{"props":{"pageProps":{"title":"Enterprise Cloud","pricing":"$99/mo"}}}'
        data_island_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>Next.js App</title>
          <script id="__NEXT_DATA__" type="application/json">{next_json}</script>
        </head>
        <body>
          <div id="root"></div>
          <p>Loading application...</p>
        </body>
        </html>
        """
        bundle_island = {"html": data_island_html, "is_local": True}
        findings_island = audit_crawl(bundle_island)
        csr_island = [f for f in findings_island if f["id"] == "F-CRAWL-006"]
        self.assertEqual(len(csr_island), 1, "Expected F-CRAWL-006 finding for empty mount root")
        self.assertEqual(csr_island[0]["severity"], "medium", f"Expected severity 'medium' for data island, got {csr_island[0]['severity']}")
        self.assertIn("__NEXT_DATA__", csr_island[0]["evidence"])
        self.assertEqual(csr_island[0]["suggested_action"]["priority"], "medium")

        # Full-barrier Case: Same empty root and thin prose, but NO data island anywhere
        no_island_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Pure React App</title></head>
        <body>
          <div id="root"></div>
          <p>Loading application...</p>
        </body>
        </html>
        """
        bundle_no_island = {"html": no_island_html, "is_local": True}
        findings_no_island = audit_crawl(bundle_no_island)
        csr_no_island = [f for f in findings_no_island if f["id"] == "F-CRAWL-006"]
        self.assertEqual(len(csr_no_island), 1, "Expected F-CRAWL-006 finding for empty mount root")
        self.assertEqual(csr_no_island[0]["severity"], "critical", f"Expected severity 'critical' without data island, got {csr_no_island[0]['severity']}")
        self.assertNotIn("__NEXT_DATA__", csr_no_island[0]["evidence"])

        # Adversarial Case C: Empty root with 11+ chars of unstructured non-JSON noise in __NEXT_DATA__ (must NOT downgrade)
        garbage_island_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Broken Build App</title>
          <script id="__NEXT_DATA__">xxxxxxxxxxx</script>
        </head>
        <body>
          <div id="root"></div>
          <p>Loading application...</p>
        </body>
        </html>
        """
        bundle_garbage = {"html": garbage_island_html, "is_local": True}
        findings_garbage = audit_crawl(bundle_garbage)
        csr_garbage = [f for f in findings_garbage if f["id"] == "F-CRAWL-006"]
        self.assertEqual(len(csr_garbage), 1, "Expected F-CRAWL-006 finding for empty mount root")
        self.assertEqual(csr_garbage[0]["severity"], "critical", f"Expected severity 'critical' for non-JSON garbage script content, got {csr_garbage[0]['severity']}")
        self.assertNotIn("__NEXT_DATA__", csr_garbage[0]["evidence"])

    def test_22_technical_prose_fluff_lexicon_no_false_positive(self):
        """False-positive guard: Substantive engineering prose containing isolated lexicon terms ('seamless', 'state-of-the-art') must pass when below compound threshold floors."""
        sample_prose = """
        <article>
          <h2>Distributed Consensus Architecture</h2>
          <p>
            Our replication engine ensures seamless state transitions across heterogeneous worker nodes.
            The primary coordinator maintains consistent event ordering while follower nodes acknowledge log append operations.
            By decoupling transactional commit phases from local disk flushing, the pipeline provides state-of-the-art durability guarantees without blocking network threads.
            Failover coordinators elect active leaders through randomized election timeouts to avoid split-brain scenarios during partition events.
            Each replica maintains an append-only transaction ledger with monotonic sequence counters to verify log synchronization integrity.
            Network boundaries remain isolated through mutual certificate verification and deterministic packet validation routines across all clustered nodes in the mesh.
          </p>
        </article>
        """
        res = evaluate_filler(sample_prose)
        self.assertFalse(res["flagged"], f"False positive: Substantive technical prose flagged as filler: {res}")
        self.assertGreaterEqual(res["fluff_count"], 1, "Expected at least 1 fluff word detected")
        self.assertLess(res["fluff_count"], 5, "Fluff count should be below the 5-hit threshold floor")
        self.assertEqual(res["quant_matches"], 0, "Expected 0 quantified metrics to test the unquantified technical prose guard")

    def test_23_faq_sibling_answer_extraction_guard(self):
        """Extraction fidelity guard: FAQPage generator extracts immediate sibling DOM answer text rather than generic meta descriptions, falling back only when sibling text is absent."""
        # Case A: Sibling <p> element exists immediately after question heading
        bundle_sibling = {
            "html": (
                "<!DOCTYPE html><html><head><title>Cloud Service SLA</title>"
                "<meta name='description' content='Default fallback description for Cloud Service.'></head>"
                "<body>"
                "<h2>What is our SLA?</h2>"
                "<p>Our platform guarantees 99.99% multi-region uptime.</p>"
                "</body></html>"
            ),
            "url": "https://example.com"
        }
        proactive_sibling = generate_proactive_actions(bundle_sibling, set())
        faq_finding = next((p for p in proactive_sibling if p["id"] == "F-PROACT-002"), None)
        self.assertIsNotNone(faq_finding, "Expected F-PROACT-002 finding for Q&A content")
        faq_summary = faq_finding["suggested_action"]["summary"]
        self.assertIn("99.99% multi-region uptime", faq_summary, "FAQPage JSON-LD must contain extracted sibling answer")
        self.assertNotIn("Default fallback description", faq_summary, "FAQPage JSON-LD should not use meta description when sibling text is present")

        # Case B: No sibling answer element (followed immediately by another heading)
        bundle_fallback = {
            "html": (
                "<!DOCTYPE html><html><head><title>Cloud Service SLA</title>"
                "<meta name='description' content='Default fallback description for Cloud Service.'></head>"
                "<body>"
                "<h2>What is our SLA?</h2>"
                "<h3>Next Heading</h3>"
                "</body></html>"
            ),
            "url": "https://example.com"
        }
        proactive_fallback = generate_proactive_actions(bundle_fallback, set())
        faq_fallback = next((p for p in proactive_fallback if p["id"] == "F-PROACT-002"), None)
        self.assertIsNotNone(faq_fallback, "Expected F-PROACT-002 finding for Q&A content")
        faq_fb_summary = faq_fallback["suggested_action"]["summary"]
        self.assertIn("Default fallback description for Cloud Service.", faq_fb_summary, "FAQPage JSON-LD must fall back to meta description when sibling element is absent")

    def test_24_ecommerce_cta_recognition_guard(self):
        """False-positive & false-negative guard: E-commerce storefront with 'Add to Cart' and /shop passes without missing-CTA flag, while commercial SaaS lacking CTAs triggers F-ENGAGE-011."""
        # Case A: E-commerce page with <button>Add to Cart</button> and <a href="/shop">
        ecom_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Artisan Store</title></head>
        <body>
          <h1>Handmade Leather Boots</h1>
          <p>Durable handcrafted footwear crafted from full grain leather.</p>
          <a href="/shop">Browse Store</a>
          <button>Add to Cart</button>
        </body>
        </html>
        """
        self.assertTrue(has_commercial_intent(ecom_html), "Expected has_commercial_intent to recognize e-commerce routes/terms")
        ecom_findings = evaluate_conversion(ecom_html)
        self.assertFalse(any(f["id"] == "F-ENGAGE-011" for f in ecom_findings), "E-commerce page with 'Add to Cart' button falsely flagged for missing CTA (F-ENGAGE-011)!")

        # Case B: Commercial page with SaaS copy and /pricing route but 0 CTA buttons
        saas_no_cta = """
        <!DOCTYPE html>
        <html>
        <head><title>Enterprise Cloud</title></head>
        <body>
          <h1>Enterprise Cloud Platform</h1>
          <p>Scalable cloud infrastructure delivering subscription solutions with guaranteed SLA.</p>
          <a href="/pricing">View Pricing Plans</a>
        </body>
        </html>
        """
        self.assertTrue(has_commercial_intent(saas_no_cta), "Expected has_commercial_intent to be True for commercial SaaS copy")
        saas_findings = evaluate_conversion(saas_no_cta)
        self.assertTrue(any(f["id"] == "F-ENGAGE-011" for f in saas_findings), "Commercial SaaS page lacking CTA must trigger F-ENGAGE-011")

    def test_25_decorative_image_exemption_guard(self):
        """False-positive & false-negative guard: Decorative images (role="presentation", aria-hidden="true") without alt text pass, while uncaptioned informative graphics fail."""
        # Case A: Purely decorative icon/background images lacking alt text
        safe_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Modern Interface</title></head>
        <body>
          <h1>Interface Architecture</h1>
          <p>The dashboard provides real-time event visualization and alerts.</p>
          <img src="/icons/star.svg" role="presentation">
          <img src="/icons/divider.png" role="none">
          <img src="/decorations/bg.svg" aria-hidden="true">
        </body>
        </html>
        """
        safe_findings = inspect_nontext(safe_html)
        self.assertFalse(any(f["id"] == "F-FRESH-009" for f in safe_findings), "False positive: Decorative images with role='presentation' or aria-hidden='true' were flagged for missing alt text!")

        # Case B: Genuinely informative diagram/infographic images lacking descriptive alt text
        unsafe_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Architecture Overview</title></head>
        <body>
          <h1>System Topology</h1>
          <p>Detailed technical architecture and failover topologies.</p>
          <img src="/diagrams/system-topology.png">
          <img src="/infographics/data-pipeline.png" alt="">
          <img src="/charts/benchmark-results.png" alt="graphic">
        </body>
        </html>
        """
        unsafe_findings = inspect_nontext(unsafe_html)
        self.assertTrue(any(f["id"] == "F-FRESH-009" for f in unsafe_findings), "True positive missed: Informative diagram graphics lacking alt text were not flagged!")
        self.assertIn("3/3 (100%) informative img elements", unsafe_findings[0]["evidence"])

    def test_26_expletive_pronoun_filter_guard(self):
        """False-positive & false-negative guard: Natural dummy-subject prose ('It is...', 'It takes...') does not penalize quotability, while genuine dangling anaphora fails."""
        # Case A: Informative prose using standard expletive/dummy-subject constructions
        safe_chunks = ""
        for phrase in [
            "Deployment requirements are minimal. It is essential to configure this before deployment.",
            "Initial cluster bootstrap takes seconds. It takes 30 seconds to complete setup.",
            "System diagnostics run continuously. It appears that the network throughput reaches optimum scale.",
            "Operational safeguards protect data. It has been verified across production clusters."
        ]:
            safe_chunks += f"<p>{phrase} " + "The distributed system coordinates state across regional edge workers without blocking the main thread. " * 5 + ".</p>"

        safe_html = f"<article class='spec'>{safe_chunks}</article>"
        safe_res = evaluate_quotability(safe_html)
        self.assertFalse(safe_res["flagged"], f"False positive: Expletive pronoun constructions flagged as dangling anaphora: {safe_res}")
        self.assertEqual(safe_res["dangling_chunks"], 0, f"Expected 0 dangling chunks for dummy subjects, got {safe_res['dangling_chunks']}")
        self.assertEqual(safe_res["score"], 100, "Expected 100/100 Atomic Quotability Score for properly formed dummy subjects")

        # Case B: Technical claims relying on genuine dangling pronouns without entity antecedents
        unsafe_chunks = ""
        for phrase in [
            "Deployment requirements are minimal. It delivers 99.99% multi-region uptime guarantees.",
            "Initial cluster bootstrap takes seconds. They feature sub-millisecond distributed consensus.",
            "System diagnostics run continuously. This provides zero-knowledge cryptographic encryption.",
            "Operational safeguards protect data. The platform executes transactional commit phases."
        ]:
            unsafe_chunks += f"<p>{phrase} " + "The distributed system coordinates state across regional edge workers without blocking the main thread. " * 5 + ".</p>"

        unsafe_html = f"<article class='spec'>{unsafe_chunks}</article>"
        unsafe_res = evaluate_quotability(unsafe_html)
        self.assertTrue(unsafe_res["flagged"], "True positive missed: Technical assertions with dangling pronouns were not flagged!")
        self.assertGreaterEqual(unsafe_res["dangling_chunks"], 3, "Expected at least 3 dangling chunks for unresolved pronouns")
        self.assertLess(unsafe_res["score"], 50, "Expected Atomic Quotability Score below 50")

    def test_27_search_form_cta_exemption_guard(self):
        """False-positive & false-negative guard: Search/query forms do not satisfy conversion CTAs, while genuine conversion buttons prevent missing-CTA flags."""
        # Case A: Commercial SaaS page containing a search form with submit button, but 0 conversion CTAs
        search_page = """
        <!DOCTYPE html>
        <html>
        <head><title>Enterprise Database</title></head>
        <body>
          <header>
            <form role="search" action="/search" method="get">
              <input type="text" name="q" placeholder="Search documentation...">
              <button type="submit">Search</button>
            </form>
            <nav><a href="/pricing">Pricing Plans</a></nav>
          </header>
          <main>
            <h1>Enterprise Database Solutions</h1>
            <p>Scalable cloud infrastructure delivering managed database subscriptions with guaranteed SLA.</p>
          </main>
        </body>
        </html>
        """
        has_cta, _ = check_primary_cta(search_page)
        self.assertFalse(has_cta, "False positive: Search form with submit button was incorrectly identified as a conversion CTA!")
        search_findings = evaluate_conversion(search_page)
        self.assertTrue(any(f["id"] == "F-ENGAGE-011" for f in search_findings), "True positive missed: Commercial page with only a search form must trigger F-ENGAGE-011!")

        # Case B: Same page with a genuine primary conversion CTA button added
        cta_page = search_page.replace("</main>", "<button>Get Started</button></main>")
        has_cta_b, cta_msg = check_primary_cta(cta_page)
        self.assertTrue(has_cta_b, "Failed to recognize genuine 'Get Started' button CTA")
        self.assertIn("Get Started", cta_msg)
        cta_findings = evaluate_conversion(cta_page)
        self.assertFalse(any(f["id"] == "F-ENGAGE-011" for f in cta_findings), "False positive: Page with valid 'Get Started' CTA button flagged for missing CTA!")

    def test_28_ai_crawler_taxonomy_training_vs_citation_severity(self):
        """Severity calibration guard: Blocking citation crawlers (OAI-SearchBot, Claude-SearchBot) triggers critical severity, while blocking model training crawlers only (GPTBot, Google-Extended) triggers high severity."""
        # Case A: Only foundation model training crawler blocked -> severity must be 'high'
        training_robots = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: Google-Extended\nDisallow: /\n"
        bundle_training = {
            "status": 200,
            "url": "https://example.com",
            "html": "<html><body><h1>Example</h1><p>Test content.</p></body></html>",
            "robots_txt": training_robots,
            "headers": {},
            "bot_probe_status": 200,
            "is_local": False
        }
        findings_train = audit_crawl(bundle_training)
        crawl_train = [f for f in findings_train if f["id"] == "F-CRAWL-003"]
        self.assertEqual(len(crawl_train), 1, "Expected F-CRAWL-003 finding for blocked training crawlers")
        self.assertEqual(crawl_train[0]["severity"], "high", "Blocking only training crawlers must be severity 'high' (not critical)")
        self.assertIn("Model Training", crawl_train[0]["evidence"])

        # Case B: Live retrieval/citation crawler blocked -> severity must be 'critical'
        citation_robots = "User-agent: OAI-SearchBot\nDisallow: /\n\nUser-agent: Claude-SearchBot\nDisallow: /\n"
        bundle_citation = {
            "status": 200,
            "url": "https://example.com",
            "html": "<html><body><h1>Example</h1><p>Test content.</p></body></html>",
            "robots_txt": citation_robots,
            "headers": {},
            "bot_probe_status": 200,
            "is_local": False
        }
        findings_cite = audit_crawl(bundle_citation)
        crawl_cite = [f for f in findings_cite if f["id"] == "F-CRAWL-003"]
        self.assertEqual(len(crawl_cite), 1, "Expected F-CRAWL-003 finding for blocked citation crawlers")
        self.assertEqual(crawl_cite[0]["severity"], "critical", "Blocking live citation/retrieval crawlers must be severity 'critical'")
        self.assertIn("Live Retrieval/Citation", crawl_cite[0]["evidence"])

    def test_29_transient_probe_retry_guard(self):
        """Reliability guard: Network probe retry prevents false-positive F-CRAWL-002 on transient 429/503 responses."""
        from http_fetcher import fetch_target_bundle
        from unittest.mock import patch

        # Simulate first probe returning 429 and retry returning 200 (transient rate limit)
        call_count = [0]
        def mock_fetch_url(url, user_agent=None, timeout=6):
            if "GPTBot" in (user_agent or ""):
                call_count[0] += 1
                if call_count[0] == 1:
                    return {"status": 429, "url": url, "html": "", "headers": {}, "is_local": False, "error": None}
                return {"status": 200, "url": url, "html": "OK", "headers": {}, "is_local": False, "error": None}
            return {"status": 200, "url": url, "html": "<html><body><h1>OK</h1></body></html>", "headers": {}, "is_local": False, "error": None}

        with patch("http_fetcher.fetch_url", side_effect=mock_fetch_url):
            with patch("http_fetcher.time.sleep", return_value=None):
                bundle = fetch_target_bundle("https://example-transient.com")
                # Bot probe should have retried and recovered to 200
                self.assertEqual(bundle["bot_probe_status"], 200, "Expected probe retry to recover from transient 429")
                self.assertEqual(call_count[0], 2, "Expected exactly 2 probe attempts (initial + 1 bounded retry)")
                # audit_crawl should NOT emit F-CRAWL-002
                findings = audit_crawl(bundle)
                self.assertFalse(any(f["id"] == "F-CRAWL-002" for f in findings), "Transient 429 must not emit F-CRAWL-002 after successful retry")

    def test_30_multilingual_cjk_word_count_guard(self):
        """Generalization guard: Non-space-delimited languages (Chinese, Japanese, Thai, Korean) must not be miscalculated as having 0-1 words or flagged as CSR barriers."""
        # 120 continuous Chinese characters with zero spaces
        cjk_text = "欢迎访问我们的企业级智能代理架构平台。我们提供高可用分布式实时路由、零数据泄露企业级隐私保障以及毫秒级确定性执行。现代工程团队信赖我们的基础设施以构建弹性的AI工作流。"
        self.assertEqual(len(cjk_text.split()), 1, "Naive split must count as 1 word (demonstrating the vulnerability)")
        counted = count_words(cjk_text)
        self.assertGreaterEqual(counted, 80, f"Expected count_words to detect substantive CJK content, got {counted}")

        # Test bundle with CJK text and <div id="root">
        cjk_bundle = {
            "status": 200,
            "url": "https://example.cn",
            "html": f"<!DOCTYPE html><html><body><div id='root'></div><main><p>{cjk_text}</p></main></body></html>",
            "robots_txt": "",
            "headers": {},
            "bot_probe_status": 200,
            "is_local": True
        }
        findings = audit_crawl(cjk_bundle)
        self.assertFalse(any(f["id"] == "F-CRAWL-006" for f in findings), "False positive: Substantive CJK content page falsely flagged as CSR barrier!")

    def test_31_qualitative_schema_validation(self):
        """Detection accuracy guard: Incomplete declared schemas (empty Product offers or broken FAQPage Q&A) must be flagged with type-specific findings."""
        # Case A: Declared Product schema lacking offers and pricing
        empty_prod_html = """
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Cloud Storage Subscription"
        }
        </script>
        """
        findings_prod, _, _ = evaluate_schema(empty_prod_html)
        self.assertTrue(any(f["id"] == "F-FRESH-010" for f in findings_prod), "True positive missed: Empty Product schema lacking offers was not flagged!")

        # Case B: Declared FAQPage schema lacking valid acceptedAnswer
        empty_faq_html = """
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            {"@type": "Question", "name": "What is the uptime?"}
          ]
        }
        </script>
        """
        findings_faq, _, _ = evaluate_schema(empty_faq_html)
        self.assertTrue(any(f["id"] == "F-FRESH-011" for f in findings_faq), "True positive missed: FAQPage lacking acceptedAnswer was not flagged!")

    def test_32_unencrypted_http_check_guard(self):
        """Security signal guard: Plain unencrypted HTTP live URLs must trigger F-CRAWL-009, while HTTPS URLs and local fixtures remain clean."""
        # Case A: Live URL over plain HTTP
        http_bundle = {
            "status": 200,
            "url": "http://insecure-example.com",
            "html": "<html><body><h1>Example</h1><p>Substantive text content here.</p></body></html>",
            "robots_txt": "",
            "headers": {},
            "bot_probe_status": 200,
            "is_local": False
        }
        findings_http = audit_crawl(http_bundle)
        self.assertTrue(any(f["id"] == "F-CRAWL-009" for f in findings_http), "Unencrypted live HTTP must trigger F-CRAWL-009")

        # Case B: Live URL over HTTPS
        https_bundle = {
            "status": 200,
            "url": "https://secure-example.com",
            "html": "<html><body><h1>Example</h1><p>Substantive text content here.</p></body></html>",
            "robots_txt": "",
            "headers": {},
            "bot_probe_status": 200,
            "is_local": False
        }
        findings_https = audit_crawl(https_bundle)
        self.assertFalse(any(f["id"] == "F-CRAWL-009" for f in findings_https), "HTTPS must not trigger F-CRAWL-009")

    def test_33_markdown_executive_narrative_synthesis(self):
        """Output design guard: build_markdown_report synthesizes a plain-English strategic narrative above the numeric counts."""
        mock_report = {
            "site": "testbrand.com",
            "audited_at": "2026-09-13T20:00:00Z",
            "summary": {"total_findings": 3, "critical": 1, "high": 1, "medium": 1},
            "findings": [
                {
                    "id": "F-001",
                    "title": "Robots.txt blocks AI citation & retrieval crawlers",
                    "severity": "critical",
                    "evidence": "Disallow: / blocks OAI-SearchBot",
                    "suggested_action": {"summary": "Allow OAI-SearchBot", "priority": "critical"}
                }
            ]
        }
        md_text = build_markdown_report(mock_report)
        self.assertIn("## Executive Summary", md_text)
        self.assertIn("> This site suffers from severe architectural barriers", md_text)
        self.assertIn("- **Total Findings:** 3", md_text)

if __name__ == "__main__":
    unittest.main()
