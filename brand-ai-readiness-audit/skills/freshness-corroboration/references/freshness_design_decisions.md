# Freshness Corroboration: Mathematical Formalism & Design Decisions

This document details the engineering and mathematical principles underlying `freshness_evaluator.py` in the `freshness-corroboration` skill.

---

## 1. Conjunctive Multi-Signal Staleness: Why `max(dates)` is Exact

A core question in temporal corroboration across $n$ signals $\{d_1, d_2, \dots, d_n\}$ is:
*How do we verify that **all** observed sources indicate that content is stale (> 365 days old)?*

### Formal Mathematical Proof:
1. The age in days of any timestamp $d_i$ relative to $\text{now}$ is:
   $$\text{age}(d_i) = \text{now} - d_i$$

2. The conjunctive condition that **all available sources agree on age > 365 days** is:
   $$\forall i \in \{1, \dots, n\}, \quad \text{age}(d_i) > 365$$

3. Substituting $\text{age}(d_i) = \text{now} - d_i$:
   $$\forall i \in \{1, \dots, n\}, \quad \text{now} - d_i > 365 \iff d_i < \text{now} - 365$$

4. In order for every date in a finite set to be less than a given threshold $T = \text{now} - 365$, the largest element in the set must be less than $T$:
   $$(\forall i, \ d_i < T) \iff \max(d_1, \dots, d_n) < T$$

5. Re-expressing in terms of age:
   $$\text{now} - \max(d_1, \dots, d_n) > 365 \iff \min(\text{age}(d_1), \dots, \text{age}(d_n)) > 365$$

### Corroboration Invariants:
- If **even one channel** (e.g., JSON-LD `dateModified`) reflects recent updates (say, 5 days ago), $\max(d)$ is 5 days old, and the staleness finding is suppressed. Content is only declared stale when **all channels agree**.
- If $\max(d)$ is older than 365 days, then by mathematical guarantee, **every other signal is at least that old or older**.
- Using $\min(d)$ (the oldest date) would introduce severe false positives: a page updated today would be flagged as stale if a legacy copyright line in the footer contained an old year.

---

## 2. Temporal Drift Detection (`F-FRESH-007`): Corroboration Conflict

While conjunctive staleness evaluates uniform age, real-world websites often suffer from **temporal desynchronization**:
- HTTP `Last-Modified` returned by a CDN edge deployment is recent (e.g., September 2026).
- Embedded Schema.org `dateModified` in the HTML payload is years old (e.g., February 2021).

### The AI Assistant Failure Mode:
When an AI search engine (Perplexity, Bing Copilot, ChatGPT Search) crawls the page, contradictory metadata causes citation discounting and temporal hallucination (e.g., citing obsolete product specs as current features).

### Heuristic Threshold:
- When $\max(\text{dates}) - \min(\text{dates}) > 180\text{ days}$ and content is not already flagged as uniformly stale, `freshness_evaluator.py` flags `F-FRESH-007: Temporal signal divergence across corroboration channels` (`medium`).
- The evidence string explicitly isolates each channel (`JSON-LD`, `OpenGraph`, `DOM <time>`, `HTTP Last-Modified`) and calculates the exact drift in days.
