#!/usr/bin/env python3
"""Show the 5 minutes of example answers -- so it is clear what has to be guessed.

    python tools/show_gt.py

This is the ONLY example of answers we have: the first 5 minutes of play, with
the correct answers. It lists the 21 segments in it -- 17 possessions and 4
dead-ball blocks.

Why it exists: the work is not "building a model". The work is to look at the
transitions into `D` in this table, open the tracking file around those frames,
and answer "why is this frame a dead ball?" -- then write the answer down as a
rule that can be coded.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Windows: the default console (cp1252) cannot print non-ASCII characters.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parents[1]
GT = (ROOT / "third_party" / "mtah2027" / "evaluation" / "gt"
      / "BAR-ATH_possession_gt_public.csv")

FPS = 25
LABEL_TEXT = {"H": "H  Barcelona in possession", "A": "A  Athletic in possession", "D": "D  DEAD BALL"}


def main() -> int:
    if not GT.exists():
        print(
            "The example-answer file is not present yet.\n\n"
            "  python tools/fetch_official.py\n",
            file=sys.stderr,
        )
        return 1

    df = pd.read_csv(GT, dtype={"label": str})

    graded = df[df["label"] != "X"]
    if graded.empty:
        print("the example-answer file contains no graded frames.", file=sys.stderr)
        return 1

    first_frame = int(graded["frame"].iloc[0])
    last_frame = int(graded["frame"].iloc[-1])

    window = df[(df["frame"] >= first_frame) & (df["frame"] <= last_frame)]
    frames = window["frame"].to_numpy()
    labels = window["label"].to_numpy()

    window_seconds = len(labels) / FPS
    print()
    print(f"Example answers: frame {first_frame:,} to {last_frame:,}")
    print(f"  {len(labels):,} graded frames  =  {window_seconds:.0f} seconds  =  {window_seconds/60:.1f} minutes")
    print(f"  outside this window, every answer is 'X' (not graded)")
    print()
    print("  #   label  start frame   end frame      length   start time")
    print("  --- ----- -------------  -------------  -------  -----------")

    segments: list[tuple[str, int, int, int]] = []
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            segments.append((labels[start], int(frames[start]), int(frames[i - 1]), i - start))
            start = i

    for number, (label, seg_start, seg_end, length) in enumerate(segments, start=1):
        seconds = seg_start / FPS
        minutes = int(seconds // 60)
        remainder = seconds - minutes * 60
        marker = " <<<" if label == "D" else ""
        print(
            f"  {number:>3} {LABEL_TEXT[label]:<27} {seg_start:>7,}  {seg_end:>13,}"
            f"  {length/FPS:>6.1f}s  {minutes:>2}:{remainder:04.1f}{marker}"
        )

    possessions = [s for s in segments if s[0] in ("H", "A")]
    dead = [s for s in segments if s[0] == "D"]

    print()
    print(f"  {len(segments)} segments: {len(possessions)} possessions and {len(dead)} dead-ball blocks.")
    print(f"  Average {sum(s[3] for s in possessions)/len(possessions)/FPS:.1f} seconds per possession."
          f"  The shortest is {min(s[3] for s in possessions)/FPS:.2f} seconds.")
    print()
    print("  The four blocks marked <<< are the question. For each of them:")
    print("    1. Open data/tactical/BAR-ATH_tactical_atd.txt around that frame.")
    print("    2. Ask: what is different there? Ball missing? Ball still? Players stopped?")
    print("    3. Write the answer in docs/possession-rules.md as a rule that can be coded.")
    print()
    print("  If you can explain why those 4 blocks are 'D' without watching the video and")
    print("  without recalling the match, you have done the domain work.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
