# Worksheet — the 21 Transitions in the 5 Minutes of Public GT

This is the day-one work, and it shapes everything that follows.

Source: `evaluation/gt/BAR-ATH_possession_gt_public.csv` from the official repo (commit `f8f2629`).
Graded window: **frames 11,185 – 18,684** (7,500 frames). Outside that window the label is `X`.

All the numbers below have been **cross-checked** against `BAR-ATH_possession_gt_public_meta.json`:
`H` count = 3,454, `A` = 2,577, `D` = 1,469, total = 7,500. Everything matches.

---

## Why this worksheet exists

`CHALLENGE.md` states that the GT is **not a human judgement**. The GT is derived mechanically from
*corrected tracking* data that we do not hold. All we have is those 5 minutes. So the first job is not
"build a model", but to **reconstruct how that corrected tracking works from 21 transition points**.

There are only 21 transitions in the whole 5 minutes. Reading them takes only five minutes if you know
what to look for, but can eat a whole day if you start from "open the CSV and just look around".

---

## Table 1 — the 21 transitions, in order

The **Reason** column is filled in by hand. The **Signal** column is filled with a guess at the feature
that could detect it. Its contents are later passed on to the dead-ball detector (playbook section
4.1).

| # | Frame | Transition | Second (±) | Reason (to fill in) | Signal / feature (to fill in) |
|---|---|---|---|---|---|
| 1 | 11,185 | `X → A` | 447.4 | start of the graded window, not a real transition | — |
| 2 | 11,351 | `A → H` | 454.0 | | |
| 3 | 11,553 | `H → A` | 462.1 | | |
| 4 | 11,624 | `A → H` | 465.0 | | |
| 5 | 12,665 | `H → A` | 506.6 | | |
| 6 | **12,851** | **`A → D`** | 514.0 | | |
| 7 | **12,989** | **`D → H`** | 519.6 | | |
| 8 | 13,704 | `H → A` | 548.2 | | |
| 9 | 13,785 | `A → H` | 551.4 | | |
| 10 | 14,846 | `H → A` | 593.8 | | |
| 11 | 15,346 | `A → H` | 613.8 | ⚠️ possession of only **19 frames (0.76 s)** | |
| 12 | 15,365 | `H → A` | 614.6 | | |
| 13 | 15,766 | `A → H` | 630.6 | ⚠️ possession of only **33 frames (1.32 s)** | |
| 14 | 15,799 | `H → A` | 632.0 | | |
| 15 | **15,889** | **`A → D`** | 635.6 | | |
| 16 | **16,400** | **`D → A`** | 656.0 | ⚠️ dead ball of **511 frames = 20.4 s** | |
| 17 | 17,293 | `A → H` | 691.7 | | |
| 18 | **17,380** | **`H → D`** | 695.2 | | |
| 19 | **17,838** | **`D → A`** | 713.5 | ⚠️ dead ball of **458 frames = 18.3 s** | |
| 20 | **18,027** | **`A → D`** | 721.1 | | |
| 21 | **18,389** | **`D → H`** | 735.6 | ⚠️ dead ball of **362 frames = 14.5 s** | |
| — | 18,685 | `H → X` | 747.4 | end of the graded window, not a real transition | |

---

## Table 2 — the 17 real possessions

This is what `spellF1` compares. Note the durations: **the two longest possessions (41.6 s and 42.4 s)
and the two shortest (0.76 s and 1.32 s) weigh exactly the same.** One possession counts as one object.
That is why this metric measures how fragmented our possessions are.

| # | Team | Frames | Duration (frames) | Duration (seconds) |
|---|---|---|---|---|
| 1 | **A** | 11,185 – 11,350 | 166 | 6.64 |
| 2 | H | 11,351 – 11,552 | 202 | 8.08 |
| 3 | **A** | 11,553 – 11,623 | 71 | 2.84 ← A's shortest |
| 4 | H | 11,624 – 12,664 | 1,041 | 41.64 ← longest |
| 5 | **A** | 12,665 – 12,850 | 186 | 7.44 |
| — | *D* | *12,851 – 12,988* | *138* | *5.52* |
| 6 | H | 12,989 – 13,703 | 715 | 28.60 |
| 7 | **A** | 13,704 – 13,784 | 81 | 3.24 |
| 8 | H | 13,785 – 14,845 | 1,061 | 42.44 ← longest |
| 9 | **A** | 14,846 – 15,345 | 500 | 20.00 |
| 10 | H | 15,346 – 15,364 | **19** | **0.76** ← SHORTEST |
| 11 | **A** | 15,365 – 15,765 | 401 | 16.04 |
| 12 | H | 15,766 – 15,798 | **33** | **1.32** |
| 13 | **A** | 15,799 – 15,888 | 90 | 3.60 |
| — | *D* | *15,889 – 16,399* | *511* | *20.44* ← longest |
| 14 | **A** | 16,400 – 17,292 | 893 | 35.72 |
| 15 | H | 17,293 – 17,379 | 87 | 3.48 |
| — | *D* | *17,380 – 17,837* | *458* | *18.32* |
| 16 | **A** | 17,838 – 18,026 | 189 | 7.56 |
| — | *D* | *18,027 – 18,388* | *362* | *14.48* |
| 17 | H | 18,389 – 18,684 | 296 | 11.84 |

