# Experiment Log — DeculGirl

> This is not a formality. It has **two** purposes: to know what has already been tried, and to be raw
> material for the mandatory section of the technical document.
>
> `SUBMISSION.md` asks the technical document to state *"which assets used and how — **including which
> were tried and dropped**"*. That section **cannot be invented in November**. The only way for it to
> have any content is to record it while the work is going on. This file is where that happens.

---

## How to log

There are three rules, and the third is the one broken most often:

1. **Write the hypothesis BEFORE running the experiment.** One line is enough: "I think changing X will
   raise `spellF1`, because Y". An experiment without a hypothesis only produces numbers, not knowledge.
2. **Write the result as it is.** Including the bad ones, and including the ones that did not change
   anything.
3. **Never delete the log of a failed experiment.** The discarded ones are exactly the content of the
   *"tried and dropped"* section of the technical document, and that section shows seriousness the
   most. A log that reports only successes looks like it comes from someone who never failed, and that
   is not believed.

**Every entry must have numbers, not impressions.** "It feels better" is not an experiment result.
Run `python tools/gate0.py` and copy the numbers.

**Always run `--bootstrap 1000` before concluding that one version is better.** A difference still
inside the noise band (`spellF1` ≈ 0.04 on the full match) means nothing. On the 5-minute public
window the noise band is even wider because there are only 17 possessions.

---

## Entry 0 — calibration · 24 October 2026

Run while setting up the project skeleton, **before there was any match data at all.** The goal was not
to chase a score, but to make sure the measuring tools work and to learn where the minimum floor is.

`python tools/gate0.py` on the 5 minutes of public ground truth:

| Version | `macroF1` | `spellF1` | `frag` | possessions reported | average duration |
|---|---|---|---|---|---|
| `baseline_raw` | 0.5972 | 0.0378 | **6.52** | 131 | 2.0 s |
| `baseline_smooth25` | 0.6200 | 0.2868 | 1.90 | 36 | 7.6 s |
| `baseline_smooth50` | **0.6207** | 0.3256 | 1.43 | 26 | 10.8 s |
| `baseline_smooth125` | 0.5812 | **0.4242** | **0.81** | 16 | 18.5 s |
| `DeculGirl` (placeholder) | 0.0000 | 0.0000 | 0.05 | 0 | 0.0 s |

*The truth: 17 possessions, 21 segments, an average of 14.2 seconds.*

**What we learned, and it changes how we work:**

- **`frag` can almost be used directly to estimate `spellF1`,** and the relationship is consistent:
  0.81 → 0.4242 · 1.43 → 0.3256 · 1.90 → 0.2868 · 6.52 → 0.0378. So the number to watch every day is
  `frag`, **not** `macroF1`, which only moves 0.04 across this whole set of runs.
- **Do not trust the ordering of these versions for the full match.** `smooth125` wins here (0.4242)
  but loses on the full match (0.2242). The public window cannot be used to rank anything.

### Breakdown of class `D` — the most useful finding in this log

| Version | `D` F1 | `D` precision | `D` recall |
|---|---|---|---|
| `baseline_raw` | **0.4197** | 0.5582 | 0.3363 |
| `baseline_smooth25` | 0.3857 | 0.6106 | 0.2818 |
| `baseline_smooth50` | 0.3225 | 0.6569 | 0.2138 |
| `baseline_smooth125` | 0.1464 | **1.0000** | **0.0790** |

Smoothing the result makes class `D` **worse**, not better. `smooth125` is never wrong when it says `D`,
so its precision is perfect, but it finds only 7.9% of the frames that really are dead ball.

**The hypothesis that emerges from this:** a dead-ball detector that uses **ball speed** (the third
column in the raw file, which no baseline has read yet) together with **player movement** will raise `D`
recall well above 0.34 **without** dropping its precision below about 0.60. This territory has not been
worked by anyone yet.

---

## Entry 1 — `X` outside graded frames · 14 November 2026

