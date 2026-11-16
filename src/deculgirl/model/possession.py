"""Possession as a state that persists (possession-rules R-3, R-4, R-5).

Input per frame: the ball position, and the players with their team. Output: ``H`` or ``A`` for every live
frame, never ``X`` (a held label is exactly what the scorer would carry forward over an ``X`` anyway).

  R-3.1  a team is a *candidate* in a frame if its nearest player is within D_CONTROL of the ball and is
         closer than the other team's nearest player by more than DISTANCE_MARGIN; the candidacy must
         last K_CONTROL frames in a row to count (fleeting touches are ignored)
  R-4.1  with no evidence from the other team, the label stays as it is, with no time limit
  R-4.2  the label switches only after N_SWITCH frames of evidence for the other team
  R-4.3  a confirmed switch is dated back to the first frame of its evidence
  R-5.1  if the switch happened inside a gap where the ball was not tracked, the gap is split at its
         midpoint (weakest guess in the rules; kept as the documented default)
"""

from __future__ import annotations

import numpy as np

from ..features.tracking import HOME, AWAY, Tracking

PARAMS = {
    "d_control": 2.0,        # m, a reasonable reach for a player controlling the ball
    "distance_margin": 1.0,  # m, below this the two teams are level
    "k_control": 5,          # frames (0.2 s), filters fleeting touches
    "n_switch": 10,          # frames (0.4 s); must stay below 19, the shortest real possession
    "evidence_gap": 25,      # frames; evidence separated by more than this does not accumulate
}

NONE = -1


def candidates(t: Tracking) -> np.ndarray:
    """Per-frame candidate team (HOME/AWAY) or NONE."""
    bx, by = t.ball[:, 0], t.ball[:, 1]
    d = np.hypot(t.players[:, :, 0] - bx[:, None], t.players[:, :, 1] - by[:, None])
    d = np.where(np.isfinite(d), d, np.inf)
    dh = d[:, t.team == HOME].min(axis=1)
    da = d[:, t.team == AWAY].min(axis=1)
    cand = np.full(t.n_frames, NONE, dtype=np.int8)
    near = np.isfinite(bx) & (np.minimum(dh, da) <= PARAMS["d_control"])
    with np.errstate(invalid="ignore"):  # inf - inf when a team has no tracked player
        cand[near & (da - dh > PARAMS["distance_margin"])] = HOME
        cand[near & (dh - da > PARAMS["distance_margin"])] = AWAY
    return _drop_short_runs(cand, PARAMS["k_control"])


def _drop_short_runs(cand: np.ndarray, k: int) -> np.ndarray:
    out = cand.copy()
    n = len(cand)
    i = 0
    while i < n:
        j = i
        while j < n and cand[j] == cand[i]:
            j += 1
        if cand[i] != NONE and j - i < k:
            out[i:j] = NONE
        i = j
    return out


def possession(cand: np.ndarray, ball_seen: np.ndarray, start: int, stop: int) -> np.ndarray:
    """Owner (HOME/AWAY/NONE) for frames ``start:stop`` of one live stretch."""
    n_sw, gap = PARAMS["n_switch"], PARAMS["evidence_gap"]
    out = np.full(stop - start, NONE, dtype=np.int8)
    owner, pend, count, pend_start, last = NONE, NONE, 0, 0, 0

    for i in range(start, stop):
        c = int(cand[i])
        if c != NONE:
            if c == owner:
                pend, count = NONE, 0
            elif c == pend and i - last <= gap:
                count += 1
                last = i
            else:
                pend, count, pend_start, last = c, 1, i, i
            if pend != NONE and count >= n_sw:
                old = owner
                owner = pend
                out[pend_start - start : i - start + 1] = owner  # R-4.3: back-date
                if old != NONE:
                    # R-5.1: the switch may hide inside a gap with no ball; split the gap at its midpoint
                    g0 = pend_start
                    while g0 > start and not ball_seen[g0 - 1]:
                        g0 -= 1
                    if g0 < pend_start:
                        mid = g0 + (pend_start - g0) // 2
                        out[g0 - start : mid - start] = old
                        out[mid - start : pend_start - start] = owner
                    # frames before the gap stay with the old owner (filled below)
                pend, count = NONE, 0
        if out[i - start] == NONE and owner != NONE:
            out[i - start] = owner
    # frames before the first confirmed owner belong to the first owner (offline look-ahead)
    seen = np.flatnonzero(out != NONE)
    if len(seen):
        out[: seen[0]] = out[seen[0]]
    # R-4.1 for the frames that switch-back-dating left empty before a later switch: hold the label
    for k in range(1, len(out)):
        if out[k] == NONE and out[k - 1] != NONE:
            out[k] = out[k - 1]
    return out
