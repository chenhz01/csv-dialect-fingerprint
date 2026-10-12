"""csv-dialect-fingerprint: sniff a CSV's dialect (delimiter, quotechar, line
ending, encoding) from bytes, and score how stable that fingerprint is.

Method: candidate delimiters (`,` `;` `\\t` `|`) are each scored by row-shape
agreement — the fraction of rows whose field count equals the modal count.
The winner needs agreement >= min_stability, otherwise the fingerprint is
reported as AMBIGUOUS rather than guessed.
"""
from __future__ import annotations

import csv
import io
import json

CANDIDATE_DELIMS = [",", ";", "\t", "|"]
CANDIDATE_QUOTES = ['"', "'"]
BOMS = (("utf-8-sig", b"\xef\xbb\xbf"), ("utf-16", b"\xff\xfe"), ("utf-16", b"\xfe\xff"))


def detect_encoding(raw: bytes) -> dict:
    for enc, bom in BOMS:
        if raw.startswith(bom):
            return {"encoding": enc, "bom": True, "decode_ok": True}
    try:
        raw.decode("utf-8")
        return {"encoding": "utf-8", "bom": False, "decode_ok": True}
    except UnicodeDecodeError:
        return {"encoding": "latin-1", "bom": False, "decode_ok": False}


def decode(raw: bytes) -> tuple:
    enc = detect_encoding(raw)
    text = raw.decode(enc["encoding"], errors="replace")
    return text, enc


def detect_line_ending(text: str) -> str:
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    best = max(crlf, lf, cr)
    if best == 0:
        return "none"
    if crlf >= lf and crlf >= cr:
        return "\\r\\n"
    return "\\n" if lf >= cr else "\\r"


def split_lines(text: str):
    lines = [ln for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _score_delimiter(lines: list, delim: str, quotechar: str) -> tuple:
    """Returns (modal_count, stability, rows_parsed)."""
    counts = []
    for ln in lines:
        if not ln.strip():
            continue
        try:
            row = next(csv.reader(io.StringIO(ln), delimiter=delim, quotechar=quotechar))
            counts.append(len(row))
        except (csv.Error, StopIteration):
            continue
    if not counts:
        return 0, 0.0, 0
    modal = max(set(counts), key=counts.count)
    stability = counts.count(modal) / len(counts)
    return modal, stability, len(counts)


def sniff(text: str, min_stability: float = 0.6, delims=None, quotes=None) -> dict:
    lines = split_lines(text)
    rows = [ln for ln in lines if ln.strip()]
    base = {"rows": len(rows)}
    if len(rows) < 2:
        return dict(base, delimiter=None, quotechar=None, columns=None,
                    stability=None, verdict="AMBIGUOUS",
                    reason="need >= 2 non-empty rows to compare shapes")
    best = None
    for q in (quotes or CANDIDATE_QUOTES):
        for d in (delims or CANDIDATE_DELIMS):
            modal, stability, nparsed = _score_delimiter(rows, d, q)
            cand = (stability, modal, nparsed, d, q)
            key = (modal >= 2, stability, modal, nparsed)
            if best is None or key > (best[1] >= 2, best[0], best[1], best[2]):
                best = cand
    stability, modal, nparsed, delim, quote = best
    if modal < 2:
        return dict(base, delimiter=None, quotechar=None, columns=modal,
                    stability=round(stability, 4), verdict="AMBIGUOUS",
                    reason="single-column data: delimiter undetectable")
    if stability < min_stability:
        return dict(base, delimiter=delim, quotechar=quote, columns=modal,
                    stability=round(stability, 4), verdict="AMBIGUOUS",
                    reason="best row-shape agreement %.2f below threshold %.2f"
                           % (stability, min_stability))
    return dict(base, delimiter=delim, quotechar=quote, columns=modal,
                stability=round(stability, 4), verdict="OK")


def fingerprint_bytes(raw: bytes, min_stability: float = 0.6) -> dict:
    text, enc = decode(raw)
    fp = sniff(text, min_stability)
    fp["encoding"] = enc["encoding"]
    fp["bom"] = enc["bom"]
    fp["decode_ok"] = enc["decode_ok"]
    fp["line_ending"] = detect_line_ending(text)
    order = ["verdict", "delimiter", "quotechar", "columns", "rows", "stability",
             "encoding", "bom", "decode_ok", "line_ending"]
    out = {k: fp.get(k) for k in order}
    for k in ("reason",):
        if k in fp:
            out[k] = fp[k]
    return out


def fingerprint_file(path: str, min_stability: float = 0.6) -> dict:
    with open(path, "rb") as f:
        fp = fingerprint_bytes(f.read(), min_stability)
    fp["path"] = path
    return fp


def fingerprint_many(paths: list, min_stability: float = 0.6) -> list:
    return [fingerprint_file(p, min_stability) for p in paths]
