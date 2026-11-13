"""Sequence model, dead-ball detection, and segmentation.

This package turns per-frame features into per-frame labels.

THE SHAPE OF THE PROBLEM
This is a *sequence labelling* problem: 199,319 ordered frames that depend on
each other, with one label per frame. The four baselines in the official repo
label each frame independently and then smooth; you can go further with a
model that actually sees the sequence.

ORDER OF WORK -- do not reverse it
  1. **Dead ball first** (section 4.1). It is the biggest hole in the
     baseline, and the baseline's own docstring admits it:
       "It has no notion of a dead ball beyond 'the tracking lost the ball',
        which is why its D class is weak."
  2. ``H``/``A`` attribution for live-ball frames (section 4.3).
  3. Anti-fragmentation segmentation (section 4.4) -- from per-frame
     probabilities to intervals.
  4. Only then the sequence model (section 4.6), and only if it beats the
     rule-based version with non-overlapping confidence intervals.

TWO NUMBERS THAT DECIDE ALL THE WORK IN THIS PACKAGE
  - The scorer has **no minimum possession length**. A single frame counts as
    a full possession. One fragment = one false positive.
  - ``fp`` is also counted for your possessions that overlap a real possession
    but whose IoU is below the threshold. So splitting one real possession
    into two produces **1 FP + 1 FN at once**.

  And the opposite direction, which is easy to miss: the shortest possession
  in the public GT is **19 frames (0.76 s)** and it is a REAL possession. So
  your minimum spell length must be conservative. Details in
  ``docs/gt-public-transitions.md`` question 3.

THE NON-NEGOTIABLE RULE
  Every label must come out of an algorithm. No hand labels on this match, in
  any amount, for any purpose -- including training or validating a model.
  See ``docs/PLAYBOOK.md`` section 6.
"""