**Total: `H` 3,454 · `A` 2,577 · `D` 1,469 = 7,500 frames. Average possession duration 14.19 seconds.** ✅

---

## Raw lines around each `D` transition

Taken as they are from the GT file, so you can see for yourself that the transitions are clean: no mixed
frames and no gradual changes.

```
12848,A          12986,D          18386,D          18682,H
12849,A          12987,D          18387,D          18683,H
12850,A          12988,D          18388,D          18684,H
12851,D          12989,H          18389,H          18685,X
12852,D          12990,H          18390,H          18686,X
12853,D          12991,H          18391,H          18687,X
```

And the start of the file, to make sure you are really reading the same lines:

```
frame,label
0,X
1,X
2,X
3,X
4,X
```

---

## Six questions that must be answered

This is not a reading list. It is a list of **decisions**. The answers go into
`docs/possession-rules.md`, and then the code is written from them.

### 1. Why is frame 12,851 labelled `D`, and why does frame 12,989 go back to `H`?

The ball goes dead **5.5 seconds** after an `A` possession that lasted only 7.4 seconds. Play restarts
5.5 seconds later and is held by `H`, not `A`. That means it was most likely not a foul by `A`. It could
be a goal kick, or a throw-in for the opposing side. Check: does Smart Tagging have a phase in the range
12,851–12,988?

### 2. There are three long dead balls: 20.4 seconds, 18.3 seconds, and 14.5 seconds. What are they?

A throw-in usually lasts only 5–8 seconds. **20 seconds** is not a throw-in. It is probably an injury, a
substitution, or a VAR check. This matters, because if you assume "a dead ball is always brief", your
detector will be wrong at the three most conspicuous moments in this window. **These three moments add
up to 1,331 frames, or 17.7% of the whole graded window.**

### 3. ⚠️ A possession as short as 19 frames is real. What does it mean for our minimum possession length?

This is the most important finding in this worksheet, and it can directly save the score:

> The shortest possession in the GT is **19 frames (0.76 seconds)**, and it is a **real possession**,
> not a data error. The second shortest is 33 frames (1.32 seconds).

This means **the scorer does not merge short possessions.** If you set a minimum that is too aggressive,
for example "merge anything under 1 second" or "drop anything under 30 frames", you will **delete
possessions that really exist**, and every lost possession ≈ **6 points** of `spellF1` on this window.

**So the minimum has to be conservative**, which goes against instinct. Answer: what limit is chosen,
and why. (Hint: `baseline_raw` reports **131 possessions** for these 5 minutes, when the correct number
is **17**.)

### 4. The `D` rule or the `H`/`A` rule — which matters more?

Look at the composition: `H` 46%, `A` 34%, `D` **20%**. Class `D` takes 20% of the frames and only 4
segments (1,469 frames). If the `D` detector misses, the error immediately splits the possessions on
both sides. One `D` error can damage **three** possessions at once: the two that get cut and the one
that appears out of nowhere. Write this down as an explicit rule.

### 5. When may the system write `X`?

The pattern comes from `EVALUATION.md`:

| Situation | Action | Reason |
|---|---|---|
| Ball missing **in the middle of** a possession | Write `X` | The scorer replaces `X` with the last label, so the possession stays **one**. Costs nothing |
| When **possession switches to the opposing team** | **Must guess** | `X` pulls the old label into the opposing team's territory. Very costly |
| Outside the graded window | `X` | Not counted |

The question to answer: **how does the system know whether it is in the middle of a possession or at a
switch?** This is both a technical question and a football question.

### 6. The ball is detected in 59.3% of graded frames. Where is the rest?

There are `ball_x` and `ball_y` in 94,214 graded frames, and **none in the other 64,643 frames**. There
is no confidence indicator and no marker of any kind. `DATA.md` says the ball is missing
*"disproportionately on the frames that matter"*.

The question: of the 4 `D` segments in this window, **how many have a run of consecutive missing-ball
frames inside them?** If the relationship is strong, the ball gap itself is the strongest `D` feature
there is, and it comes for free. If it is weak, it means dead balls happen **while the ball is still
detected** (the ball rolling out, or sitting still at the spot of a foul), and that is a much harder
problem.

---

## How to fill in this worksheet

1. Run `python tools/fetch_official.py`, then `python run.py --placeholder` and
   `python tools/gate0.py` to make sure the chain runs and the public GT can be read.
2. Plot the ball position per frame over the range 11,185–18,684, with the background colour following
   the GT label.
3. For every `D` transition: look at 2 seconds before and after it. Ask *"what is happening here?"*
4. **Write what you observe, not the conclusion.** "Players stop and the ball is still" is more useful
   than "dead ball".
5. Every finding that can be turned into code → put it into `docs/possession-rules.md`.
6. Every finding that is still doubtful → record it in `docs/decisions.md` as a decision, with its
   reason.

**Do not** fill the Reason column with memories of the real match. If you remember a foul in the 20th
minute, it must not go in. Only what you **see in the plot and in the data** is allowed. See
`PLAYBOOK.md` section 6.
