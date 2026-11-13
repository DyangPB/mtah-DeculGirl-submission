"""data -> CSV submission.

THE ``build_labels()`` CONTRACT
-------------------------------
- returns a 1-D numpy array of strings, of length **exactly**
  ``deculgirl.N_VIDEO_FRAMES``
- every element must be one of ``"H"``, ``"A"``, ``"D"``, ``"X"``
- index ``i`` is ``video_frame`` ``i`` (0-based)
- no empty elements -- write ``"X"`` to abstain

If this contract is broken, ``validate_submission.py`` rejects the file and the
submission is **scored zero**. It is the most common cause of failure in this
competition.


===========================================================================
STATUS: FAIL-SAFE, NOT SMART YET.
===========================================================================

What runs right now is the **official baseline** (nearest tracked player to the
ball + majority voting), imported directly from
``third_party/mtah2027/starter/baseline.py``. That is neither cheating nor
laziness: the code is MIT, and the organisers themselves call it *"a starting
point, not a constraint"* -- and it is the fastest way to have a valid
submission.

It is your insurance. Once the data is in place and ``python run.py`` works,
you already hold a scoring submission (about 0.32 on the public window, 0.2433
on the full match). **Never remove this state.** Every improvement is added as
a variant, and `main` can always produce a valid submission.

HOW TO REPLACE IT -- one pillar at a time
-----------------------------------------
Change ``build_labels()`` to call your own pipeline, then work on the four
pillars in ``src/deculgirl/features/`` and ``src/deculgirl/model/`` (see
``docs/PLAYBOOK.md`` section 4):

  1. Dead-ball detection -- the highest-value pillar. The baseline has no
                            dead-ball logic at all
  2. Ball imputation     -- the ball is missing in 41% of graded frames
  3. Team attribution    -- richer than "nearest player"
  4. Segmentation        -- do not split possessions into fragments

The rule that must not be broken in this file: **no label may come from a
human hand.** Every label must come out of an algorithm. Not for the
submission, not for training a model, not for validating one.
See ``docs/PLAYBOOK.md`` section 6.

Also remember: labels outside ``GRADED_RUNS`` have no effect on the score.
Do not waste time perfecting the half-time break.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import GRADED_RUNS, LABELS, N_VIDEO_FRAMES

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL = ROOT / "third_party" / "mtah2027"

#: Where the match bundle lives. Same convention as the official repo: the
#: ``MTAH_DATA_DIR`` environment variable wins; otherwise use ``data/`` at the
#: root of this repo.
DEFAULT_DATA_DIR = Path(os.environ.get("MTAH_DATA_DIR") or (ROOT / "data"))

#: Half-width of the majority-voting window, in frames. 50 = a +/- 2 second
#: window, and it is the configuration that produces the published floor
#: (spellF1 0.2433 on the full match).
#:
#: DO NOT tune this number on the 5-minute public window. EVALUATION.md proves
#: that tuning there picks the WRONG value: window 125 wins on the public
#: window (0.4242) but loses on the full match (0.2242).
DEFAULT_WINDOW = 50


def _load_official_baseline():
    """Import ``starter/baseline.py`` from the official repo.

    Imported, not copied, so that when you update the official repo
    (``tools/fetch_official.py --force``) you also get their fixes -- and so it
    is clear that what runs here is their code, not something we made up.
    Licence: MIT.
    """
    starter = OFFICIAL / "starter"
    if not starter.is_dir():
        raise FileNotFoundError(
            f"Official repo not found at {OFFICIAL}.\n"
            "  run this first:  python tools/fetch_official.py"
        )
    # baseline.py itself adds the official repo root to sys.path when imported;
    # we add both so the order does not depend on it.
    for path in (OFFICIAL, starter):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    import baseline  # noqa: PLC0415  (deliberate: the import needs the sys.path above)

    return baseline


def build_labels(data_dir: Path | str | None = None, window: int = DEFAULT_WINDOW) -> np.ndarray:
    """Build one label for every video frame.

    This is the function to replace as the pipeline grows. The contract is in
    the module docstring.
    """
    baseline = _load_official_baseline()
    codes = baseline.build(data_dir=str(data_dir or DEFAULT_DATA_DIR))
    labels = baseline.smooth(codes, window)
    return _abstain_outside_graded(labels)


def _abstain_outside_graded(labels: np.ndarray) -> np.ndarray:
    """Write ``X`` for every frame outside ``GRADED_RUNS``.

    Possession rules section 5: outside the graded window there is nothing to
    answer, and the scorer ignores those frames. This does not change the
    score; it only makes the file say "no answer" where there is none, instead
    of the baseline's default ``D``.
    """
    labels = np.array(labels, dtype="<U1")
    graded = np.zeros(len(labels), dtype=bool)
    for start, stop in GRADED_RUNS:
        graded[start:stop] = True
    labels[~graded] = "X"
    return labels


def build_placeholder() -> np.ndarray:
    """A legal submission that answers nothing. Its score is 0.0000.

    It has exactly one purpose: to prove that the ``build -> write -> validate
    -> score`` chain is connected BEFORE the match data is available. Never
    submit this.

    Note that this file still **passes validation**. That is worth seeing
    once -- a valid file and correct contents are two different things, and
    the scorer only punishes the second.
    """
    return np.full(N_VIDEO_FRAMES, "X", dtype="<U1")


def write_submission(labels: np.ndarray, path: Path | str) -> None:
    """Write the submission file to the contract, then check it.

    Do not change this function. If the shape of the file is wrong, that is a
    bug in ``build_labels()``, not here.
    """
    labels = np.asarray(labels)

    if labels.ndim != 1:
        raise ValueError(f"labels must be 1-D, got {labels.ndim}-D")
    if len(labels) != N_VIDEO_FRAMES:
        raise ValueError(f"labels must have {N_VIDEO_FRAMES} elements, got {len(labels)}")

    labels = np.char.upper(np.char.strip(labels.astype(str)))

    empty = int(np.sum(labels == ""))
    if empty:
        raise ValueError(
            f"{empty} empty labels. The validator rejects empty cells -- write "
            "'X' to abstain, do not leave them empty."
        )

    bad = sorted(set(labels.tolist()) - set(LABELS))
    if bad:
        raise ValueError(f"labels outside {list(LABELS)}: {bad[:5]}")

    frame = pd.DataFrame(
        {
            "frame": np.arange(N_VIDEO_FRAMES, dtype=np.int64),
            "label": labels,
        }
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # newline="" + lineterminator="\n": make sure the file is identical on
    # Windows and Linux. Reproducibility is a grading requirement, not a bonus.
    with open(path, "w", newline="", encoding="utf-8") as handle:
        frame.to_csv(handle, index=False, lineterminator="\n")
