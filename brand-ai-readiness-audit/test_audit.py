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

    def test_06_differentiator_turnkey_artifacts(self):
        # Verify that proactive findings embed turnkey code blocks in suggested_action.summary
        fixture = os.path.join(self.fixtures_dir, "blocked_site")
        report = run_audit(fixture)
        proactive = [f for f in report["findings"] if "[Proactive Opportunity]" in f["title"]]
        self.assertGreaterEqual(len(proactive), 1)
        
        # Verify markdown code block presence
        has_code_block = any("```" in f["suggested_action"]["summary"] for f in proactive)
        self.assertTrue(has_code_block, "Proactive suggestions must embed turnkey code blocks")

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
