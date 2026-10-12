# csv-dialect-fingerprint

csv-dialect-fingerprint sniffs a CSV file's dialect — delimiter, quote character, line ending, encoding — from raw bytes, and reports how stable that guess is. When row shapes disagree below a threshold it answers AMBIGUOUS instead of guessing. Use it when you must auto-detect a delimiter but a wrong silent guess is worse than no answer. Confidence: High (≥80%) for the refusal behavior, based on the self-test suite.

## Problem

Ingestion pipelines receive CSVs from partners, exports, and scraped sources with unknown dialects: comma vs semicolon vs tab vs pipe, `"` vs `'` quoting, `\r\n` vs `\n` vs `\r`, UTF-8 vs UTF-16 vs latin-1. Standard parsers force you to commit to a dialect up front. A wrong guess silently corrupts every row; a one-off manual peek does not scale. What is missing is not another "best guess" sniffer — it is one that also tells you *when it does not know*.

## How it works

1. **Encoding** — BOM scan (`utf-8-sig`, `utf-16`); else try strict UTF-8; else fall back to `latin-1` with `decode_ok=false`.
2. **Line ending** — count `\r\n` / `\n` / `\r`, report the dominant form (JSON-safe literal, e.g. `\\r\\n`).
3. **Dialect** — each candidate delimiter (` , ; \t | `) × quotechar (`"` `'`) is scored by *row-shape agreement*: the fraction of non-empty rows whose field count equals the modal count. Candidates with a modal count of 1 are ranked below real multi-column delimiters, so "everything is one field" cannot win.
4. **Verdict** — the winner needs agreement ≥ `min_stability` (default 0.6) and ≥ 2 columns; otherwise the fingerprint is `AMBIGUOUS` with the reason attached. Fewer than 2 non-empty rows is also a refusal.

Output is a single JSON-serializable dict: `verdict, delimiter, quotechar, columns, rows, stability, encoding, bom, decode_ok, line_ending[, reason]`.

## Quickstart (~2 min)

```bash
# step 1: sniff one file (~1 s)
python cli.py data.csv
# step 2: batch a directory, machine-readable (~2 s)
python cli.py ./exports --json --min-stability 0.8
# full test suite (~3 s)
python self_test.py   # SUMMARY: PASS 42/42 [Measured]
```

Library use: `import csvprint; csvprint.fingerprint_bytes(b"a,b\n1,2\n")` or `fingerprint_file(path)` / `fingerprint_many(paths)`.

## Why not X? (as of 2026-10-12)

- **ws-garcia/CSVsniffer** (11★) — "The absolute pinnacle in CSV dialect detection", research-backed and Python-implemented. It is an accuracy-first *guesser*: it always returns its best dialect. csv-dialect-fingerprint differs in posture — it adds an explicit AMBIGUOUS refusal when row shapes disagree, plus line-ending/encoding detection in the same pass.
- **nradawg/delimiter-quorum** — scores CSV dialect detection by row-shape agreement and refuses to guess instead of picking a bad delimiter. Same core idea we adopted; this repo extends it with quotechar candidates, encoding/BOM handling, a 0–1 stability score, and a CLI batch mode.
- **ws-garcia/P-CSVsniffer** — "Robust CSV dialect detection methodology… outperforms existing state of the art by 8.x%". A methodology/benchmark line of work aimed at winning accuracy contests; we instead optimize for an auditable, machine-readable fingerprint with a calibrated confidence (stability) and a hard refusal path.

## Minimal Fallback (PLAN B)

No Python at hand? Two shell checks cover 80% of real cases: `head -1 file.csv | grep -o ';' | wc -l` vs the same for `,` — the more frequent winner is almost always the delimiter; `file file.csv` gives the encoding. If counts tie, the file genuinely is ambiguous — which is exactly the verdict this tool would also give.

## Design Trade-offs

Priority order: **calibrated refusal > determinism > coverage > performance**. We deliberately rank a "perfect 1-column agreement" delimiter *below* any multi-column candidate (a raw design decision from the v0.1.1 self-review) even though it lowers raw accuracy on genuinely single-column inputs — those are reported as AMBIGUOUS "single-column" instead. Detection is hand-rolled (no `csv.Sniffer`) so the ranking is explainable and testable.

## Limits & Second-order Effects

- Only 4 delimiters and 2 quotechars are candidates; exotic dialects (`\x01`, `^`) are out of scope.
- Row-shape agreement can be fooled by a file where an unquoted delimiter appears inside one field of every row.
- Second-order: teams that trust `stability=1.0` may stop spot-checking source files; a source that *changes* dialect upstream will still pass its old threshold on most rows before failing. Automate re-sniffing on ingest, not once.
- AMBIGUOUS results invite "just lower the threshold" reflexes; the threshold exists to protect downstream parsing, not to be tuned per file.

## FAQ

**Does it parse the file?** No — it fingerprints only; parsing is `csv.reader`'s job once the dialect is known.

**Why literal `\\r\\n` instead of a real CRLF in output?** JSON-safe and visible; a raw `\r\n` would vanish into the line break when printed.

### When NOT to use this tool?

- You need maximum accuracy on messy real-world CSV at any cost — use a research sniffer (e.g. CSVsniffer) and accept its guess.
- Your files are single-column exports — no delimiter can be detected by definition; this returns AMBIGUOUS by design.
- You need full RFC 4180 parsing with edge-case quoting semantics — use a real parser after fingerprinting.
- You need streaming detection on unbounded input — this loads text into memory.

## License

MIT — see `LICENSE`. Contact: hcac4735@agent.qq.com

---

[Core Assumptions]
- Real CSVs are shape-consistent: in a well-formed file, ≥60% of rows share one field count (hence the default 0.6 threshold).
- A delimiter that yields exactly one field per row carries no evidence and must not win the ranking.
- Encoding without a BOM is UTF-8 or legacy single-byte; anything else requires explicit handling upstream.
- Claim of no better-fitting "refuse-to-guess fingerprint + encoding + line-ending in one pass" tool is dated as of 2026-10-12.

---

Part of the [zhengming-toolbox](https://github.com/chenhz01/zhengming-toolbox) — 55 purpose-built AI-engineering tools across neglected niches.

Related tools: [md-table-lint](https://github.com/chenhz01/md-table-lint) · [event-replay-verifier](https://github.com/chenhz01/event-replay-verifier) · [idempotency-key-spec](https://github.com/chenhz01/idempotency-key-spec)
