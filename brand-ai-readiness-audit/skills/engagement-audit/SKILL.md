---
name: engagement-audit
description: Audits on-site visitor orientation (5-second rule), AI referral landing readiness, deep-link citation anchors, substantive content density, and conversion friction traps.
license: Apache-2.0
allowed-tools:
  - python
  - bash
---

# Engagement & Friction Audit Skill

## When to use
Use when diagnosing why visitors referred from AI assistants bounce immediately or fail to engage with the website.

## Inputs
- `target`: URL or path to local fixture bundle.
- Executed directly via `scripts/audit_engagement.py <target>` or imported as a module by the orchestrator.

## Procedure
1. **5-Second Cognitive Orientation**: Inspect hero `<h1>` heading presence, clarity, and length; verify semantic alignment with `<meta name="description">`.
2. **AI Referral Landing & Deep Citation Anchors**: Inspect heading hierarchy (`<h1>` -> `<h2>` -> `<h3>`) and determine if subheadings possess HTML `id` attributes for deep-link citations.
3. **Substantive Content Density vs Boilerplate**: Strip navigation, headers, footers, scripts, and styles. Measure substantive body prose word count to detect thin-content landing pages.
4. **Trust & Compliance Signals**: Scan for visible links to essential trust pages (`/privacy`, `/terms`, `/contact`, `/about`).

## Output
Returns a structured list of findings:
- `F-ENGAGE-001`: Missing primary `<h1>` heading for visitor orientation.
- `F-ENGAGE-002`: Multiple competing `<h1>` headings causing hierarchy confusion.
- `F-ENGAGE-004`: Missing or empty meta description.
- `F-ENGAGE-005`: Subheadings lack persistent citation anchor IDs.
- `F-ENGAGE-006`: Low substantive body content (thin landing experience).
- `F-ENGAGE-007`: Missing essential trust and compliance routes.
