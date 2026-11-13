#!/usr/bin/env python3
"""Show the tracking file for a few frames, in a human-readable form.

    python tools/show_frames.py 12840 12900

The file `BAR-ATH_tactical_atd.txt` is 199,319 lines of numbers that are hard to
read directly. This script turns it into a table: for each frame, where the ball
is, how fast it is moving, how far it moved since the previous frame, and which
player is closest.

Its purpose is to answer "why is this frame a dead ball?" without opening the
video. Just look: is the ball still? Have the players stopped? Is the ball
missing?
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Windows: the default console (cp1252) cannot print non-ASCII characters.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parents[1]
DATA_TACTICAL = ROOT / "data" / "tactical"
RAW = DATA_TACTICAL / "BAR-ATH_tactical_atd.txt"
META = DATA_TACTICAL / "BAR-ATH_tactical_atd.xml"

FPS = 25
PITCH = (105.3, 68.0)      # metres, same as the official repo's games.py
MISSING = "N"              # first letter of "NaN"
HOME, AWAY = 0, 1


def team_of_each_track(meta_path: Path) -> list[int]:
    """For each track slot: 0 for the home team, 1 for the away team.

    Read exactly like `starter/baseline.py` in the official repo: the first
    <Team> element in the file is the home team (FIFA/EPTS convention).
    """
    root = ET.parse(meta_path).getroot()
    ids = [t.get("id") for t in root.iter("Team")]
    if len(ids) != 2:
        raise ValueError(f"{meta_path}: expected 2 teams, found {len(ids)}")
    home_id = ids[0]
    return [HOME if p.get("teamId") == home_id else AWAY for p in root.iter("Player")]


def parse_group(text: str) -> tuple[float, float, float] | None:
    """'x,y,speed' -> (x, y, speed). None if the group is empty/NaN."""
    if not text or text[0] == MISSING:
        return None
    pieces = text.split(",")
    if len(pieces) < 2:
        return None
    try:
        x = float(pieces[0])
        y = float(pieces[1])
        speed = float(pieces[2]) if len(pieces) > 2 else 0.0
    except ValueError:
        return None
    return x, y, speed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("start", type=int, help="first frame (0-based, as in the submission)")
    parser.add_argument("end", type=int, nargs="?", default=None,
                        help="last frame (default: 60 frames after 'start')")
    args = parser.parse_args()

    first = args.start
    last = args.end if args.end is not None else first + 59

    if not RAW.exists():
        print(
            f"Tracking file not found at:\n  {RAW}\n\n"
            "Use the exact original file name and put it in that folder.\n",
            file=sys.stderr,
        )
        return 1
    if not META.exists():
        print(f"Metadata file not found at:\n  {META}\n", file=sys.stderr)
        return 1

    teams = team_of_each_track(META)
    length, width = PITCH
    team_names = {HOME: "Barcelona", AWAY: "Athletic"}

    print()
    print(f"Frames {first:,} to {last:,}   ({first/FPS:.1f}s to {last/FPS:.1f}s)")
    print("Frames in the file are 1-based, so reading starts at line", first + 1)
    print()
    print("  frame   ball_x  ball_y  speed   moved   n   nearest player")
    print("  ------  ------  ------  ------  ------  ---  ----------------------")

    previous: tuple[float, float] | None = None
    rows_printed = 0

    with RAW.open() as handle:
        for line in handle:
            parts = line.split(":")
            if len(parts) != 3:
                continue
            try:
                id_frame = int(parts[0])
            except ValueError:
                continue

            if id_frame > last + 1:
                break

            ball = parse_group(parts[2])
            frame = id_frame - 1     # id_frame is 1-based -> video frame is 0-based

            if first <= frame <= last:
                if ball is None:
                    print(f"  {frame:>6,}  {'--':>6}  {'--':>6}  {'--':>6}  {'--':>6}  "
                          f"{'n/a':>3}  BALL NOT DETECTED")
                    previous = None
                    rows_printed += 1
                    continue

                bx, by, speed = ball
                mx = bx * length
                my = by * width

                if previous is None:
                    moved = "--"
                else:
                    px, py = previous
                    d = ((bx - px) * length) ** 2 + ((by - py) * width) ** 2
                    moved = f"{d ** 0.5:.2f}"

                players = parts[1].split(";")
                nearest_distance = None
                nearest_team = None
                nearest_slot = None
                tracked = 0

                for slot, group in enumerate(players):
                    p = parse_group(group)
                    if p is None:
                        continue
                    tracked += 1
                    px_ = p[0] * length
                    py_ = p[1] * width
                    distance = ((px_ - mx) ** 2 + (py_ - my) ** 2) ** 0.5
                    if nearest_distance is None or distance < nearest_distance:
                        nearest_distance = distance
                        nearest_team = teams[slot] if slot < len(teams) else None
                        nearest_slot = slot + 1

                if nearest_distance is None:
                    info = "no player detected"
                else:
                    team_name = team_names.get(nearest_team, "?")
                    info = f"{team_name} (slot {nearest_slot}, {nearest_distance:.1f} m)"

                print(f"  {frame:>6,}  {bx:>6.3f}  {by:>6.3f}  {speed:>6.2f}  "
                      f"{moved:>6}  {tracked:>3}  {info}")
                previous = (bx, by)
                rows_printed += 1

    print()
    if rows_printed == 0:
        print("  No frame in that range could be read from the file.")
        print("  How many lines does the file have? Check first -- it should be 199,319.")
    else:
        print("  How to read it: 'moved' is how many metres the ball travelled since the previous frame.")
        print("  A ball that stays still (moved 0.00 repeatedly) almost always means a dead ball.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
