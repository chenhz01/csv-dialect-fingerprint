"""Self-test for csv-dialect-fingerprint: functional / error-path / extreme-edge."""
from __future__ import annotations

import json
import os
import sys
import tempfile

import csvprint

_results = []


def record(family, name, ok, detail=""):
    _results.append((family, name, "PASS" if ok else "FAIL", detail))


def w(tmp, name, data):
    p = os.path.join(tmp, name)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(p, mode, **({} if isinstance(data, bytes) else {"encoding": "utf-8"})) as f:
        f.write(data)
    return p


# ---------------------------------------------------------------- functional

def t_functional(tmp):
    fp = csvprint.fingerprint_bytes(b"a,b,c\n1,2,3\n4,5,6\n")
    record("functional", "comma csv -> OK , 3 cols stability 1.0",
           fp["verdict"] == "OK" and fp["delimiter"] == "," and fp["columns"] == 3
           and fp["stability"] == 1.0, json.dumps(fp))

    fp = csvprint.fingerprint_bytes(b"a;b;c\n1;2;3\n4;5;6\n")
    record("functional", "semicolon detected", fp["delimiter"] == ";")

    fp = csvprint.fingerprint_bytes(b"a\tb\tc\n1\t2\t3\n")
    record("functional", "tab detected", fp["delimiter"] == "\t")

    fp = csvprint.fingerprint_bytes(b"a|b|c\n1|2|3\n")
    record("functional", "pipe detected", fp["delimiter"] == "|")

    fp = csvprint.fingerprint_bytes(b'name,note\n"x,1",has comma\n"y",plain\n')
    record("functional", "embedded comma inside quotes, 2 cols stable",
           fp["verdict"] == "OK" and fp["delimiter"] == "," and fp["columns"] == 2)

    fp = csvprint.fingerprint_bytes(b"name;note\n'x;1';semi inside\n'y';plain\n")
    record("functional", "single-quote quotechar with semicolon delim",
           fp["delimiter"] == ";" and fp["quotechar"] == "'")

    fp = csvprint.fingerprint_bytes(b"a,b\n1,2\r\n3,4\r\n")
    record("functional", "CRLF line ending reported", fp["line_ending"] == "\\r\\n", fp["line_ending"])

    fp = csvprint.fingerprint_bytes(b"a,b\n1,2\n3,4\n")
    record("functional", "LF line ending reported", fp["line_ending"] == "\\n")

    fp = csvprint.fingerprint_bytes(b"\xef\xbb\xbfa,b\n1,2\n")
    record("functional", "UTF-8 BOM detected", fp["encoding"] == "utf-8-sig" and fp["bom"] is True)

    fp = csvprint.fingerprint_bytes("naïve,café\nok,ok2\n".encode("utf-8"))
    record("functional", "utf-8 non-bom detected", fp["encoding"] == "utf-8")

    fp = csvprint.fingerprint_bytes(b"a,b,c\n1,2,3\n9,9\n")
    record("functional", "ragged rows -> stability < 1, still OK above threshold",
           fp["verdict"] == "OK" and fp["stability"] < 1.0)

    fp = csvprint.fingerprint_bytes(b"a,b\n1,2\n3\n4,5,6,7\n")
    record("functional", "chaotic shapes -> AMBIGUOUS below threshold",
           fp["verdict"] == "AMBIGUOUS" and "threshold" in fp["reason"])

    fp = csvprint.fingerprint_bytes(b"onlyoneheader\nsolo\n", min_stability=0.6)
    record("functional", "single-column -> AMBIGUOUS with reason",
           fp["verdict"] == "AMBIGUOUS" and "single-column" in fp["reason"])

    fp = csvprint.fingerprint_bytes(b"a,b\n1,2\n")
    record("functional", "fingerprint JSON-serializable", json.dumps(fp) and fp["rows"] == 2)

    fp = csvprint.fingerprint_bytes("名字,城市\n1,2\n".encode("utf-16"))
    record("functional", "utf-16 BOM detected", fp["encoding"] == "utf-16" and fp["bom"] is True)

    fp = csvprint.sniff("a:b\n1:2\n", delims=[":"])
    record("functional", "sniff custom delim override", fp["delimiter"] == ":" and fp["verdict"] == "OK")

    fp = csvprint.fingerprint_file(w(tmp, "f.csv", b"x,y\n1,2\n"))
    record("functional", "fingerprint_file adds path", fp["path"].endswith("f.csv"))


# ---------------------------------------------------------------- error paths

def t_error_paths(tmp):
    fp = csvprint.fingerprint_bytes(b"")
    record("error", "empty file -> AMBIGUOUS not crash", fp["verdict"] == "AMBIGUOUS")

    fp = csvprint.fingerprint_bytes(b"\n\n\n")
    record("error", "blank lines only -> AMBIGUOUS", fp["verdict"] == "AMBIGUOUS")

    fp = csvprint.fingerprint_bytes(b"singleline")
    record("error", "one row -> AMBIGUOUS needs 2", fp["verdict"] == "AMBIGUOUS"
           and "2 non-empty rows" in fp["reason"])

    fp = csvprint.fingerprint_bytes(b"\x00\x01\x02\xff\xfe\x9c\n\x00\x9c\n")
    record("error", "binary garbage -> latin-1 fallback, no crash", fp["encoding"] == "latin-1")

    fp = csvprint.fingerprint_bytes(b'a,b\n"unterminated,2\n3,4\n')
    record("error", "unterminated quote tolerated", fp["verdict"] in ("OK", "AMBIGUOUS"))

    fp = csvprint.fingerprint_bytes(b"a,b,c\x00\n1,2,3\x00\n")
    record("error", "NUL bytes decoded via replace", isinstance(fp["rows"], int))

    fp = csvprint.sniff("")
    record("error", "sniff empty text -> AMBIGUOUS", fp["verdict"] == "AMBIGUOUS")

    fp = csvprint.fingerprint_bytes(b"a,b\n1,2\n3,4\n", min_stability=2.0)
    record("error", "impossible threshold -> AMBIGUOUS", fp["verdict"] == "AMBIGUOUS")


