"""Data and ball signal.

This package loads the supplied assets, canonicalises them, and builds
per-frame features.

Three things must be right before anything else:

1. **Alignment.** ``video_frame = id_frame - 1`` for ATD. Smart Tagging is in
   seconds --> ``round(seconds * 25)``. Homography is already per ``frame``.
   If this is wrong, all your features are correct but useless.

2. **Table shape.** One row per video frame, exactly 199,319 rows, index
   0..199318. If the count differs, **do not pad or trim** -- find out why it
   differs (FAQ.md forbids adjusting; "work out why the counts differ").

3. **The ball.** It is present in 56.9% of all frames and 59.3% of graded
   frames, and there is no confidence indicator at all. ``DATA.md`` says the
   gaps fall "disproportionately on the frames that matter". Design for that
   **from day one** -- that is their instruction, not a suggestion.

Available assets:

    data/tactical/BAR-ATH_tactical_atd.xml + _atd.txt   tracking (EPTS)
    data/tactical/BAR-ATH_tactical_smart_tagging.xml    tactical tagging
    data/tactical/BAR-ATH_tactical_homography.csv       camera geometry
    data/tactical/BAR-ATH_tactical.mp4                  video (NOT used)

Full details are in the official repo's ``DATA.md``, and the reader helpers
are in ``third_party/mtah2027/starter/`` (``load_atd.py``,
``load_smart_tagging.py``, ``load_homography.py``) -- all MIT, provided to be
used.

The features the model needs are described in ``docs/PLAYBOOK.md`` sections
4.1-4.3.
"""
