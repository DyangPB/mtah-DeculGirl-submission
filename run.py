#!/usr/bin/env python3
"""One command that produces the submission file.

    python run.py                        # the real pipeline
    python run.py --placeholder          # empty submission, to test the chain
    python run.py --window 25            # change the baseline configuration

Writes ``results/DeculGirl.csv`` with exactly 199,319 data rows.

This is the entry point everything goes through. If you change how the
pipeline works, **do not change this command** -- change the contents of
``src/deculgirl/submit.py`` instead. Reproducibility is a grading requirement,
and one command that never changes is the cheapest way to protect it.

WARNING about ``--placeholder``: the file it produces **passes validation but
scores 0.0000**. Never submit it. It exists only to test the chain before the
data bundle is present -- which is why it has to be requested explicitly
instead of being the default behaviour. If the data is not found, this command
fails clearly instead of silently giving you an empty file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Windows: the default console code page (cp1252) cannot print non-ASCII
# characters and will CRASH in the middle of the pipeline. Force UTF-8 here so
# this trivial mistake never kills a long-running process.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from deculgirl import N_VIDEO_FRAMES  # noqa: E402
from deculgirl.submit import (  # noqa: E402
    DEFAULT_DATA_DIR,
    DEFAULT_WINDOW,
    build_labels,
    build_placeholder,
    write_submission,
)

OUT = ROOT / "results" / "DeculGirl.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="write an empty submission (all 'X'). Its score is 0.0000. "
             "Only for testing the chain without data",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW,
        help=f"half-width of the majority-voting window, in frames (default: {DEFAULT_WINDOW})",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"location of the match bundle (default: {DEFAULT_DATA_DIR})",
    )
    args = parser.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)

    try:
        labels = (
            build_placeholder()
            if args.placeholder
            else build_labels(data_dir=args.data_dir, window=args.window)
        )
    except (FileNotFoundError, IOError, OSError) as error:
        print(f"\nFAILED to build labels:\n\n{error}\n", file=sys.stderr)
        print(
            "If you only want to test that the chain is connected, and the "
            "data bundle is not there yet:\n\n"
            "    python run.py --placeholder\n\n"
            "The file produced will be valid but score 0.0000.\n",
            file=sys.stderr,
        )
        return 1

    if len(labels) != N_VIDEO_FRAMES:
        print(
            f"build_labels() returned {len(labels)} labels, "
            f"expected {N_VIDEO_FRAMES}.",
            file=sys.stderr,
        )
        return 1

    write_submission(labels, OUT)

    print(f"\nwritten: {OUT.relative_to(ROOT)}")
    print(f"rows   : {len(labels)}")
    if args.placeholder:
        print("\n  WARNING: PLACEHOLDER -- all 'X'. Valid, but its score is 0.0000.")
        print("           Do not submit this.")
    print("\nnext step:  python tools/gate0.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
