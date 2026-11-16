# Decision Log — DeculGirl

One decision = one row. Add it **when** the decision is made, not when summarising at the end.

A decision that is only said out loud, or left in a chat, is forgotten within two days and argued about
again next week. This document prevents that. It is also raw material for the technical document and
for any later challenge, because the story cannot be reconstructed from memory.

**Rule:** if a decision is not here, it is treated as not made.

---

## Format

| # | Date | Decision | Reason | Rejected alternatives |
|---|---|---|---|---|

The conditions for being recorded here: the decision is **costly to reverse**, **surprising to someone
without the context**, and **the result of a real trade-off**. If it does not meet all three, do not
record it, because it will change by itself anyway.

---

## Decisions made

### Day 0 — before work started, 24 October 2026

| # | Date | Decision | Reason | Rejected alternatives |
|---|---|---|---|---|
| 001 | 24 Oct 2026 | Enter **Phase 1: Ball Possession** with a target of **the top 20**, but work as if the target were only "hand in a valid submission" | The top 20 is the door to the Innovation Challenge (10 matches and technical mentoring). Safeguards come first because 25 days is short | Going straight for the ranking without safeguards; stopping at just handing something in |
| 002 | 24 Oct 2026 | **Rules and features first, the sequence model afterwards** | Every structural piece can be proven on its own. If an end-to-end model raises the score without us knowing why, nothing can be written in the technical document | Using a model straight away; pure rules with no model |

### Technical decisions

| # | Date | Decision | Reason | Rejected alternatives |
|---|---|---|---|---|
| 003 | 24 Oct 2026 | **No video at all.** No ball detector of our own, no video decoding | `RULES.md` forbids manual annotation "in any amount and for any purpose", including for training a model. So we would have to rely on a model trained by someone else that happens to find the ball, and validate it without ground truth. None of it could be proven correct before the deadline | A self-built ball detector on a 4 GB GPU; local template matching around the estimated ball position |
| 004 | 24 Oct 2026 | **`X` is treated as a merging tool**, not as a plain "no answer": use `X` in the middle of a possession, and always guess when possession switches to the opposing team | The scorer replaces `X` with the last label in the same half before building possessions. Not answering in the middle of a possession costs nothing; not answering at a switch pulls the old label into the opposing team's territory | Not using `X` at all; using `X` as an ordinary "no answer" mark |
| 005 | 24 Oct 2026 | **The minimum possession length must be conservative**, below 19 frames | The shortest possession in the public GT is **19 frames (0.76 seconds)** and it is a real possession. The scorer does not merge short possessions, so an aggressive filter would delete real possessions. One lost possession ≈ 6 points of `spellF1` | A minimum of 1 second / 30 frames; an aggressive median filter |
| 006 | 24 Oct 2026 | **Code freeze on 14 November 2026.** After that, only fix what is broken | Most points are lost in the last 72 hours, and the cause is not the score but a file that used to be valid becoming invalid | Working until the last minute |
| 007 | 24 Oct 2026 | **The 5-minute public window is only for confirming the pipeline is correct**, not for choosing versions | `EVALUATION.md` proves that tuning parameters there picks the wrong baseline: `smooth125` wins on the public window (0.4242) but loses on the full match (0.2242). This is also an official rule, not just advice | Tuning hyperparameters on the public window |
| 008 | 24 Oct 2026 | **Every command is run with Python, not shell scripts.** `python run.py`, `python tools/fetch_official.py`, `python tools/gate0.py` | Development happens on Windows. `run.sh` does not work in cmd/PowerShell, and that difference costs people their first 20 minutes every time | Separate `.sh` and `.bat` files; a Makefile |
| 009 | 24 Oct 2026 | **The official repo is copied as a version-pinned clone** (`third_party/`, in .gitignore, downloaded by `tools/fetch_official.py`), and **its baseline is imported, not copied**, into `submit.py` | `possession_metrics.py` **is** the metric specification. Pinning the version keeps our local numbers from silently changing if the source repo changes. Importing instead of copying makes it clear that what runs is their code (MIT), not ours | Copying the baseline into our code; not using the official repo at all |
| 010 | 24 Oct 2026 | **Every change that enters `main` must have an entry in `docs/experiments.md`** with numbers and a verdict ✅/❌/⚠️ | Work that leaves no trail of numbers is hard to trust. Running experiments is the only way to know whether a change is a real improvement or just a difference inside the noise band. Also, `SUBMISSION.md` requires the technical document to name the assets that were **tried and dropped**. That section is impossible to invent in November, so it must be recorded while the work is going on | Letting experiment notes scatter across chats and memory; inventing the "tried and dropped" section while writing the document |
| 011 | 16 Nov 2026 | **Submit the own pipeline (`tools/make_own.py`), not the baseline wrapper and not a teammate's file** | The baseline wrapper is identical to `baseline_smooth50` on every graded frame (0 differences in 158,857), so it shows no work of our own. The own pipeline differs on 42.1% of graded frames, removes the baseline's fragments (98 → 4 possessions under 19 frames) and agrees 86.6% with an independently built pipeline. It is **not proven** more accurate: on the public 5 minutes spellF1 is 0.3758 vs 0.3256 for the baseline and 0.4457 for the teammate's file, and all three are inside the noise (gaps below ~0.33 with 17 possessions). Dead-ball recall is weak (0.07). Chosen by the author | Submitting the baseline + `X`; submitting the teammate's v2 (better public score, but it is another person's pipeline and was declined) |
| 012 | 16 Nov 2026 | **The own pipeline is a separate variant; `submit.build_labels()` and `run.py` are not changed** | The code freeze (decision 006) was on 14 Nov. Leaving the default path untouched keeps a valid baseline-based submission one command away | Rewiring `build_labels()` |
| 013 | 16 Nov 2026 | **Thresholds of the dead-ball layers come from football/physics and from the tracking's own distribution, never from the public ground truth.** One correction on record: the first quiet-team threshold (1.0 m/s) was too high because the median speed of all tracked players is ~1.35 m/s, giving `D` = 27.7%; lowered to 0.5 m/s | Decision 007 and `RULES.md`. The `D` recall problem was **not** fixed by fitting the four public dead-ball blocks | Tuning on the 4 public `D` blocks |

---

## Template for a new decision

```markdown
| 0XX | DD Mmm 2026 | **<decision in one sentence>** | <why, with the numbers that support it> | <rejected alternative, and why> |
```

If the decision is big and does not fit in one row, create a file in `docs/adr/` named
`00XX-<slug>.md`, one page only, containing the context, the decision, and its consequences. But do not
overdo it: most decisions are fine as one row in the table above.
