#!/usr/bin/env python3
"""Fetch the organisers' official repo, pinned to a single commit.

    python tools/fetch_official.py
    python tools/fetch_official.py --force     # delete, then fetch again

The result goes into ``third_party/mtah2027/`` (gitignored, fetched again when
needed).

WHY IT IS PINNED
----------------
``evaluation/possession_metrics.py`` **is** the metric specification.
``EVALUATION.md`` says so itself:

    "If this document and that file ever disagree, the file is right."

If upstream changes that file mid-competition, your local numbers change
without you noticing -- and you end up chasing ghosts. The pin prevents that:
every run, on every machine, gets exactly the same scorer code.

If you do want to pull a newer version, change ``PINNED_SHA`` below and write
down the reason in ``docs/decisions.md``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
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
DEST = ROOT / "third_party" / "mtah2027"

UPSTREAM = "https://github.com/metrica-sports/more-than-a-hack-2027.git"

#: The pinned commit. Taken on 24 October 2026 -- the latest commit at the
#: time, "Clarifying the guidelines for annotating the provided video."
PINNED_SHA = "f8f2629ff1e0985f81d7e59d8413678514ee1530"


def _rmtree(path: Path) -> None:
    """Delete a folder that may contain read-only files (git objects on Windows)."""

    def on_error(func, target, _exc_info):  # type: ignore[no-untyped-def]
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:  # noqa: BLE001
            pass

    shutil.rmtree(path, onerror=on_error)


def _git(args: list[str], cwd: Path | None = None) -> None:
    printable = " ".join(args)
    print(f"  $ git {printable}")
    subprocess.run(["git", *args], cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--force",
        action="store_true",
        help="delete third_party/mtah2027 first, then fetch again",
    )
    args = parser.parse_args()

    if shutil.which("git") is None:
        print("git is not on PATH. Install Git first.", file=sys.stderr)
        return 1

    if DEST.exists():
        if not args.force:
            print(f"already present: {DEST.relative_to(ROOT)}")
            print("fetch again with:  python tools/fetch_official.py --force")
            return 0
        print(f"deleting {DEST.relative_to(ROOT)} ...")
        _rmtree(DEST)

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True)

    print(f"fetching {UPSTREAM}")
    print(f"       @ {PINNED_SHA}\n")

    try:
        _git(["init", "--quiet"], cwd=DEST)
        _git(["remote", "add", "origin", UPSTREAM], cwd=DEST)
        # --depth 1 + a direct SHA: fast, and pins exactly one commit.
        _git(["fetch", "--quiet", "--depth", "1", "origin", PINNED_SHA], cwd=DEST)
        _git(["checkout", "--quiet", "FETCH_HEAD"], cwd=DEST)
    except subprocess.CalledProcessError:
        print(
            "\nfailed to fetch the official repo.\n"
            "  - check your internet connection\n"
            "  - check that git can reach github.com\n"
            "  - then run it again\n"
            "The half-finished folder is left in place so it can be inspected; "
            "use --force to clean it up.",
            file=sys.stderr,
        )
        return 1

    scorer = DEST / "evaluation" / "run_evaluation.py"
    gt = DEST / "evaluation" / "gt" / "BAR-ATH_possession_gt_public.csv"
    if not scorer.exists() or not gt.exists():
        print(
            "\nthe repo was fetched but the key files are missing "
            f"({scorer.name}, {gt.name}).\n"
            "Upstream may have changed. Check by hand before continuing.",
            file=sys.stderr,
        )
        return 1

    print(f"\nok: {DEST.relative_to(ROOT)}  @ {PINNED_SHA[:8]}")
    print("next step:  python run.py")
    print("then:       python tools/gate0.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
