"""Read the raw ATD tracking file into numpy arrays (and cache them).

Line format (see DATA.md and starter/baseline.py):

    <frame_id>:<slot>;<slot>;...:<ball>        each group is "x,y,speed", "NaN" if missing

Coordinates are normalised to 0-1 and are converted to metres here. ``frame_id``
counts from 1 in the file, submissions count from 0, so row ``i`` of every array
is ``video_frame`` ``i``.

The parsed arrays are cached next to the data (``data/`` is gitignored) so that
the 11-second parse is paid once.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .. import N_VIDEO_FRAMES

ROOT = Path(__file__).resolve().parents[3]
#: Same convention as the official repo and ``submit.py``: ``MTAH_DATA_DIR`` wins, otherwise ``data/``.
DATA_DIR = Path(os.environ.get("MTAH_DATA_DIR") or (ROOT / "data"))
DATA_TACTICAL = DATA_DIR / "tactical"
RAW = DATA_TACTICAL / "BAR-ATH_tactical_atd.txt"
META = DATA_TACTICAL / "BAR-ATH_tactical_atd.xml"
CACHE = DATA_DIR / "cache_tracking.npz"

PITCH = (105.3, 68.0)  # metres, same as the official repo's games.py
FPS = 25
HOME, AWAY = 0, 1


@dataclass(frozen=True)
class Tracking:
    ball: np.ndarray      # (N, 3) x_m, y_m, speed_m_s   -- NaN where the ball is not detected
    players: np.ndarray   # (N, S, 3) same, per track slot -- NaN where the slot is empty
    team: np.ndarray      # (S,) 0 = home, 1 = away

    @property
    def n_frames(self) -> int:
        return self.ball.shape[0]


def _team_of_each_slot(meta_path: Path) -> np.ndarray:
    root = ET.parse(meta_path).getroot()
    ids = [t.get("id") for t in root.iter("Team")]
    if len(ids) != 2:
        raise ValueError(f"{meta_path}: expected 2 teams, found {len(ids)}")
    return np.array(
        [HOME if p.get("teamId") == ids[0] else AWAY for p in root.iter("Player")],
        dtype=np.int8,
    )


def _parse_group(text: str, out: np.ndarray) -> None:
    if not text or text[0] == "N":
        return
    pieces = text.split(",")
    out[0] = float(pieces[0]) * PITCH[0]
    out[1] = float(pieces[1]) * PITCH[1]
    out[2] = float(pieces[2]) if len(pieces) > 2 else np.nan


def load_tracking(use_cache: bool = True) -> Tracking:
    if use_cache and CACHE.is_file() and CACHE.stat().st_mtime >= RAW.stat().st_mtime:
        z = np.load(CACHE)
        return Tracking(ball=z["ball"], players=z["players"], team=z["team"])

    team = _team_of_each_slot(META)
    slots = len(team)
    ball = np.full((N_VIDEO_FRAMES, 3), np.nan, dtype=np.float32)
    players = np.full((N_VIDEO_FRAMES, slots, 3), np.nan, dtype=np.float32)

    with open(RAW) as handle:
        for line in handle:
            parts = line.rstrip("\n").split(":")
            if len(parts) != 3:
                continue
            i = int(parts[0]) - 1
            _parse_group(parts[2], ball[i])
            for s, group in enumerate(parts[1].split(";")):
                if s < slots:
                    _parse_group(group, players[i, s])

    np.savez(CACHE, ball=ball, players=players, team=team)
    return Tracking(ball=ball, players=players, team=team)
