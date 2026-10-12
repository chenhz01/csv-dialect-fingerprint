"""CLI for csv-dialect-fingerprint."""
import argparse
import json
import os
import sys

import csvprint


def main(argv=None):
    ap = argparse.ArgumentParser(prog="csv-dialect-fingerprint",
                                 description="Sniff CSV dialect (delimiter/quote/line-ending/encoding) and score fingerprint stability; refuses to guess below threshold.")
    ap.add_argument("paths", nargs="+", help="CSV files or directories")
    ap.add_argument("--min-stability", type=float, default=0.6,
                    help="minimum row-shape agreement to call a dialect (default 0.6)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    files = []
    for p in args.paths:
        if os.path.isdir(p):
            files.extend(os.path.join(p, f) for f in sorted(os.listdir(p))
                         if f.lower().endswith((".csv", ".tsv", ".txt", ".dat")))
        elif os.path.exists(p):
            files.append(p)
        else:
            print("error: path not found: %s" % p, file=sys.stderr)
            return 2
    if not files:
        print("error: no CSV files found", file=sys.stderr)
        return 2

    fps = csvprint.fingerprint_many(files, args.min_stability)
    if args.json:
        print(json.dumps(fps, indent=2, ensure_ascii=False))
    else:
        for fp in fps:
            print("%-9s %s" % (fp["verdict"], fp["path"]))
            print("  delimiter=%r quotechar=%r columns=%s rows=%s stability=%s"
                  % (fp["delimiter"], fp["quotechar"], fp["columns"], fp["rows"], fp["stability"]))
            print("  encoding=%s bom=%s line_ending=%s" % (fp["encoding"], fp["bom"], fp["line_ending"]))
            if "reason" in fp:
                print("  note: %s" % fp["reason"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
