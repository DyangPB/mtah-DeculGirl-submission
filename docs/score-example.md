# Mini Example: From Data to the `spellF1` Score

This page explains the output of `tools/score_example.py`, a small example (14 frames, made-up data)
that runs the whole flow from start to finish. Its purpose is **learning**: every step is small enough
to read and compute by hand.

> **This script is not part of the submission pipeline.** Its numbers must not be used as a score or as
> a guide for tuning parameters. The official scorer
> (`third_party/mtah2027/evaluation/possession_metrics.py`) decides the real number, and this script has
> not been matched line by line against it.

## How to run it

From the repo root, in any terminal (PowerShell, Command Prompt, the VS Code terminal):

```
python tools/score_example.py                  # with clean-up (min-spell 2)
python tools/score_example.py --min-spell 1    # no clean-up, watch the score drop
python tools/score_example.py --min-spell 3    # more aggressive clean-up
```

It uses only the Python standard library, so nothing needs installing. If `python` is not recognised,
try `py tools/score_example.py`.

## The flow

```
position data -> features -> per-frame guess -> clean up into possessions
              -> fill X (done by the scorer) -> compute spellF1
```

The labels used: `H` (home team in possession), `A` (away team in possession), `D` (dead ball),
`X` (no guess; the scorer fills it with the previous label).

## Steps 1–2: data becomes a per-frame guess

Each frame has four pieces of information: whether the ball is detected, the team of the nearest
player, the ball speed, and whether the players are walking. The rule (the function
`guess_one_frame`):

1. Ball not detected → `X`.
2. Ball almost still and players walking → `D`.
3. Otherwise → the team of the nearest player.

The result is right in almost every frame. One mistake is planted on purpose at **frame 4**: an
Athletic player happens to pass near the ball, so the rule guesses `A`, when the real answer is `H`.

## Step 3: cleaning up

`clean_up` turns a short `H`/`A` possession into the team around it, **only if** both sides are the
same team. The pattern `H A H` becomes `H H H`. A dead ball `D` is never changed, and two possessions
of different teams are never merged (the same as R-6.2 and R-6.3 in
[Possession Rules](possession-rules.md)).

The `X` at frame 2 is still written as `X` in the output file. The script only fills it temporarily,
mimicking the scorer, before computing the score.

This is the anti-fragmentation step; the example here is only a simple version of it.

## Step 4: possessions

A possession is a run of consecutive frames with the same `H` or `A` label. The true answer in this
example has two: `H[0-6]` and `A[10-13]`. The dead ball `D` at frames 7–9 is not a possession.

## Step 5: `spellF1`

Scoring is per possession, not per frame:

1. Predicted possessions are matched one-to-one with real possessions of the same team, starting from
   the largest IoU.
2. **IoU** is the intersection divided by the union of the frame ranges. It is 1.0 when the ranges are
   exactly the same.
3. A pair counts as **correct** if IoU ≥ the threshold. The thresholds are 0.3 / 0.4 / 0.5 / 0.6 / 0.7.
4. For each threshold, `F1 = 2·correct / (2·correct + wrong + missed)` is computed. `spellF1` is the
   mean of those five F1 values.

Meaning of the table columns: `correct` = predicted possessions that match a real one;
`wrong_guesses` = predicted possessions with no match; `missed` = real possessions that were not
detected.

## Results for three settings

| `--min-spell` | Per-frame accuracy | Predicted possessions | `spellF1` |
|---|---|---|---|
| 1 (no clean-up) | 13/14 (93%) | `H[0-3]`, `A[4-4]`, `H[5-6]`, `A[10-13]` | **0.5333** |
| 2 (default) | 14/14 (100%) | `H[0-6]`, `A[10-13]` | **1.0000** |
| 3 | 14/14 (100%) | `H[0-6]`, `A[10-13]` | **1.0000** |

## The main lesson

**One wrong frame can wreck the score.** Without clean-up, per-frame accuracy is still 93%, but
`spellF1` falls to 0.53. One wrong `A` in the middle splits `H[0-6]` into three pieces:

- `H[0-3]` has an IoU of 4/7 ≈ 0.57 against `H[0-6]`. It passes at thresholds 0.3–0.5 but fails at 0.6
  and 0.7.
- `A[4-4]` and `H[5-6]` have no match, so they always count as wrong guesses.

This is a small version of what is written in the [Summary](SUMMARY.md): splitting one possession means
one false positive **and** one false negative. That is why `spellF1` measures how tidy the possessions
are, not the accuracy of each frame.

## Do not misread it

- **The `min-spell` value here is not a real parameter.** This example is only 14 frames. In the real
  data there are possessions as short as 19 frames that are genuine, and the minimum chosen in
  [Possession Rules](possession-rules.md) section 6 is 12 frames. Clean-up that is too aggressive
  deletes real possessions.
- **The true answer in this script is made up.** In the competition, the true answer is held by the
  organisers and we never see it. Do not make your own "true answer" from memory of the match; that
  counts as manual labelling, which is forbidden (see
  [Playbook section 6](PLAYBOOK.md#6-prohibitions-that-must-not-be-broken)).
