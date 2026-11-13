"""Match constants and the submission contract.

Every number here comes from the organisers' official repo at commit
``f8f2629``. If anything conflicts with the official repo, **the official repo
is right** -- then update this file.

Terminology lives in ``GLOSSARY.md`` at the repo root. Use the terms from
there in code and docs, so "possession" vs "spell" never becomes ambiguous.
"""

from __future__ import annotations

# --- Shape of the match -----------------------------------------------------

#: Number of tactical-video frames. This is also the exact number of data rows
#: a submission file must have -- always, no matter what.
N_VIDEO_FRAMES = 199_319

#: Frames per second. 25 tracking rows = 1 second.
FPS = 25

#: Pitch size in metres, from the official repo's ``games.py``.
#: (The metadata says 105.0 x 68.0; the 30 cm difference only matters if you
#: compute distances in metres. The official baseline uses this value.)
PITCH_M = (105.3, 68.0)

# --- Label contract ---------------------------------------------------------

#: The only valid labels. Nothing else, in any form.
LABELS = ("H", "A", "D", "X")

#: Labels that spellF1 counts as a possession. ``D`` is a stoppage and ``X``
#: is not a state.
POSSESSION_LABELS = ("H", "A")

# --- Graded frames ----------------------------------------------------------
#
# Half-open ranges [start, stop), exactly like ``valid_runs()`` in the official
# repo: (11185, 90652) and (110808, 190198).
#
# IMPORTANT: the second half is graded from frame 110,808, but its kick-off is
# only at 113,742 -- so the first 2,934 frames of the second half are graded
# and ALL of them are ``D``. This is published officially in FAQ.md, it is not
# a guess. If you use it to calibrate a dead-ball detector, cite the source in
# the technical document (RULES.md forbids constants derived from your own
# observation).
GRADED_RUNS = ((11_185, 90_652), (110_808, 190_198))

#: Outside the ranges above your labels have no effect at all: macroF1 only
#: counts graded frames, and spellF1 only builds possessions inside the graded
#: ranges.
N_GRADED_FRAMES = 158_857

# --- Public ground-truth window ---------------------------------------------

#: The only ground truth we hold. Use it to verify that the pipeline is
#: CORRECT -- not for ranking, not as training data, not as a tuning set.
PUBLIC_GT_RUNS = ((11_185, 18_685),)
PUBLIC_GT_FRAMES = 7_500
PUBLIC_GT_POSSESSIONS = 17

# --- Calibration: offsets between sources -----------------------------------

#: ``video_frame = id_frame - 1`` for ATD.
ID_FRAME_OFFSET = 1

#: Per-half offsets for Smart Tagging, from ``games.py``.
#: The two halves differ by one frame, so no single exact offset exists.
FRAME_OFFSETS = {1: 1_702_057, 2: 1_702_058}

# --- Metric thresholds ------------------------------------------------------
#
# Do not compare below these numbers; that is noise, not progress.

#: spellF1 noise band on the full match.
SPELL_F1_NOISE = 0.04

#: macroF1 noise band.
MACRO_F1_NOISE = 0.01

#: The floor to beat: baseline_smooth50 on the full match.
BASELINE_FLOOR_SPELL_F1 = 0.2433
