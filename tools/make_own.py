#!/usr/bin/env python3
"""Write our own variant: results/DeculGirl_own.csv  (does not touch results/DeculGirl.csv).

    python tools/make_own.py
    python tools/make_own.py --layers out still          # switch dead-ball layers on/off
    python tools/make_own.py --out results/other.csv

Then check it:  python tools/gate0.py --file results/DeculGirl_own.csv
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deculgirl import GRADED_RUNS  # noqa: E402
from deculgirl.features.dead_ball import LAYERS  # noqa: E402
from deculgirl.own import build_labels_own  # noqa: E402
from deculgirl.submit import write_submission  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--layers", nargs="*", default=list(LAYERS), choices=LAYERS)
    ap.add_argument("--out", default=str(ROOT / "results" / "DeculGirl_own.csv"))
    args = ap.parse_args()

    labels = build_labels_own(tuple(args.layers))
    write_submission(labels, args.out)

    graded = [l for a, b in GRADED_RUNS for l in labels[a:b]]
    c = Counter(graded)
    n = len(graded)
    print(f"layers: {args.layers}")
    print("graded frames:", {k: f"{c[k]:,} ({100*c[k]/n:.1f}%)" for k in "HADX"})
    for half, (a, b) in enumerate(GRADED_RUNS, 1):
        seg = labels[a:b]
        runs = 1 + int((seg[1:] != seg[:-1]).sum())
        print(f"half {half}: {runs} label runs")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
