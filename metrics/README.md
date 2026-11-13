# metrics/

Measurement tools, a regression suite (tests that catch results getting worse), and diagnostic tools.

## Why this folder exists

> The key to the ranking in this competition is in your hands: **the scorer you run on your own computer
> is the scorer that decides the ranking.** In the words of `EVALUATION.md`:
> *"Organisers run this exact script against the private full-match ground truth; the published board
> is its output. There is no stricter version held back."*

This is a big advantage, but it is only useful if it is used with discipline. This folder is what keeps
that discipline.

It is also the path that must not break: if nobody can run this folder, nobody can reproduce the
submission file, and that disqualifies the entry rather than merely costing points. So build it early,
**freeze** it once it is green, and **automate** its checks through CI.

## Planned contents

| File | Purpose |
|---|---|
| `regression.py` | Runs a set of submissions and compares them with the last known result. Catches regressions you did not notice |
| `compare.py` | Compares two versions with `--bootstrap 1000`, then reports whether the intervals overlap. **This tool stops you from fooling yourself** |
| `diagnose.py` | Summarises `reports/<name>_transitions.csv` from the official evaluator: which are `matched`, `missed`, and `spurious` |
| `ci.py` | Runs the same checks as `.github/workflows/validate.yml`, but on the local machine |

## Three measurement rules

1. **Noise band on the full match: `spellF1` ≈ 0.04 · `macroF1` ≈ 0.01.**
   A difference below that is not progress. Do not celebrate it and do not chase it.
2. **Always run `--bootstrap 1000` before believing that one version is better.**
   Usually the intervals overlap. If they overlap, pick the simpler version and stop there.
3. **The 5-minute public window is not a leaderboard.** It has only 17 possessions, and one missed
   possession ≈ 6 points. `EVALUATION.md` proves that tuning parameters there picks the wrong baseline.
   Use it only to confirm that the pipeline is **correct**: frame numbers are aligned, the file follows
   the requested format, and labels mean what you think they mean.

## One thing few people know

The official evaluator writes `reports/<name>_transitions.csv`, a list of every transition together with
its status (`matched` / `missed` / `spurious`) for every video frame. It is the best debugging tool
available, and it is free. Use `diagnose.py` to read it.
