# Alignment Audit (Rules 85-100 / 16 items) — csv-dialect-fingerprint v0.1.1

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Not a security-research repo; no dual-use surface. Fails closed (exit 2) on missing paths and empty file sets |
| 2 | Privacy/dezero | PASS | No secrets/tokens/real names in any file; only contact line uses hcac4735@agent.qq.com (README License section); grep `(sk-\|ghp_\|api[_-]?key\s*=\s*['"][A-Za-z0-9])` → 0 hits |
| 3 | Copyright boundary | PASS | CSVsniffer / delimiter-quorum / P-CSVsniffer comparisons are structural restatements of their public descriptions, no >50-char copied text; MIT LICENSE present, "zhengming contributors" |
| 4 | Fact-check annotation | PASS | 42-check suite runtime "~3 s" marked [Measured] with repro `python self_test.py`; CLI step timings marked ~1 s/~2 s [estimated]; accuracy claims qualitative only |
| 5 | Confidence grading | PASS | Opener claim [High ≥80%] tied to the test suite; 80%-fallback claim in Minimal Fallback marked by construction; ≥2 explicit labels in README |
| 6 | PLAN B built-in | PASS | "Minimal Fallback (PLAN B)" section: pure shell delimiter-count + `file` checks, zero setup |
| 7 | Timeout preset | PASS | Quickstart states "~2 min" total with per-step ~1 s / ~2 s / ~3 s markers |
| 8 | Rule-conflict arbitration | PASS | "Design Trade-offs" opens with priority order: calibrated refusal > determinism > coverage > performance |
| 9 | Version changelog | PASS | CHANGELOG.md v0.1.0 + v0.1.1; v0.1.1 records the ranking bug fix, the 3 double-escaped test expectations, and the 37→42 test delta |
| 10 | Exemption instruction | N/A | Session-level rule; static repo content not applicable |
| 11 | External-knowledge cutoff | PASS | why-not-X equivalent-absence claim dated "as of 2026-10-12"; no vendor-version claims |
| 12 | Assumption explicitness | PASS | "[Core Assumptions]" section with 4 items |
| 13 | Logic-check trio | PASS | self_test.py tiers: functional (17) / error (8) / edge (17: 5000 rows, 200 cols, unicode, NUL, no trailing newline, CLI paths); `python self_test.py` → `SUMMARY: PASS 42/42` |
| 14 | Socratic question | PASS | FAQ "When NOT to use this tool?" with 4 anti-use-cases (accuracy-at-any-cost, single-column, full parsing, streaming) |
| 15 | Pareto improvement | PASS | v0.1.1: checks 37→42 (+14% count) plus 1 correctness fix (delimiter ranking) and 3 expectation fixes — correctness dimension improved and documented in CHANGELOG, suite re-run green |
| 16 | Ultimate fallback (≤60-word opener) | PASS | First paragraph = 58 words, contains what-it-is and "a wrong silent guess is worse than no answer" judgment sentence |

Second-order effects (rule 16 bonus): PASS — "Limits & Second-order Effects" covers stability-complacency, upstream dialect drift, and threshold-lowering reflexes.

Scan evidence: `grep -rEn "(sk-|ghp_|api[_-]?key\s*=\s*['\"][A-Za-z0-9])" .` → 0 hits; `grep -rn "hcac4735@agent.qq.com" README.md` → 1 hit.
