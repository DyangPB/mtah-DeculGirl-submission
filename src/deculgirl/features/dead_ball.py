"""Dead-ball detector -- our own rules, tracking only (possession-rules R-2).

Four independent layers, each switchable so that its effect can be logged on its own
(docs/experiments.md). A frame is dead (``D``) if ANY enabled layer says so.

  out      R-2.2(a)  the ball is detected outside the pitch for at least 1 s
  still    R-2.2(b)  the ball stays inside a 1 m circle for 1 s AND the players are walking pace or slower
  quiet    R-2.3     the players are slower than walking pace for 10 s, whether or not the ball is seen
                     (long stoppages: injury, substitution, VAR -- and the ball is often not tracked there)
  huddle   R-2.3     the players are clustered AND slower than normal play for 5 s (a goal celebration, a
                     substitution, players gathering around a referee or an injured player)
  prekick  FAQ.md    frames 110,808-113,741 are graded and all dead (published, not observed)

Every number is an assumption from football or physics, listed in PARAMS with its reason. None is fitted to
the match, to its public ground truth, or to its video.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import GRADED_RUNS
from .tracking import FPS, PITCH, Tracking

PARAMS = {
    # The median speed of the tracked players is ~1.35 m/s through the graded halves (keepers and
    # defenders pull it below an outfield walk), so thresholds on it are low: 28% of graded frames are
    # already under 1.0 m/s. "Slower than normal play" for the ball-still layer = under 1.0 m/s.
    "walk_speed": 1.0,
    # ball counts as still when it moves less than v_still (1 m/s, possession-rules table) over T_still (1 s)
    "still_radius_m": 1.0,
    "still_frames": FPS,
    # out of the pitch for a full second is not a tracking flicker
    "out_frames": FPS,
    # a standing team (median speed under 0.5 m/s, ~9% of graded frames) for this long is a stoppage
    "quiet_speed": 0.5,
    "quiet_frames": 10 * FPS,
    # a throw-in lasts 5-8 s (possession-rules R-2.3), so nothing shorter than 2 s is a dead ball
    "min_dead_frames": 2 * FPS,
    # gaps this short inside a dead stretch are tracking drop-outs, not a restart
    "bridge_frames": FPS,
    # player speed is the displacement over this many frames (centred), expressed in m/s
    "speed_span": FPS,
    # RMS distance of the tracked players from their centroid is ~21 m in open play (median over the graded
    # halves); under 16 m is the clustered tail (bottom ~4%), well below any normal team shape.
    "huddle_spread_m": 16.0,
    "huddle_frames": 5 * FPS,
    # FAQ.md: second half graded from 110,808, kick-off at 113,742
    "prekick": (110_808, 113_742),
}

LAYERS = ("out", "still", "quiet", "huddle", "prekick")


def team_speed(players: np.ndarray, span: int | None = None) -> np.ndarray:
    """Median speed (m/s) over tracked slots, from displacement across ``span`` frames, centred."""
    span = span or PARAMS["speed_span"]
    half = span // 2
    n = players.shape[0]
    xy = players[:, :, :2]
    ahead = np.full_like(xy, np.nan)
    behind = np.full_like(xy, np.nan)
    ahead[: n - half] = xy[half:]
    behind[half:] = xy[: n - half]
    disp = np.hypot(*(ahead - behind).transpose(2, 0, 1))
    speed = disp * FPS / (2 * half)
    speed[speed > 12.0] = np.nan  # faster than a sprint is a tracking jump
    with np.errstate(all="ignore"):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return np.nanmedian(speed, axis=1)


def team_spread(players: np.ndarray, min_tracked: int = 14) -> np.ndarray:
    """RMS distance (m) of the tracked players from their centroid; NaN with fewer than ``min_tracked``."""
    xy = players[:, :, :2]
    with np.errstate(all="ignore"):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            cx = np.nanmean(xy[:, :, 0], axis=1)
            cy = np.nanmean(xy[:, :, 1], axis=1)
            rms = np.sqrt(np.nanmean((xy[:, :, 0] - cx[:, None]) ** 2 + (xy[:, :, 1] - cy[:, None]) ** 2, axis=1))
    rms[np.isfinite(xy[:, :, 0]).sum(axis=1) < min_tracked] = np.nan
    return rms


def _runs(mask: np.ndarray):
    edge = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    return zip(np.flatnonzero(edge == 1), np.flatnonzero(edge == -1))


def _close(mask: np.ndarray, gap: int) -> np.ndarray:
    """Fill False gaps of at most ``gap`` frames between True stretches."""
    out = mask.copy()
    prev_end = None
    for s, e in _runs(mask):
        if prev_end is not None and s - prev_end <= gap:
            out[prev_end:s] = True
        prev_end = e
    return out


def _keep_long(mask: np.ndarray, min_len: int) -> np.ndarray:
    out = np.zeros_like(mask)
    for s, e in _runs(mask):
        if e - s >= min_len:
            out[s:e] = True
    return out


def graded_mask(n: int) -> np.ndarray:
    g = np.zeros(n, dtype=bool)
    for a, b in GRADED_RUNS:
        g[a:b] = True
    return g


def layer_masks(t: Tracking) -> dict[str, np.ndarray]:
    n = t.n_frames
    bx, by = t.ball[:, 0], t.ball[:, 1]
    det = np.isfinite(bx)
    speed = team_speed(t.players)
    walking_or_slower = np.nan_to_num(speed, nan=np.inf) < PARAMS["walk_speed"]
    quiet = np.nan_to_num(speed, nan=np.inf) < PARAMS["quiet_speed"]

    out_of_pitch = det & ((bx < 0) | (bx > PITCH[0]) | (by < 0) | (by > PITCH[1]))
    out = _keep_long(_close(out_of_pitch, PARAMS["bridge_frames"]), PARAMS["out_frames"])

    w = PARAMS["still_frames"]
    sx, sy = pd.Series(bx), pd.Series(by)
    rx = sx.rolling(w, center=True, min_periods=w // 2 + 1).max() - sx.rolling(
        w, center=True, min_periods=w // 2 + 1
    ).min()
    ry = sy.rolling(w, center=True, min_periods=w // 2 + 1).max() - sy.rolling(
        w, center=True, min_periods=w // 2 + 1
    ).min()
    ball_still = det & (np.hypot(rx.to_numpy(), ry.to_numpy()) <= PARAMS["still_radius_m"])
    still = ball_still & walking_or_slower

    quiet_long = _keep_long(_close(quiet, PARAMS["bridge_frames"]), PARAMS["quiet_frames"])

    spread = team_spread(t.players)
    clustered = np.nan_to_num(spread, nan=np.inf) < PARAMS["huddle_spread_m"]
    slow = np.nan_to_num(speed, nan=np.inf) < PARAMS["walk_speed"]
    huddle = _keep_long(_close(clustered & slow, PARAMS["bridge_frames"]), PARAMS["huddle_frames"])

    prekick = np.zeros(n, dtype=bool)
    prekick[PARAMS["prekick"][0] : PARAMS["prekick"][1]] = True

    return {"out": out, "still": still, "quiet": quiet_long, "huddle": huddle, "prekick": prekick}


def dead_ball(t: Tracking, layers: tuple[str, ...] = LAYERS) -> np.ndarray:
    """Boolean mask, True where the ball is dead, restricted to graded frames."""
    masks = layer_masks(t)
    dead = np.zeros(t.n_frames, dtype=bool)
    for name in layers:
        dead |= masks[name]
    g = graded_mask(t.n_frames)
    dead = _keep_long(_close(dead & g, PARAMS["bridge_frames"]), PARAMS["min_dead_frames"])
    # the pre-kick-off block is always dead, whatever the short-run filter did
    if "prekick" in layers:
        dead |= masks["prekick"]
    return dead & g
