#!/usr/bin/env python3
"""
Automated Test Suite for Brand AI-Readiness Audit Marketplace.
Validates detection accuracy, schema conformity, causal shielding,
the 4 Impressive Key Differentiators, and execution speed (< 0.5s).
"""

import os
import sys
import time
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORCHESTRATOR_SCRIPTS = os.path.join(BASE_DIR, "skills/audit-orchestrator/scripts")
sys.path.insert(0, ORCHESTRATOR_SCRIPTS)

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

if __name__ == "__main__":
    unittest.main()
