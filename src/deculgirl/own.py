"""Our own labelling pipeline: tracking only, rules from docs/possession-rules.md.

    labels = build_labels_own()            # H / A / D / X, one per video frame

Layers (each one can be switched off to measure it on its own):
  1. dead ball      deculgirl.features.dead_ball   (D)
  2. possession     deculgirl.model.possession     (H / A inside each stretch of live play)
  3. X outside the two graded ranges

This does not use the official baseline's labels, Smart Tagging, the video or the public ground truth.
The default pipeline in ``submit.build_labels`` is untouched: this is a separate variant.
"""

from __future__ import annotations

import numpy as np

from . import GRADED_RUNS, N_VIDEO_FRAMES
from .features.dead_ball import LAYERS, dead_ball, _runs, graded_mask
from .features.tracking import AWAY, HOME, load_tracking
from .model.possession import NONE, candidates, possession


def build_labels_own(layers: tuple[str, ...] = LAYERS) -> np.ndarray:
    t = load_tracking()
    graded = graded_mask(t.n_frames)
    dead = dead_ball(t, layers)
    live = graded & ~dead

    cand = candidates(t)
    ball_seen = np.isfinite(t.ball[:, 0])

    owner = np.full(t.n_frames, NONE, dtype=np.int8)
    for s, e in _runs(live):
        owner[s:e] = possession(cand, ball_seen, s, e)

    # A live stretch in which nobody is ever seen controlling the ball takes the nearest known team.
    known = np.flatnonzero(owner != NONE)
    todo = np.flatnonzero((owner == NONE) & live)
    if len(known) and len(todo):
        pos = np.searchsorted(known, todo)
        owner[todo] = owner[known[np.minimum(np.maximum(pos - 1, 0), len(known) - 1)]]

    labels = np.full(N_VIDEO_FRAMES, "X", dtype="<U1")
    labels[live & (owner == HOME)] = "H"
    labels[live & (owner == AWAY)] = "A"
    labels[dead] = "D"
    return labels
