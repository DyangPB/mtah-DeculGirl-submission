# SUMMARY — DeculGirl

**Five minutes is enough to read this.** The full explanation is in `docs/PLAYBOOK.md`. If this file
differs from the playbook, the playbook is right.

More than a Hack 2027 · Phase 1: Ball Possession · submission deadline **17 November 2026**

---

## What we are doing

The organisers give us one complete LaLiga match, **Barcelona vs Athletic**, together with automatic
tracking data (player and ball positions), automatic tactical tagging, and camera-to-pitch mapping data.
The task fits in one sentence:

> **For every frame, decide which team has the ball.**

The result is one CSV file `frame,label` with **199,319 rows**, using the labels `H` / `A` / `D` / `X`.
Scoring is automatic, using **`spellF1`**. There is no jury and no presentation.

Three things have to be handed in: the **CSV file**, a **public repo that can produce exactly that
file**, and a **technical document** a few pages long.

---

## Eight numbers that matter

| Number | Why it matters |
|---|---|
| **0.2433** | The minimum `spellF1` that has to be beaten (`baseline_smooth50`, full match) |
| **158,857** | The number of graded frames, out of 199,319. The rest have no effect at all |
| **41%** | The share of graded frames in which the **ball position is not detected** — and it is often missing at the important moments |
| **11×** | The `spellF1` gap between the best and worst baseline on the 5-minute public window. All four baselines use the **same algorithm**; only the window width differs (on the full match the gap is 5×) |
| **0.04** | A `spellF1` difference below this is only noise, not progress |
| **17** | The number of possessions in the 5-minute public window (21 segments, an average of 14.2 seconds) |
| **19** | Frames in the shortest possession in the GT (0.76 seconds). A possession this short **is real** |
| **14 Nov** | Code freeze day. After that the code must not change |

---

## Why we have a chance to win, and why the answer is not a fancy model

`spellF1` measures **how tidy the possessions are, without being fragmented**, not the accuracy of each
frame. The four baselines in the official repo use the same algorithm. Their `macroF1` differs by only
0.04, yet their `spellF1` differs enormously.

Our score will come from **four structural things**. None of the four is "a fancier model":

1. **Detecting the dead ball.** The baseline has no way at all of recognising a dead ball. It simply
   treats "ball not detected" as a dead ball. This is its biggest weakness. Class `D` actually gets
   **worse** when the result is smoothed.
2. **Filling in the missing ball position (imputation).** In 41% of graded frames the ball is not
   detected, and that often happens at the most decisive moments.
3. **Deciding which team has the ball.** The baseline only looks at the "nearest player". But there is
   still the distance to several players, the direction players are moving, earlier context, and the
   team tags from Smart Tagging, which nobody has used yet.
4. **Building possessions without splitting them.** Splitting one possession into two means **1 false
   positive and 1 false negative at once**. The `frag` column on the scoreboard can almost be used
   directly to estimate `spellF1`.

One more tool that is misunderstood most often: **`X` is not a give-up mark. `X` means "follow the
previous label".** Before building possessions, the scorer replaces every `X` with the last non-`X`
label. So not answering in the middle of a possession **costs nothing**. By contrast, not answering
exactly when the ball switches to the opposing team is **very costly**.

---

## Things to keep in mind

1. **The data goes in `data/tactical/`** with exactly the original file names. Only four files are
   needed; `tactical.mp4` is not used. The data must never be committed or uploaded anywhere.
2. **Run the chain early:** `python tools/fetch_official.py`, then `python run.py --placeholder`, then
   `python tools/gate0.py`. It works before the match data arrives.
3. **Never label by hand**, in any form and for any purpose. That includes **your own memory of the real
   match**. Never upload the data to a cloud LLM.
4. **Freeze the code on 14 November.** After that, only fix what is broken.

---

## Reading order

| # | Document | What it is for |
|---|---|---|
| 1 | `docs/SUMMARY.md` | **this document** |
| 2 | `docs/PLAYBOOK.md` sections 1–3 | the reasoning behind the strategy |
| 3 | `docs/PLAYBOOK.md` section 6 | **the prohibitions that must not be broken** |
| 4 | `docs/PLAYBOOK.md` section 4 | the technical strategy: dead ball, imputation, team attribution, segmentation, `X` policy |
| 5 | `docs/PLAYBOOK.md` section 5 | how to measure without fooling yourself |
| 6 | `docs/gt-public-transitions.md` | the first piece of work: the 21 transitions in the public GT |
| 7 | `docs/possession-rules.md` | the rules, in a form that can be coded |
| 8 | `RULES.md` and `CHALLENGE.md` in the official repo | the official rules |
