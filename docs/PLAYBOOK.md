# PLAYBOOK — DeculGirl

**More than a Hack 2027 · Phase 1: Ball Possession**
Metrica Sports × FC Barcelona (Barça Innovation Hub) × Mobile World Capital Barcelona

Written 24 October 2026 · Submission deadline **17 November 2026**

---

## 0. How to use this document

**If you only have 5 minutes, read [`SUMMARY.md`](SUMMARY.md), not this document.** This is the full
version, where all the numbers, reasons, and decisions are recorded.

This is not a pep-talk document. It is a working document: every section has consequences that can be
checked. How to use it:

- Sections 1, 2, and 6 are required reading.
- Section 4 is the working list for the technical pipeline (4.1–4.7).
- Section 5 is the measurement discipline, and section 8 is the submission checklist.
- Keep `docs/decisions.md` and `docs/experiments.md` up to date as you go.

If anything in this document conflicts with the organisers' official repo, **the official repo is
right**. All the numbers here were taken from that repo on 24 October 2026, from commit `f8f2629`.

---

## 1. What we are actually doing

We are working on one complete LaLiga match: **FC Barcelona vs Athletic Club**, LaLiga EA Sports 2024-25
matchday 2. The organisers give us footage from two cameras, automatic tracking of the position of every
player and the ball, automatic tactical tagging (Smart Tagging), and a camera-to-pitch mapping
(homography).

The task fits in one sentence:

> **For every frame of the match, decide which team has the ball.**

The result is one CSV file: `frame,label`, **199,319 rows**, with frames `0` to `199318` and labels
`H` / `A` / `D` / `X`.

| Label | Meaning |
|---|---|
| `H` | Barcelona (home) has the ball, and the ball is live |
| `A` | Athletic (away) has the ball, and the ball is live |
| `D` | Dead ball, i.e. the ball is not in play |
| `X` | The system does not answer |

**This part is misunderstood most often:** the task is **not** a computer-vision challenge, **not**
multi-object tracking, and **not** reconstruction of the game state. The tracking, tagging, and camera
mapping data are already supplied, so we do not need to build detection, player re-identification, or
camera calibration from scratch. Only one thing is graded: what the positions of 22 players and one ball
reveal about who has the ball.

More importantly, `CHALLENGE.md` states:

> *"The ground truth is derived from corrected tracking data — not from a human watching video, and not
> from event data. The derivation is mechanical: a frame is `D` where the corrected tracking marks the
> ball dead, and otherwise takes the team the tracking names as owning it. Nothing is smoothed,
> interpolated or hand-adjusted afterwards."*

This means: **the ground truth is not a human judgement about football.** The ground truth is the output
of a corrected tracking system. So what you are chasing is not "truth in football", but **guessing what
that corrected tracking data would say**. The only window into how it works is the **5 minutes of public
ground truth** in the repo.

---

## 2. Map of the terrain: the numbers that decide

| | |
|---|---|
| FPS (frames per second) | 25 |
| Total video frames | 199,319 (0–199318) |
| **Graded frames** | **158,857** |
| Graded half 1 | frames 11,185 – 90,651 (79,467 frames) |
| Graded half 2 | frames 110,808 – 190,197 (79,390 frames) |
| Half 2 kick-off | frame **113,742**, so the first 2,934 frames of half 2 are graded and **all of them are `D`** |
| Ball detected | 56.9% of all frames (113,488 / 199,319) · 59.3% of graded frames (94,214 / 158,857) |
| **Ball not detected** | **41% of graded frames**, 43% of all frames |
| Track slots | 46 (tactical feed) · 51 (broadcast) |
| Broadcast tracker records | 164,488 (its own timeline, not the same as tactical-feed frame numbers) |
| Smart Tagging | 638 phases |
| Valid homography | tactical 100% · broadcast 65.8% |
| Pitch size | 105.3 × 68.0 m (per `games.py`; the metadata says 105.0 × 68.0) |
| Frame offset | `{1: 1702057, 2: 1702058}`, one frame apart between halves |
| `video_frame` | `= id_frame − 1` (tracking data starts at 1, the submission starts at 0) |

**5 minutes of public ground truth** (the only ground truth we have):

