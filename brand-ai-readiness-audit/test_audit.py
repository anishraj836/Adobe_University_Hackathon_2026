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
from freshness_evaluator import evaluate_freshness, extract_temporal_signals
from entity_resolver import evaluate_entity
from audit_crawl import audit_crawl, parse_robots_records, is_bot_blocked
from conversion_evaluator import evaluate_conversion
from quotability_evaluator import evaluate_quotability
from filler_evaluator import evaluate_filler

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

    def test_14_multichannel_freshness_and_temporal_drift(self):
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
        """Entity ambiguity: Common-word brand with legalName and sameAs passes; generic brand without disambiguation fails."""
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
        """CSR false positive: Server-rendered page with empty mount root passes; client-only blank mount root fails."""
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
        """Conversion friction: Informational documentation page passes; commercial SaaS page lacking CTA fails."""
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
        """Passage quotability: Narrative blog-post container passes via scope gate; technical spec with dangling pronouns fails."""
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
        """Fact-to-filler ratio: Fluff inside hero container is exempt; identical fluff in technical section fails."""
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
        """Robots.txt evaluation: Permitted bot passes; path-scoped Disallow: /private/ is flagged as a partial block."""
        # Safe Case: Specific record with empty Disallow (RFC 9309 allow-all)
        safe_robots = "User-agent: ClaudeBot\nDisallow:\n"
        safe_records = parse_robots_records(safe_robots)
        blocked_safe, _ = is_bot_blocked("claudebot", safe_records)
        self.assertFalse(blocked_safe, "False positive: Explicitly permitted bot with empty Disallow was flagged as blocked!")

        # Unsafe Case: Specific record with path-scoped Disallow: /private/
        unsafe_robots = "User-agent: ClaudeBot\nDisallow: /private/\n"
        unsafe_records = parse_robots_records(unsafe_robots)
        blocked_unsafe, reason_unsafe = is_bot_blocked("claudebot", unsafe_records)
        self.assertTrue(blocked_unsafe, "True positive missed: Path-scoped disallow was not flagged as blocked!")
        self.assertIn("/private/", reason_unsafe)

    def test_21_csr_data_island_severity_downgrade_guard(self):
        """CSR data-island: Empty mount root with __NEXT_DATA__ JSON state downgrades from critical to medium."""
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
        """Filler evaluator: Domain-appropriate technical prose with 1-2 lexicon words ('seamless', 'state-of-the-art') does not flag."""
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

if __name__ == "__main__":
    unittest.main()
