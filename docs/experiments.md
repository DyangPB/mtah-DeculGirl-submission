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