| | |
|---|---|
| Range | frames 11,185 – 18,684 |
| Graded frames | 7,500 |
| Possessions | **17** · 21 segments · an average of 14.2 seconds |
| Composition | `H` 3,454 · `A` 2,577 · `D` 1,469 |

**The minimum floor to beat** is `baseline_smooth50`, measured on the full match:

| Baseline | macroF1 | spellF1 |
|---|---|---|
| `baseline_raw` | 0.6532 | 0.0486 |
| `baseline_smooth25` | **0.6752** | 0.1996 |
| `baseline_smooth50` | 0.6724 | **0.2433** ← minimum floor |
| `baseline_smooth125` | 0.6356 | 0.2242 |

Look at that table once more. The four rows are **the same algorithm, run four times**: find the player
nearest to the ball, then take the most votes (majority voting) within a window. The only thing that
changes is the window width. Yet `macroF1` shifts by only **0.04**, while `spellF1` changes **fivefold**.

That is no accident. That is the heart of this whole competition.

---

## 3. Why we can win, and why a model is not the answer

`spellF1` measures **how fragmented** our possessions are, not the accuracy of each frame. Every
possession (an unbroken run of `H` or `A`) is treated as one object. It is matched one-to-one with a
real possession through **temporal IoU** (a measure of overlap in time), and then the F1 is averaged at
the thresholds 0.3 / 0.4 / 0.5 / 0.6 / 0.7.

Four consequences that decide our strategy:

1. **A small fragment is not "half right". A small fragment is entirely wrong.** The scorer has **no
   minimum possession length**, so even a single frame counts as a full possession. What counts as `fp`
   (false positive) is not only ghost possessions. Our possessions that overlap a real possession but
   whose IoU is below the threshold **also** count as `fp`. So splitting one real possession into two
   produces **1 `fp` and 1 `fn` at once**. "Do not split possessions" is arithmetic, not just advice.
2. **One mistake can move the score by 6 points.** On the public window, one missed possession lowers
   `spellF1` by about 6 points. Every mistake has a large effect.
3. **Being 1 frame late does not matter.** Being 1 second late only lowers the score to 0.6539. This
   means **precision at the edges does not matter, but cutting in the middle of a possession is fatal.**
4. **The same label for every frame scores exactly 0.** There is no safe shortcut.

**The proof** comes from running the official scorer on the 5 public minutes. The `frag` column is the
ratio between the number of predicted segments and the 21 correct segments:

| Baseline version | `frag` | `spellF1` | possessions reported (GT: 17) |
|---|---|---|---|
| `baseline_smooth125` | 0.81 | **0.4242** | 16 (−1) |
| `baseline_smooth50` | 1.43 | 0.3256 | 26 (+9) |
| `baseline_smooth25` | 1.90 | 0.2868 | 36 (+19) |
| `baseline_raw` | 6.52 | 0.0378 | 131 (+114) |

The `frag` column can almost be used directly to estimate `spellF1`, and the relationship is consistent:
the smaller `frag` is, the larger `spellF1` is. That number is printed by the official evaluator every
time you run `tools/gate0.py`. **Watch that number every day, not `macroF1`.**

The conclusion to hold on to until 17 November:

> Our score comes from **four structural things**: dead-ball detection, filling in the missing ball
> position (imputation), deciding which team has the ball, and building possessions without splitting
> them. None of them is "a fancier model". All four can be done with features, rules, and thresholds,
> and each can be tested on its own.

---

## 4. Technical strategy

Suggested order of work: **rules and features first, the model afterwards.** The reason is not wanting to
be safe. The reason is that **every structural piece can be proven on its own**, and only that way do you
have something that can actually be written in the technical document.

### 4.1 Dead-ball detection — the highest-value part

The baseline has no dead-ball logic at all. The docstring of `starter/baseline.py` admits it:

> *"It has no notion of a dead ball beyond 'the tracking lost the ball', which is why its D class is weak."*

The only `D` signal in the baseline is that the ball is absent from that frame. This means the baseline
is only right when it gives `D` if the ball happens to be undetected **and** the ball really is dead.

**Smoothing the result makes class `D` worse, not better.** Here is the `D` F1 for each variant, from the
official scorer on the public window:

