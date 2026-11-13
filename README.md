# DeculGirl — More than a Hack 2027, Phase 1

Label ball possession **for every frame** of one complete LaLiga match
(**FC Barcelona vs Athletic Club**, LaLiga EA Sports 2024-25 matchday 2).

A challenge from [Metrica Sports](https://metrica-sports.com), FC Barcelona (Barça Innovation Hub), and
[Mobile World Capital Barcelona](https://www.mwcbarcelona.com) for
[More than a Hack 2027](https://landing.mobileworldcapital.com/more-than-a-hack-2027).

The end result is one `frame,label` file with **199,319 rows**, using the labels `H` / `A` / `D` / `X`.
Scoring is automatic, using **`spellF1`**, compared against the organisers' private ground truth for the
whole match.

**Start here:** **[`docs/SUMMARY.md`](docs/SUMMARY.md)** — one page, five minutes to read. The full
explanation is in **[`docs/PLAYBOOK.md`](docs/PLAYBOOK.md)**.

---

## How to run

Needs **Python 3.9 or newer**. Every command uses Python so it behaves identically on Windows, macOS, and
Linux. There are no shell scripts.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

python tools/fetch_official.py    # download the official repo (pinned to a specific commit)
python run.py                     # produce results/DeculGirl.csv
python tools/gate0.py             # validate and score that file
```

**`python tools/gate0.py` can run without the match data.** It uses the 5 minutes of public ground truth
that ship in the official repo. So you can confirm that the whole `CSV → validation → score` chain works
even before the match data has been downloaded (use `python run.py --placeholder` to produce a valid
empty file for that).

### Match data

The data is **not in this repo and must not be.** Put the data bundle in the `data/` folder, or point the
`MTAH_DATA_DIR` environment variable at another folder. The layout:

```
data/tactical/BAR-ATH_tactical.mp4 | _atd.xml | _atd.txt | _homography.csv | _smart_tagging.xml
data/broadcast/BAR-ATH_broadcast.mp4 | _atd.xml | _atd.txt | _homography.csv
```

The `data/` folder is already in `.gitignore`. Never commit its contents.

---

## Folder layout

```
docs/
  SUMMARY.md               one-page summary — start here if you only have 5 minutes
  PLAYBOOK.md              the full plan: strategy, measurement, prohibitions, checklist
  possession-rules.md      RULES: when it is D, when it is H/A
  experiments.md           EXPERIMENT LOG: what was tried, the numbers, the verdict
  gt-public-transitions.md worksheet of the 21 transitions in the public GT
  decisions.md             decision log. One decision = one row
  score-example.md         walkthrough of the mini example tools/score_example.py (for learning)
src/deculgirl/
  submit.py                data -> CSV submission
  features/                data readers, format normalisation, per-frame features
  model/                   dead ball, team attribution, possession building
metrics/                   measurement tools, regression tests, bootstrap
tools/
  fetch_official.py        download the official repo at the pinned commit
  gate0.py                 validate and score (uses the public GT)
  score_example.py         14-frame mini example for learning spellF1 (not part of the pipeline)
results/                   submission output (not in git)
third_party/mtah2027/      the downloaded official repo (not in git)
data/                      match bundle (not in git)
```

`GLOSSARY.md` in the root folder holds the standard terms. Use them in code, docs, and chat, so there is
no misunderstanding, for example between "possession" and "spell".

---

## Working rules

- **No direct pushes to `main`.** Changes go through a branch and a pull request (PR).
- **`docs/decisions.md` is the only valid source for decisions.** A decision that is not written there is
  treated as not made.
- **Automatic checks run on every PR** (`.github/workflows/validate.yml`).
- **Manual labelling is forbidden, in any form and for any purpose.** Read
  [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md) section 6 before touching the data.

---

## Licence

The code in this repo is MIT-licensed (see [`LICENSE`](LICENSE)). **The match data is not covered by it.**
That data is licensed separately, only for this competition, under the terms agreed to at registration.

`third_party/mtah2027/` is a copy of the organisers' official repo (MIT-licensed), pinned to commit
`f8f2629ff1e0985f81d7e59d8413678514ee1530`. It is downloaded with `tools/fetch_official.py`.