**Hypothesis:** writing `X` for frames outside `GRADED_RUNS` (instead of the baseline's default `D`) does
not change any score, because the scorer ignores those frames; it only makes the file use all four labels.
**What changed:** `_abstain_outside_graded()` in `src/deculgirl/submit.py`, applied after the baseline's
majority voting (window 50).
**Command:** `python run.py` then `python tools/gate0.py`

| Version | macroF1 | spellF1 | frag | poss | dur |
|---|---|---|---|---|---|
| `DeculGirl` before (3 labels) | 0.6207 | 0.3256 | 1.43 | 26 | 10.8 s |
| `DeculGirl` after (4 labels) | 0.6207 | 0.3256 | 1.43 | 26 | 10.8 s |

Label counts after: `H` 61,306 · `A` 46,183 · `D` 51,368 · `X` 40,462 (= 199,319 − 158,857 graded frames).

**Result:** unchanged, as expected.
**Is the difference above the noise band?** There is no difference.
**Verdict:** ✅ kept
**Reason for the verdict:** zero score risk, and the file now matches the four-label contract. The `X` policy
for ball-missing gaps inside the graded frames (possession rules R-5.1) is not implemented yet.

---

## Entry 2 — looking at the dead ball in tracking · 16 November 2026

**Status:** analysis only. No label has been changed yet, so `results/DeculGirl.csv` is still identical to
`baseline_smooth50` on every graded frame.

**Hypothesis (written before the numbers):** a dead ball shows up in the tracking as a slow ball, players
who move slowly, and a ball that is far from every player. A detector built on those signals, instead of on
"the ball was lost for 4 seconds", will raise `D` recall above the baseline's 0.21–0.34.

**What was looked at:** the 4 `D` blocks of the public GT (frames 12851–12988, 15889–16399, 17380–17837,
18027–18388; 1,469 frames) against the `H` and `A` frames of the same 5 minutes. Tracking only, no video.
Script kept outside the repo; the loader is `src/deculgirl/features/tracking.py`.

| Signal | `H` | `A` | `D` |
|---|---|---|---|
| Ball detected | 100% | 85% | **66%** |
| Ball outside the pitch (given detected) | 0% | 0% | **11%** |
| Ball speed from positions, median m/s | 5.3 | 6.6 | **2.7** |
| Nearest player to ball, median m | 1.6 | 1.7 | **2.9** |
| Mean player speed, median m/s | 2.05 | 2.47 | **1.19** |

**Findings:**

1. **The ball-speed column of the file is almost empty.** It exists in 1.2% of detected ball frames inside
   the graded ranges (8.7% over the whole match). The hypothesis in Entry 0 ("read the ball speed, third
   column") cannot be used as written. Ball speed has to be computed from positions between frames.
   The player speed column is present in only 37% of slots, so player speed is also best recomputed.
2. **The four `D` blocks do not look alike.** Block 1 (138 frames) and block 3 (458) have the ball missing
   most of the time (7% and 20% detected). Block 2 (511) has it detected 100% of the time, slow
   (median 2.8 m/s), inside the pitch. Block 4 (362) has it detected 100% of the time but 28% outside the
   pitch. One rule will not catch all four.
3. **Player speed separates `D` from `H`/`A` most cleanly** (1.19 vs 2.05 / 2.47 m/s), except block 4,
   where it is 2.18.
4. With only 4 blocks, these numbers describe the window, they do not calibrate a threshold. Thresholds
   must come from a stated source (R-2.2, parameter table), not from fitting these four blocks.

**Verdict:** ⏳ open. Next: write the detector with thresholds from possession-rules R-2.2, then score it.

---

## Entry 3 — own pipeline (variant, not wired into `build_labels`) · 16 November 2026

**Hypothesis (written before running):** a possession state machine (R-3/R-4/R-5) plus a layered dead-ball
detector (R-2) built only from tracking will beat `baseline_smooth50`, because it removes the baseline's
`D`-means-"ball lost" error and the frame-to-frame flicker of "nearest player wins".
**What changed:** new files only. `src/deculgirl/features/dead_ball.py`, `src/deculgirl/model/possession.py`,
`src/deculgirl/own.py`, `tools/make_own.py`. `submit.build_labels()` and `run.py` are untouched; the output is
`results/DeculGirl_own.csv`. Code freeze (decision 006) was on 14 Nov: this is a separate variant on purpose.
**Command:** `python tools/make_own.py` then `python tools/gate0.py --file results/DeculGirl_own.csv`

Dead-ball layers on graded frames (share of 158,857, each layer alone): prekick (FAQ) 1.8% · out of pitch 2.0%
· ball still + slow players 1.4% · quiet team (median < 0.5 m/s for 10 s) 6.6% · all four together **11.4%**.

**Correction made during the run, recorded because it is a "tried and dropped":** the first version used a quiet
threshold of 1.0 m/s and a ball-still threshold of 1.5 m/s on the team median speed. That gave `D` = 27.7% of
graded frames. The cause was my assumption, not the speed estimate (it matches the file's own speed column,
ratio 0.95): the median speed of all tracked players is ~1.35 m/s through the graded halves, so 28% of graded
frames are already under 1.0 m/s. Thresholds were lowered to 0.5 and 1.0 using that descriptive statistic of
the tracking only, not any ground truth.

| Version | macroF1 | spellF1 | poss | dur | `D` share (graded) |
|---|---|---|---|---|---|
| `baseline_smooth50` | 0.6207 | 0.3256 | 26 | 10.8 s | 32% |
| `DeculGirl_own` | 0.5600 | 0.3758 | 16 | 18.5 s | 11.4% |
| `DeculGirl_yona` (teammate, v2) | 0.6515 | 0.4457 | 18 | 15.5 s | 15.4% |

**Follow-up — `huddle` layer (added the same day).** Hypothesis: players clustered (RMS spread from the
centroid < 16 m, the bottom ~4% of graded frames; median is ~21 m) and slower than normal play (< 1.0 m/s) for
5 s is a celebration, substitution or gathering, i.e. a dead ball. Thresholds come from the distribution of the
tracking itself, not from any ground truth.
Result: alone it marks 0.6% of graded frames; added to the other four layers `D` goes from 11.4% to 11.9%
(+795 frames). It never fires inside the public 5 minutes, so the public score is unchanged
(spellF1 0.3758, macroF1 0.5600, `D` recall 0.07). **It does not fix the recall problem** — the dead balls in
the public window are not clusters. Kept because it is cheap and has a stated reason; it is not the answer.

**Is the difference above the noise band?** Not measurable: 17 possessions, one possession ≈ 6 points.
**Verdict:** ⚠️ kept as a variant, not selected. It does not beat the teammate's v2 on the public window, and
the window cannot rank anything (decision 007).

---

## Entry 4 — what can and cannot be shown about the own pipeline · 16 November 2026

**Hypothesis:** without the answer key, the own pipeline can still be checked on structure and on agreement
with an independent method. Checks chosen from `docs/possession-rules.md` section 6 (possession counts,
fragments shorter than 19 frames), plus agreement with a second, independently built pipeline.
**What changed:** nothing in the pipeline. Measurement only, over both graded halves (158,857 frames).
**Command:** a short script over `results/DeculGirl_own.csv`, the teammate's v2 file and `baseline_smooth50.csv`;
`python tools/gate0.py --file ... --bootstrap 1000` for the noise band.

| Check (both graded halves) | `baseline_smooth50` | own | teammate v2 |
|---|---|---|---|
| `H`/`A` possessions | 594 | 341 | 281 |
| Possessions shorter than 19 frames | 98 | 4 | 5 |
| Median possession length | 4.6 s | 10.0 s | 12.2 s |
| `D` runs · median length | 133 · 7.6 s | 62 · 5.0 s | 77 · 8.4 s |

Agreement between independent pipelines, on graded frames both call live (`H` or `A`), n = 129,076:
own vs teammate **86.6%** · own vs baseline 81.8% · teammate vs baseline 83.3%.
`D` overlap: 13,682 of the 18,948 own `D` frames (72%) are also `D` in the teammate's file.

Public 5 minutes (sanity only, decision 007): spellF1 own 0.3758, baseline 0.3256, teammate 0.4457.
The scorer's bootstrap (1,000 draws, 17 possessions) states that gaps below about 0.33 are inside the noise,
so none of these three scores is distinguishable from another.

**What is shown:** the own pipeline removes the baseline's main defect (98 fragments under 19 frames → 4) and
agrees with an independently built pipeline more than either agrees with the baseline.
**What is not shown:** that it is more accurate than the baseline on the full match, or than the teammate's
file. `D` recall on the public window is 0.07 (precision 0.98), the weak point.
**Verdict:** ⚠️ kept as a documented independent attempt, not submitted.

---

## Template for a new entry

Copy this block every time you try something measurable.

```markdown
## Entry N — <short name> · <date>

**Hypothesis:** <one line: what is changed, and why I think it raises spellF1>
**What changed:** <file and lines, or the parameter. If there is one, give the branch name>
**Command:** `python tools/gate0.py --file results/<variant-name>.csv`
**Bootstrap:** <number of resamples, if used>

| Version | macroF1 | spellF1 | frag | poss | dur |
|---|---|---|---|---|---|
| <comparison> | | | | | |
| <new variant> | | | | | |

**Result:** <as it is. If nothing changed, write "unchanged">
**Is the difference above the noise band?** <yes / no / overlapping — see the bootstrap result>
**Verdict:** ✅ kept · ❌ dropped · ⚠️ unclear, needs re-testing
**Reason for the verdict:** <one or two lines>
```

## What the verdict marks mean

| Mark | Meaning | Goes into the technical document? |
|---|---|---|
| ✅ **kept** | Already in `main` and contributes to producing the submission file | Yes, in the "assets and approaches used" section |
| ❌ **dropped** | Tried, but the result is not used | **Yes**, this is exactly the content of the *"tried and dropped"* section |
| ⚠️ **unclear** | The difference is still inside the noise band, or the result is inconsistent | Yes, write it as a limitation |

## Why this work deserves to be taken seriously

Running experiments sounds like support work. What happens here is the opposite: **it is the only way to
know whether a change is truly an improvement.** Without this log, every decision follows a feeling,
two versions each claim to be better, and nobody can decide because there are no numbers, only memory.

And if the entry later goes on to the Innovation Challenge, this file becomes the archive of how the
work was thought through. That is material that cannot be reconstructed from memory.