| Version | `D` F1 | `D` precision | `D` recall |
|---|---|---|---|
| `baseline_raw` | **0.4197** | 0.5582 | 0.3363 |
| `baseline_smooth25` | 0.3857 | 0.6106 | 0.2818 |
| `baseline_smooth50` | 0.3225 | 0.6569 | 0.2138 |
| `baseline_smooth125` | 0.1464 | **1.0000** | **0.0790** |

How to read it: `smooth125` is **never wrong** when it says `D`, so its precision is perfect, but it
finds only **7.9%** of the frames that really are dead ball. And all four variants are worse than `raw`
for this class. So a better dead-ball detector is **not just a small refinement on top of the baseline**.
It is territory that has not been worked at all, and every improvement here takes points from nobody.

Features that are available and that nobody has used yet:

| Feature | Why it is relevant |
|---|---|
| Length of the run of consecutive missing-ball frames | A dead ball often shows up as a long gap, not a short one |
| Ball speed | It is in the raw file as the **third** number in each group (`x,y,speed`). The baseline only reads the first two numbers |
| Player movement | During a dead ball, players walk (not run) or stop |
| Player spread and density | Player positions at a restart (kick-off, throw-in) have a characteristic pattern |
| Smart Tagging | **Every set piece is the start of the restart**, and it ends the dead-ball period. Every phase also has a team tag |
| The break between halves, before kick-off | Half 2 is graded from frame 110,808, kick-off is at 113,742. There are 2,934 frames that are all `D` |

> **A compliance note on the last point.** The fact about those 2,934 frames is **published in the
> official `FAQ.md`**, so using it is not a violation. But `RULES.md` forbids *"rules and constants tied
> to specific frames of the game"* that you **derive yourself from observation**. The safe way: build a
> dead-ball detector that is **general**, then use the FAQ fact as a **checking tool**, i.e. whether your
> detector really marks `D` there. If you decide to write the number directly in the code (hardcode),
> **cite it with its source** in the technical document. If in doubt, ask the organisers through an
> issue. `FAQ.md` openly invites this: *"If a rule is unclear or your approach sits near a line, ask
> before you build on it."*

### 4.2 Filling in the missing ball position (imputation)

The ball is not detected in **41% of graded frames**. According to `DATA.md`, it goes missing
*"disproportionately on the frames that matter"*, namely in a crowded penalty area, aerial duels, and
tackles. There is no confidence or visibility indicator in the data. `DATA.md` itself advises: *"design
for it on day one."*

A staged approach, from cheap to expensive:

1. **Short gaps** (less than about 0.5 seconds or 12 frames): fill with linear interpolation or a Kalman
   filter. The ball moves smoothly, so filling short gaps is almost always right.
2. **Long gaps**: **do not fill.** Leave them as uncertainty and use them as a signal. A long gap carries
   information by itself (see section 4.1).
3. **Geometry check:** project the filled ball position into pixels through the homography, then check
   that the result makes sense. This is the most directly useful use of the homography, and the tactical
   feed's homography is **100% valid**.
4. **One disturbance plus one bad guess costs more than one gap.** Remember that `X` in the middle of a
   possession **costs nothing** (section 4.5). So there is no reason to force a ball position you are not
   confident about.

**Do not use the video.** A GPU with 4 GB of VRAM is enough to run a small model. But `RULES.md` forbids
manual annotation *"in any amount and for any purpose"*, including for training a model. That means you
would have to rely on a model trained by someone else that happens to find the ball, and validate it
without ground truth. That is an experiment, not a plan. No part of it can be proven correct before 17
November.

### 4.3 Deciding which team has the ball

Baseline: the tracked player nearest to the ball, using squared Euclidean distance in metres. That is
all.

Replacement features. The list is long, but all of it is cheap to do:

- The distance from the ball to the **2–3 nearest players of each team**, then compared, not just the
  single nearest player overall.