# ---------------------------------------------------------------- extreme edges

def t_extreme_edges(tmp):
    big = b"id,name,val\n" + b"".join(b"%d,cell%d,%f\n" % (i, i, i * 1.5) for i in range(5000))
    fp = csvprint.fingerprint_bytes(big)
    record("edge", "5000 rows -> OK , 3 cols", fp["verdict"] == "OK" and fp["rows"] == 5001
           and fp["delimiter"] == ",")

    wide = b",".join(b"h%d" % i for i in range(200)) + b"\n" + b",".join(b"v%d" % i for i in range(200)) + b"\n"
    fp = csvprint.fingerprint_bytes(wide)
    record("edge", "200 columns detected", fp["columns"] == 200)

    uni = "名字,城市\n张三,北京\n李四,上海\n".encode("utf-8")
    fp = csvprint.fingerprint_bytes(uni)
    record("edge", "unicode content, comma still detected", fp["delimiter"] == ",")

    quoted = b'"a","b"\n"1","2"\n"3","4"\n'
    fp = csvprint.fingerprint_bytes(quoted)
    record("edge", "all-quoted fields parsed", fp["verdict"] == "OK" and fp["columns"] == 2)

    mixed = b"a,b\n1,2\r\n3,4\n5,6\r\n"
    fp = csvprint.fingerprint_bytes(mixed)
    record("edge", "mixed endings reported as dominant", fp["line_ending"] == "\\r\\n")

    fp = csvprint.fingerprint_bytes(b"a,b\r1,2\r3,4\r")
    record("edge", "old-Mac CR endings reported", fp["line_ending"] == "\\r")

    fp = csvprint.fingerprint_bytes(b"a,b,c\n1,2,3\n1,2,3\n1,2\n", min_stability=0.99)
    record("edge", "min_stability=0.99 rejects 0.8 agreement", fp["verdict"] == "AMBIGUOUS")

    paths = [w(tmp, "m1.csv", b"a,b\n1,2\n"), w(tmp, "m2.csv", b"x;y\n1;2\n")]
    many = csvprint.fingerprint_many(paths)
    record("edge", "fingerprint_many returns 2 with paths",
           len(many) == 2 and many[0]["delimiter"] == "," and many[1]["delimiter"] == ";")

    fp = csvprint.fingerprint_bytes(b"a;b\n1,2,3\n4;5\n")
    record("edge", "delim/commas conflict resolved by agreement",
           fp["verdict"] in ("OK", "AMBIGUOUS") and fp["stability"] is not None)

    fp = csvprint.fingerprint_bytes(b"a,b\n1,2")
    record("edge", "no trailing newline handled", fp["rows"] == 2)

    p = w(tmp, "u.csv", "name,note\ncafé,ok\nnaïve,ok\n".encode("utf-8"))
    fp = csvprint.fingerprint_file(p)
    record("edge", "fingerprint_file on utf-8 file OK", fp["verdict"] == "OK")

    import cli as cli_mod
    import io
    from contextlib import redirect_stdout
    good = w(tmp, "g.csv", b"a,b\n1,2\n3,4\n")
    def run_cli(*argv):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = cli_mod.main(list(argv))
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 2
        return rc, buf.getvalue()
    rc, _ = run_cli(good)
    record("edge", "cli good file -> 0", rc == 0)
    rc, out = run_cli(good, "--json")
    record("edge", "cli --json emits list", rc == 0 and json.loads(out)[0]["verdict"] == "OK")
    rc, _ = run_cli(os.path.dirname(good))
    record("edge", "cli directory batch works", rc == 0)
    rc, _ = run_cli("__missing__.csv")
    record("edge", "cli missing path -> 2", rc == 2)

    d = os.path.join(tmp, "emptydir")
    os.makedirs(d, exist_ok=True)
    rc, _ = run_cli(d)
    record("edge", "cli dir with no csvs -> 2", rc == 2)

    ragged = b"a,b,c\n1,2,3\n1,2,3\n1,2,3\n1,2\n"
    fp = csvprint.fingerprint_bytes(ragged)
    record("edge", "4-of-5 agreement = 0.8 above default threshold",
           fp["verdict"] == "OK" and fp["stability"] == 0.8)


def main():
    tmp = tempfile.mkdtemp(prefix="csvprint_test_")
    try:
        t_functional(tmp)
        t_error_paths(tmp)
        t_extreme_edges(tmp)
    finally:
        for root, dirs, files in os.walk(tmp, topdown=False):
            for f in files:
                try:
                    os.unlink(os.path.join(root, f))
                except OSError:
                    pass
            try:
                os.rmdir(root)
            except OSError:
                pass
    fails = [r for r in _results if r[2] == "FAIL"]
    for fam, name, status, detail in _results:
        print("[%s] %-10s %s%s" % (status, fam, name, (" | " + detail) if detail else ""))
    print("\n%d checks, %d failed" % (len(_results), len(fails)))
    print("SUMMARY: PASS %d/%d" % (len(_results) - len(fails), len(_results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
