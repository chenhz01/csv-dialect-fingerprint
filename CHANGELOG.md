# Changelog

## v0.1.1 — 2026-10-12
- Fixed a real ranking bug in `csvprint.sniff`: candidate delimiters were compared by stability alone, so a pseudo-delimiter yielding perfect 1-field rows (e.g. `;` on a comma file) with stability 1.0 outranked the true delimiter and pushed results into "single-column AMBIGUOUS". Candidates with modal count ≥ 2 are now ranked first; ragged/chaotic/4-of-5-agreement cases resolve correctly.
- Self-test repaired and extended: 3 tests used double-escaped expectations for `line_ending` (`\\\\r\\\\n` vs the code's JSON-safe literal `\\r\\n`), 1 asserted a wrong row count. Added 5 cases (utf-16 BOM, custom `delims` override, old-Mac CR endings, `min_stability=0.99` rejection, `fingerprint_many`). 37 → 42 checks, `SUMMARY: PASS 42/42`.
- Documentation layer completed: README (Problem / How it works / Quickstart / why-not-X with anchors / Minimal Fallback / Trade-offs / Limits / FAQ), ALIGNMENT.md 16-item audit.

## v0.1.0 — 2026-10-11
- Initial implementation: encoding/BOM sniff, dominant line-ending detection, delimiter×quotechar scoring by row-shape agreement with `min_stability` refusal threshold, `fingerprint_bytes / fingerprint_file / fingerprint_many` API and `cli.py` (file or directory batch, `--json`, exit 2 on missing/empty inputs).
- Self-test suite (functional / error / extreme-edge tiers).