- **Direction of movement:** whether a player is moving **towards** the ball (the dot product between
  the player's velocity and the vector from the player to the ball). A player approaching the ball is far
  more likely to gain control than a player who just happens to be near it.
- **Context before the gap:** which team last controlled the ball before it disappeared.
- **Hints from Smart Tagging:** every phase has a team tag. Two warnings from its documentation:
  `Team = N/A` on **every throw-in**, and *"the intervals are phases, not possessions"*.
- **Continuity from the previous frame is a feature, not a problem:** possession is a *state* that
  persists, not a decision made separately in each frame. A frame is labelled `H` mostly because the
  previous frame was `H`.

### 4.4 Building possessions without splitting them

This step turns per-frame probabilities into time spans. It is the part directly tied to the metric.

- **Minimum possession length.** The scorer has no minimum possession length, so **we** must have the
  rule. Merge short fragments into the dominant neighbour, or drop them. Every dropped fragment means one
  `fp` that disappears.
- **HMM / Viterbi** with a transition matrix that makes `H → A` switches expensive. This is the most
  natural form of the idea "possession is a persisting state, not a stand-alone decision".
- **Median filter** is the cheapest version of the same idea, and the baseline has already proven that
  the idea works: just by widening the window, `spellF1` moves fivefold.
- **Watch your possession count.** `validate_submission.py` prints the number. The `raw` baseline
  reports **131 possessions** for the 5 public minutes, when the correct number is **17**. That means
  possessions are fragmented 7.7 times over, and that is why its `spellF1` is only 0.0378.

### 4.5 The `X` policy — the most powerful tool we have

Before building possessions, the scorer replaces every `X` with the last non-`X` label **in the same
half** (at the start of a half, it is filled with the first non-`X` label encountered). So:

```
H H H X X X H H H   →   H H H H H H H H H   →   ONE possession
```

**`X` is not a give-up button. `X` is the "same as before" button.**

How to apply it:

| Situation | Action | Reason |
|---|---|---|
| Ball missing **in the middle of** a possession | Write `X` | Costs nothing. The possession stays whole. Safer than a guess that could split it |
| When **possession switches to the opposing team** | **Must guess** | `X` would pull the old label into the opposing team's territory. This is very costly |
| Outside match time | `X` | Not graded at all |

On cost: `macroF1` counts `X` as wrong, but `macroF1` is only the tiebreaker. `spellF1`, which decides
the ranking, never sees it. So in practice **`X` is cheap**, and there is no reason to hesitate to use
it.

### 4.6 Sequence model (last, not first)

Only done after the four structural pieces stand and are proven. The most sensible form: **a CRF or
GRU/Bi-GRU on top of per-frame features**, with the four structural pieces as input features, not as a
replacement.

The rule: if it does not beat the rule-based version with non-overlapping confidence intervals,
**keep the rule-based version.** The sequence model is only a bonus, not a way out.

### 4.7 The technical document (the third deliverable)

`SUBMISSION.md` asks for *"a few pages"*. The requested structure should be followed exactly:

1. **The approach and its reasons** — why it was chosen that way, not just what was done.
2. **Which assets were used and how** — including **those that were tried and then dropped**. This part
   is missed most often, yet it is the one that shows seriousness the most. Its content is taken as it
   is from `docs/experiments.md`. **That is why that file exists**, and why it must be filled in while
   the work is going on, not reconstructed in November.
3. **Training data** — every labelled dataset, its source, who labelled it, and its size. If there is
   none, write "none". That is a valid answer.
4. **The possession rules applied** — taken from `docs/possession-rules.md`.
5. **Limitations** — write them honestly. Honesty raises credibility, it does not lower it.
6. **How to reproduce the result** — one command.

Also attach which facts from the official documentation you used (section 4.1), and which decisions were
calibrations or made by hand, if any.

---

## 5. How to measure without fooling yourself

**The scorer you run on your own computer is the scorer that decides the competition ranking.** In the
words of `EVALUATION.md`: *"Organisers run this exact script against the private full-match ground truth;
the published board is its output. There is no stricter version held back."* This is a big advantage, so
use it to the full.

```bash
python tools/gate0.py              # fetch the official repo, run the official evaluator
python evaluation/validate_submission.py <file>   # BEFORE every submission
```

Measurement rules:

- **`spellF1` noise on the full match ≈ 0.04.** A difference below that is not an improvement.
  `macroF1` noise ≈ 0.01.
- **Always run `--bootstrap 1000`** before believing that one version is better than another. The
  intervals usually overlap.
- **The 5-minute public window is not a leaderboard.** It has only 17 possessions, and one missed
  possession roughly means 6 points. `EVALUATION.md` proves that tuning parameters there picks the wrong
  baseline. Use it only to confirm that **the pipeline is correct**, not to choose versions.
- **The result must always be the same (deterministic).** If the score changes between two runs of the
  same program, that is a bug, not luck.
- **`reports/<name>_transitions.csv`** from the official evaluator lists every transition as `matched`,
  `missed`, or `spurious` for every video frame. It is the best debugging tool you have, and few people
  know it exists.

### Scoreboard columns you must read

`tools/gate0.py` prints the official scoreboard. Besides `spellF1` and `macroF1`, there are five columns
that are far more useful for daily work:

| Column | Meaning | What you are looking for |
|---|---|---|
| **`frag`** | number of predicted segments ÷ number of correct segments | **Close to 1.0 or slightly below.** This is the most important column on the whole board |
| **`poss`** | the number of possessions you report | The correct number is **17** in this window. 26 is already starting to drift; 131 is a danger sign |
| **`dur`** | average possession duration | The correct value is **14.2 seconds**. If it is too short, your possessions are fragmented |
| **`shareE`** | difference in the home team's possession share compared with the truth | The truth is 0.5727: Barcelona has 57% of live-ball frames in this window |
| **`lat_f`** | average lateness, in frames | Under 25 frames is still cheap (section 3 point 3); above that it is costly |

The per-submission report (the `.txt` file the evaluator writes) is sharper still. It contains the 4×4
confusion matrix, precision/recall/F1 per class, `alive/dead F1`, team accuracy, and, most relevant to
section 4.5, **how many of your `X` frames fall on graded frames.** That is a direct measure of the
abstention policy you are using. The evaluator also writes `scoreboard.csv`.

---

## 6. Prohibitions that must not be broken

This list contains the things that can make three weeks of work worth zero. It is not about ethics, it is
about **what counts**.

| ❌ Forbidden | Details that are easy to miss |
|---|---|
| **Labelling this match by hand** | *"in any amount and for any purpose"*: for the submission, **for training a model, and for validating one**. This includes correcting an algorithm's output by hand, whether *frame by frame, segment by segment, or only at the transition points* |
| **Human-made data about this match** | Event data (Opta, StatsBomb, Wyscout, LaLiga, or anyone else), corrected tracking, possession data, or any annotation from any source |
| ⚠️ **Your own memory of this match** | This follows from the prohibition above, and is a particular trap for anyone who knows football. If someone remembers the final score, the minute of a goal, or a VAR incident, that is **human knowledge about this match**. Using it as a feature, a label, or a constant is a violation. What is allowed: understanding what football **means**. What is not allowed: remembering **this match** |
| **Uploading data to a cloud LLM** | The terms of use (ToU) forbid uploading video, the dataset, or **pieces of them** to a third-party cloud-based LLM. Using AI to write code is still allowed; what is forbidden is sending the contents of the data |
| **Distributing the data** | Do not commit `data/` to a public repo. Do not publish derivatives that could be used to reconstruct the data |
| **A repo that cannot reproduce the file** | *"A private in-house model or an unavailable internal dataset is the one thing this rules out"* |
| **Tuning parameters on the public 5 minutes** | This is a rule, not advice. And it is proven harmful (section 5) |

**What is explicitly allowed**, and which you may not have realised:

- Correcting or **replacing** the supplied tracking data, as long as it is done **by an algorithm**, not
  by hand.
- Using models already trained by others, any LLM, and any framework.
- Using outside data, **as long as it is about other matches**.
- Labelling **other matches** by hand, as much as you like.
- Using Smart Tagging. The FAQ answers this suspicion directly: *"Use it — that is why it is there."*
- Using a model you built yourself: a detector, a tracker, or an event recogniser. *"If it produces a
  better answer, it is a better answer."*

---

## 7. Ten decisive things — from the most often overlooked

1. **The winner is not the one with the fanciest model.** The four baselines in the repo use **the same**
   algorithm with different windows: `macroF1` moves 0.04, while `spellF1` differs 11-fold on the public
   window (5-fold on the full match).
2. **`X` is the "repeat the previous answer" button.** Not answering in the middle of a possession costs
   nothing; not answering when possession switches to the opposing team is a disaster. One policy, two
   opposite directions.
3. **The scorer has no minimum possession length.** A small fragment is not "half right". It is a pure
   `fp`, and splitting one possession into two produces an `fp` and an `fn` at once.
4. **Class `D` is the biggest weakness.** The baseline admits it itself. Smart Tagging gives team tags
   and set-piece markers for free, and **nobody has used them yet.**
5. **The ball is not detected in 41% of graded frames, and it is missing exactly in the frames that
   matter.** It is not a disturbance to be tolerated. It is the problem.
6. **The public 5 minutes cannot be used to rank anything.** `smooth125` wins on the public window but
   loses on the full match. And that is just one parameter on a simple baseline.
7. **Most points are lost to admin.** A file that fails validation is scored **zero**, and a repo that
   cannot reproduce the file disqualifies the entry. `validate_submission.py` takes only two seconds.
8. **Outside the two halves, your labels have no effect at all.** `macroF1` only counts graded frames,
   and `spellF1` only builds possessions inside the graded ranges. Do not waste time on the break.
9. **The first 2,934 frames of half 2 are all `D`**, and that is officially published in `FAQ.md`. Use it
   as a checking tool for your dead-ball detector, and cite the source.
10. **Everything you produce will be read.** Two of the three deliverables are not numbers: the repo and
    the document. Both also help decide what happens at the Innovation Challenge, which is judged very
    differently: there is a jury, a presentation, and design.

---

## 8. Submission checklist

Run on **15 November**, no later.

**CSV file**
- [ ] `DeculGirl.csv` — exactly **199,319** data rows, header `frame,label`
- [ ] The `frame` column holds 0…199318, in order, with no duplicates
- [ ] No empty cells — write `X` if the system does not answer
- [ ] `python evaluation/validate_submission.py DeculGirl.csv` → **`Valid.`**
- [ ] The possession count reported is plausible (compare with 17 on the public 5 minutes; 131 is a
      danger sign)
- [ ] The `frag` column is close to 1.0 or slightly below, not 2 or more
- [ ] The line `abstained ... frames of X on graded ground truth` in the report matches your `X` policy,
      not 0% and not 100%

**Public repo**
- [ ] The submission repo is **public**, and its URL opens in an incognito window
- [ ] The `data/` folder is **not** in the repo
- [ ] `run.py` produces an identical file, tested on someone else's laptop
- [ ] Dependency versions are pinned (`requirements.txt` with version numbers)
- [ ] `README.md` explains how to run it in language an outsider can follow

**Technical document**
- [ ] `DeculGirl.pdf` or `.md`, a few pages, following the structure in section 4.7
- [ ] Mentions the assets that were tried **and then dropped**, not only those used
- [ ] States whether there is training data, with its source
- [ ] Lists the official facts used as calibration

**Form**
- [ ] One response per team. **The last response before the deadline is the one graded.**
- [ ] Team name: `DeculGirl` · files: `DeculGirl.csv`, `DeculGirl.pdf`
- [ ] A Google account is needed · there is no live leaderboard and no feedback
- [ ] Keep a screenshot as proof of submission somewhere safe

---

## 9. After 17 November

Results are announced **before 26 November**. If the entry reaches the **top 20**, it continues to the
Innovation Challenge (**26 Nov – 14 Jan**, online) with a dataset of **10 professional matches**, an
open design challenge, and technical mentoring. If it reaches the **top 5** there, it appears in the
Final Pitch on **2 March 2027** at the Talent Arena Barcelona. Travel and accommodation are covered, and
there is an official Barça jersey and an exclusive experience. There is no cash prize.

Even if it does not qualify, there is still a public repo containing the analysis of one real LaLiga
match, with a reproducible pipeline and a technical document other people can read. That is not a small
result.

**Judging changes completely in the next phase.** Phase 1 is judged purely on numbers with no jury, so a
good idea earns no marks. The Innovation Challenge judges design, interpretation, and storytelling
instead. So for these 25 days: **chase the score first, the story afterwards.** But from now on, record
every decision in `docs/decisions.md`. The raw material for the story cannot be reconstructed in
December.
