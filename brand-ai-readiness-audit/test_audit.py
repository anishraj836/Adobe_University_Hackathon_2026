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

from run_audit import run_audit
from schema_validator import validate_report_schema
from proactive_engine import generate_proactive_actions

class TestBrandAIReadinessAudit(unittest.TestCase):

    def setUp(self):
        self.fixtures_dir = os.path.join(BASE_DIR, "fixtures")

    def test_01_blocked_site_detection(self):
        fixture = os.path.join(self.fixtures_dir, "blocked_site")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")
        
        # Verify AI robots disallow is detected
        titles = [f["title"].lower() for f in report["findings"]]
        self.assertTrue(any("robots.txt blocks ai" in t for t in titles))
        self.assertGreaterEqual(report["summary"]["critical"], 1)

    def test_02_pure_csr_spa_detection(self):
        fixture = os.path.join(self.fixtures_dir, "pure_csr_spa")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        # Verify CSR barrier is flagged
        titles = [f["title"].lower() for f in report["findings"]]
        self.assertTrue(any("client-side rendering" in t for t in titles))

    def test_03_modern_nextjs_ssr_pass(self):
        fixture = os.path.join(self.fixtures_dir, "modern_nextjs_ssr")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        # Ensure modern SSR with React flight scripts is NOT flagged as CSR barrier
        titles = [f["title"].lower() for f in report["findings"]]
        self.assertFalse(any("client-side rendering" in t for t in titles), "False positive: Modern SSR flagged as CSR!")
        self.assertEqual(report["summary"]["critical"], 0)

    def test_04_stale_and_uncorroborated_detection(self):
        fixture = os.path.join(self.fixtures_dir, "stale_and_uncorroborated")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        titles = [f["title"].lower() for f in report["findings"]]
        self.assertTrue(any("stale temporal signals" in t for t in titles))
        self.assertTrue(any("uncaptioned images" in t for t in titles))
        self.assertTrue(any("missing primary <h1>" in t for t in titles))

    def test_05_high_performing_brand_benchmark(self):
        fixture = os.path.join(self.fixtures_dir, "high_performing_brand")
        report = run_audit(fixture)
        valid, errors = validate_report_schema(report)
        self.assertTrue(valid, f"Schema errors: {errors}")

        # Should have zero critical and zero high findings
        self.assertEqual(report["summary"]["critical"], 0)
        self.assertEqual(report["summary"]["high"], 0)

    def test_06_differentiator_evidence_conditioned_proactive_engine(self):
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
        start = time.time()
        for fixture_name in ["blocked_site", "pure_csr_spa", "modern_nextjs_ssr", "stale_and_uncorroborated", "high_performing_brand"]:
            fixture_path = os.path.join(self.fixtures_dir, fixture_name)
            report = run_audit(fixture_path)
            self.assertIsNotNone(report)
        elapsed = time.time() - start
        print(f"\n[*] Audited 5 test fixtures in {elapsed:.3f} seconds (< 3.0s limit).")
        self.assertLess(elapsed, 3.0)


    def test_08_rfc_9309_specific_agent_precedence(self):
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

if __name__ == "__main__":
    unittest.main()
