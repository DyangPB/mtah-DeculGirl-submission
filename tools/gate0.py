#!/usr/bin/env python3
"""Validate and score a submission file, using the official tools.

    python tools/gate0.py
    python tools/gate0.py --file results/DeculGirl_v2.csv
    python tools/gate0.py --bootstrap 1000     # confidence interval

THIS GATE DOES NOT NEED THE MATCH DATA. The score is computed on the 5 minutes
of public ground truth that ship inside the official repo, so it can run from
the very first minute -- before the data bundle is downloaded.

WHAT IT DOES
  1. Runs ``evaluation/validate_submission.py`` -- **exactly the same check**
     that the official scorer runs. A file that fails here is scored zero if
     submitted.
  2. Runs ``evaluation/run_evaluation.py`` -- the official scorer.

A WARNING TO ALWAYS REMEMBER
  The numbers from this gate are computed on **17 possessions**. One missed
  possession moves spellF1 by about **6 points**. ``EVALUATION.md`` proves that
  tuning on this window picks the WRONG baseline: ``smooth125`` wins here
  (0.4242) but loses on the full match (0.2242).

  So: use this gate to verify that your pipeline is **correct** (frames
  aligned, file follows the contract, labels mean what you think they mean).
  Do not use it to choose between versions.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Windows: the default console (cp1252) cannot print non-ASCII characters and
# will crash. Force UTF-8 before anything is printed.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "third_party" / "mtah2027"
DEFAULT_FILE = ROOT / "results" / "DeculGirl.csv"


def _run(cmd: list[str], cwd: Path) -> int:
    pretty = " ".join(str(part) for part in cmd)
    print(f"  $ {pretty}\n", flush=True)
    return subprocess.run([str(part) for part in cmd], cwd=cwd).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--file",
        default=str(DEFAULT_FILE),
        help="submission file to check (default: results/DeculGirl.csv)",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=0,
        metavar="N",
        help="number of bootstrap draws for the confidence interval (e.g. 1000)",
    )
    args = parser.parse_args()

    if not (OFFICIAL / "evaluation" / "run_evaluation.py").exists():
        print(
            "The official repo is not present yet.\n\n  python tools/fetch_official.py\n",
            file=sys.stderr,
        )
        return 1

    submission = Path(args.file).resolve()
    if not submission.exists():
        print(
            f"Submission file not found: {submission}\n\n  python run.py\n",
            file=sys.stderr,
        )
        return 1

    # 1. Validation -- the exact same function the official scorer uses.
    print(f"=== 1/2  VALIDATION  {submission.name} ===\n")
    rc = _run(
        [sys.executable, "evaluation/validate_submission.py", str(submission)],
        cwd=OFFICIAL,
    )
    if rc != 0:
        print(
            "\nVALIDATION FAILED. This file would be scored ZERO if "
            "submitted.\nThe file contract is in SUBMISSION.md; the most common "
            "causes are an off-by-one at the start or end of the file, a "
            "missing header, and empty cells that should contain 'X'.",
            file=sys.stderr,
        )
        return rc

    # 2. Score. The scorer reads every *.csv in evaluation/results/.
    results_dir = OFFICIAL / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(submission, results_dir / submission.name)

    print("\n=== 2/2  SCORE  (5 minutes of public ground truth) ===\n")
    cmd = [sys.executable, "evaluation/run_evaluation.py"]
    if args.bootstrap:
        cmd += ["--bootstrap", str(args.bootstrap)]
    rc = _run(cmd, cwd=OFFICIAL)

    print(
        "\nThe floor to beat: spellF1 0.2433 on the full match "
        "(baseline_smooth50).\nThe numbers above come from 17 possessions -- 1 "
        "missed possession ~ 6 points. This is not a leaderboard."
    )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
