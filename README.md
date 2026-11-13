# DeculGirl — More than a Hack 2027, Phase 1

Label ball possession **for every frame** of one complete LaLiga match
(**FC Barcelona v Athletic Club**, LaLiga EA Sports 2024-25, matchday 2).

A challenge from [Metrica Sports](https://metrica-sports.com), FC Barcelona (Barça Innovation Hub) and
[Mobile World Capital Barcelona](https://www.mwcbarcelona.com) for
[More than a Hack 2027](https://landing.mobileworldcapital.com/more-than-a-hack-2027).

This repository is one entrant's experiment: a reproducible pipeline that reads the organisers' automatic
tracking data and writes the submission file, plus the notes, measurements and decisions that go with it.

**Start here:** [`docs/SUMMARY.md`](docs/SUMMARY.md) is a one-page, five-minute read.
The full reasoning is in [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md).

---

## Contents

1. [The task](#the-task)
2. [Current status](#current-status)
3. [Quick start](#quick-start)
4. [How the pipeline works](#how-the-pipeline-works)
5. [Match data](#match-data)
6. [Tools](#tools)
7. [Repository layout](#repository-layout)
8. [Documentation map](#documentation-map)
9. [Reproducibility](#reproducibility)
10. [Continuous integration](#continuous-integration)
11. [Rules that must not be broken](#rules-that-must-not-be-broken)
12. [Working rules](#working-rules)
13. [Key dates](#key-dates)
14. [Licence](#licence)

---

## The task

The organisers provide one complete match with automatic tracking (player and ball positions), automatic
tactical tagging and camera-to-pitch mapping. The job, in one sentence:

> **For every video frame, decide which team has the ball.**

The output is one CSV, `results/DeculGirl.csv`, with the header `frame,label` and **exactly 199,319 data
rows** (video frames 0 to 199,318, 25 frames per second).

| Label | Meaning |
|---|---|
| `H` | Home team (FC Barcelona) has the ball and the ball is live |
| `A` | Away team (Athletic Club) has the ball and the ball is live |
| `D` | Dead ball (out of play, stoppage, restart pending) |
| `X` | No answer. Not a fourth state: the scorer replaces each `X` with the last non-`X` label in the same half |

**Scoring** is automatic: `spellF1`, computed against the organisers' private ground truth for the whole
match. It rewards possessions that are *tidy and unfragmented* rather than per-frame accuracy, so splitting
one possession into two costs a false positive and a false negative at once. Only **158,857 of the 199,319
frames are graded** (two ranges, `(11185, 90652)` and `(110808, 190198)`); labels outside them have no
effect on the score.

Three things are handed in: the CSV, a public repository that reproduces exactly that file, and a short
technical document.

---

## Current status

**The pipeline is a fail-safe, not a smart model yet.** `python run.py` wraps the organisers' official
baseline (the nearest tracked player to the ball, then majority voting over a ±50-frame window) and writes
`X` outside the graded frames. That gives a valid, scoring submission at all times; every improvement is
added on top of it.

| Measure | Value |
|---|---|
| `spellF1`, 5-minute public window (17 possessions) | about 0.33 (0.3256 measured locally) |
| `spellF1`, full match, published baseline floor | 0.2433 |
| Noise band on the full match | ±0.04 (differences below this are not progress) |
| Rows in the submission | 199,319 |

The public window has only 17 possessions, so one missed possession moves `spellF1` by about 6 points.
Use it to confirm the pipeline is *correct*, never to choose between versions.

The four pillars where the baseline is weakest, and where the work goes (details in
[`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 4):

| # | Pillar | Why it matters |
|---|---|---|
| 1 | Dead-ball detection | The baseline cannot recognise a dead ball at all. It is the highest-value part |
| 2 | Ball imputation | The ball position is missing in about 41% of graded frames, often at decisive moments |
| 3 | Team attribution | "Nearest player" ignores distance to several players, movement direction and context |
| 4 | Segmentation | Do not split one possession into fragments |

`src/deculgirl/features/` and `src/deculgirl/model/` are the places for these; they are still empty
packages. What was tried, with numbers and verdicts, goes in [`docs/experiments.md`](docs/experiments.md).

---

## Quick start

Needs **Python 3.9 or newer**. Every command is Python, so it behaves the same on Windows, macOS and Linux.
There are no shell scripts.

```bash
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -r requirements.txt

python tools/fetch_official.py    # download the official repo, pinned to one commit
python run.py                     # build results/DeculGirl.csv
python tools/gate0.py             # validate and score that file
```

| Command | What it does |
|---|---|
| `python tools/fetch_official.py` | Downloads the organisers' repo into `third_party/mtah2027/` at the pinned commit. `--force` refreshes it |
| `python run.py` | Builds the labels from the match data and writes `results/DeculGirl.csv`. Fails with a clear message if the data is missing |
| `python run.py --placeholder` | Writes an all-`X` file that passes validation but scores **0.0000**. For testing the chain only; never submit it |
| `python run.py --window 25` | Changes the majority-voting half-width (default 50 frames) |
| `python run.py --data-dir PATH` | Reads the match bundle from another folder |
| `python tools/gate0.py` | Runs the official validator, then the official scorer, on the public ground truth |
| `python tools/gate0.py --file results/other.csv` | Same, for another file |
| `python tools/gate0.py --bootstrap 1000` | Adds a confidence interval. Run this before concluding one version beats another |

`tools/gate0.py` **does not need the match data**: it scores against the 5 minutes of public ground truth
that ship in the official repo. So the whole `CSV → validation → score` chain can be tested before the data
is downloaded, using `python run.py --placeholder`.

---

## How the pipeline works

```
data/tactical/*_atd.txt, _atd.xml          third_party/mtah2027/starter/baseline.py
              │                                          │
              ▼                                          ▼
   run.py ──► deculgirl.submit.build_labels() ──► nearest player to ball ──► majority vote (±window)
                         │
                         ▼
              _abstain_outside_graded()   X outside the two graded ranges
                         │
                         ▼
              write_submission()          checks the contract, writes the CSV
                         │
                         ▼
              results/DeculGirl.csv  ──►  tools/gate0.py (validate + score)
```

- **`run.py` is the single entry point and does not change.** To change how labels are made, change
  `src/deculgirl/submit.py`. One unchanging command is the cheapest protection for reproducibility.
- **The `build_labels()` contract:** return a 1-D array of exactly 199,319 strings, each one of
  `H`, `A`, `D`, `X`; index `i` is video frame `i`; no empty cells (write `X` to abstain). Breaking it makes
  the validator reject the file and the submission scores zero.
- **The baseline is imported, not copied** from `third_party/mtah2027/starter/baseline.py`, so refreshing the
  official repo also brings in its fixes, and it stays clear that this part is their MIT-licensed code.
- **`write_submission()` enforces the file format:** UTF-8, `\n` line endings, `frame,label` header, and no
  labels outside `H/A/D/X`, so the file is byte-identical on every operating system.
- **`src/deculgirl/__init__.py` holds the match constants** (frame count, frame rate, pitch size, graded
  ranges, public ground-truth window, frame offsets). They come from the official repo; if anything
  conflicts, the official repo is right.

---

## Match data

The data is **not in this repo and must not be.** Put the bundle in `data/`, or point the `MTAH_DATA_DIR`
environment variable at another folder. Expected layout:

```
data/tactical/BAR-ATH_tactical.mp4 | _atd.xml | _atd.txt | _homography.csv | _smart_tagging.xml
data/broadcast/BAR-ATH_broadcast.mp4 | _atd.xml | _atd.txt | _homography.csv
```

The pipeline reads the tactical ATD files (`_atd.txt` and `_atd.xml`); the video is not used. `data/` is in
`.gitignore`, as are `results/`, `third_party/`, `*.csv` and `src/tactical/`. Never commit or upload any of it.

---

## Tools

All of them are plain Python scripts in `tools/`:

| Script | Purpose |
|---|---|
| `fetch_official.py` | Download the official repo at the pinned commit |
| `gate0.py` | Validate and score a submission with the official tools (public ground truth, no match data needed) |
| `show_gt.py` | List the 21 segments (17 possessions, 4 dead-ball blocks) of the public ground truth, to see what has to be guessed |
| `show_frames.py` | Print the tracking file for a range of frames as a readable table (ball position, speed, nearest player), to answer "why is this frame a dead ball?" without opening the video |
| `score_example.py` | A 14-frame worked example of how `spellF1` is computed, for learning. Not part of the pipeline |

```bash
python tools/show_gt.py
python tools/show_frames.py 12840 12900
```

---

## Repository layout

```
run.py                       the single entry point; produces results/DeculGirl.csv
requirements.txt             pinned dependencies
GLOSSARY.md                  standard terms (use them in code, docs and chat)
LICENSE                      MIT, for the code in this repo

src/deculgirl/
  __init__.py                match constants and the submission contract
  submit.py                  data -> labels -> CSV (build_labels, write_submission)
  features/                  data readers, format normalisation, per-frame features   (empty so far)
  model/                     dead ball, team attribution, possession building         (empty so far)

tools/                       the scripts above
metrics/                     measurement tools, regression tests, bootstrap (planned; see metrics/README.md)

docs/
  SUMMARY.md                 one-page summary
  PLAYBOOK.md                the full plan: strategy, measurement, prohibitions, checklist
  possession-rules.md        rules: when a frame is D, and when it is H or A
  experiments.md             experiment log: what was tried, the numbers, the verdict
  decisions.md               decision log; one decision is one row
  gt-public-transitions.md   worksheet of the 21 transitions in the public ground truth
  score-example.md           walkthrough of tools/score_example.py

.github/workflows/validate.yml   CI (see below)

results/                     submission output           (not in git)
third_party/mtah2027/        the official repo, downloaded (not in git)
data/                        the match bundle            (not in git)
```

---

## Documentation map

| If you want to... | Read |
|---|---|
| Understand the task in five minutes | [`docs/SUMMARY.md`](docs/SUMMARY.md) |
| Understand why the strategy is what it is | [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) sections 1–3 |
| Know what is forbidden | [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 6 |
| See the technical plan | [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 4 |
| Measure without fooling yourself | [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 5 |
| Check the submission before handing in | [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 8 |
| Read the rules as code-ready `if ... then ...` | [`docs/possession-rules.md`](docs/possession-rules.md) |
| See what was tried and dropped | [`docs/experiments.md`](docs/experiments.md) |
| See why a decision was made | [`docs/decisions.md`](docs/decisions.md) |
| Look up a term | [`GLOSSARY.md`](GLOSSARY.md) |

The organisers' own `RULES.md`, `CHALLENGE.md`, `EVALUATION.md`, `SUBMISSION.md` and `FAQ.md` are in the
official repo downloaded by `tools/fetch_official.py`. If this repo and the official repo disagree, the
official repo is right.

---

## Reproducibility

Reproducibility is a grading requirement, not a bonus.

- **Pinned dependencies.** `requirements.txt` uses exact versions (`numpy==1.26.4`, `pandas==2.2.2`).
  Adding or bumping one is recorded, with the reason, in `docs/decisions.md`.
- **Pinned official repo.** `tools/fetch_official.py` fetches commit
  `f8f2629ff1e0985f81d7e59d8413678514ee1530`.
- **One command.** `python run.py` always builds the file; its behaviour changes only through
  `src/deculgirl/submit.py`.
- **Deterministic output.** UTF-8, `\n` line endings, fixed header; identical on Windows and Linux.
- **Do not tune on the public window.** The default window of 50 frames is the configuration behind the
  published floor. A window of 125 wins on the public window (0.4242) but loses on the full match
  (0.2242), so tuning there picks the wrong value.

---

## Continuous integration

`.github/workflows/validate.yml` runs on every pull request, on pushes to `main`, and on demand. It
installs the pinned dependencies, fetches the official repo, builds `python run.py --placeholder`, then runs
`python tools/gate0.py`. CI has no match data (it is gated and must never be in the repo), so it tests the
**chain**, not the score: the file must be produced, have the right length and respect the contract. The
real score is measured locally on a machine that has the data.

---

## Rules that must not be broken

Read [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 6 before touching the data. In short:

- **No manual labelling**, in any form and for any purpose: not for the submission, not for training a model,
  not for validating one. Every label must come out of an algorithm.
- **No human-made data about the match**: no event data, no results looked up from memory or elsewhere.
- **No uploading the match data** to a cloud service or a hosted language model.
- **No committing or distributing the data**, or anything derived from it that could reconstruct it.
- **No constants derived from your own observation of the match** without citing an official source.
- **Do not submit the placeholder.** It validates, and scores 0.0000.

---

## Working rules

- **No direct pushes to `main`.** Changes go through a branch and a pull request.
- **`docs/decisions.md` is the only valid source for decisions.** A decision that is not written there is
  treated as not made.
- **Log every experiment** in `docs/experiments.md`: hypothesis first, the result as it is (including the
  bad ones), with numbers from `tools/gate0.py`. Failed experiments are never deleted; they become the
  "tried and dropped" section of the technical document.
- **Use the terms in `GLOSSARY.md`**, so "possession" and "spell" never get confused.

---

## Key dates

| Date | What |
|---|---|
| 14 November 2026 | Code freeze. After this, only fix what is broken |
| 17 November 2026 | Submission deadline |

---

## Licence

The code in this repo is MIT-licensed (see [`LICENSE`](LICENSE)). **The match data is not covered by it.**
That data is licensed separately, only for this competition, under the terms agreed to at registration.

`third_party/mtah2027/` is a copy of the organisers' official repo (MIT-licensed), pinned to commit
`f8f2629ff1e0985f81d7e59d8413678514ee1530` and downloaded with `tools/fetch_official.py`.
