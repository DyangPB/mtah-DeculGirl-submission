# Possession Rules — DeculGirl

Status: `DRAFT`

> This is the most important document in this repo. It has one job: **move the understanding of football
> out of one head and into the repo**, so that the code can be written without anyone having to ask
> again.
>
> If a reader still has to ask "what does this mean?", the document is not finished. The cause is not
> that the reader is slow, but that the sentence is not clear enough.

**How to fill it in:** every rule must be writable in the form `if ... then ...`, and every rule must
have a number. That number is used in commit messages and in `docs/decisions.md`, so when something
changes we know exactly what changed.

---

## 1. Scope

There are only three states. There is no "contested", no "transition", and no "unknown".

| Label | Definition that can be applied in code |
|---|---|
| `H` | Barcelona has the ball **and** the ball is live |
| `A` | Athletic has the ball **and** the ball is live |
| `D` | Dead ball |

`X` is not a fourth state. `X` is the system's decision not to answer. See section 5.

**What is deliberately not asked:** who holds the ball during a dead ball. The tracking data still names
one team when the ball goes out of play (for example the team that will restart play, or the team that
touched it last). But the ground truth throws that information away. During a dead ball the answer is
`D`. Full stop.

---

## 2. What "live ball" and "dead ball" mean

> **Status of this section: HYPOTHESIS.** R-2.1 and R-2.2 come from general understanding of football,
> and have not been verified against the tracking data, because the ATD bundle had not been downloaded.
> How to verify: open the tracking around each `D` block of the public GT (see
> `docs/gt-public-transitions.md`), then change or drop the rules that do not match. All threshold
> numbers are in the parameter table at the end of section 6.

**R-2.1** If the ball is detected, moving faster than `v_still`, and a player is within `d_control` of
it or it is moving between players, then the ball is **live**.

**R-2.2** The ball is **dead** if either of these conditions holds:

- (a) the ball's position is outside the pitch boundary (outside the 0–1 coordinate range) → `D`
- (b) the ball's speed is below `v_still` for at least `T_still` consecutive frames, and the players
  around it are moving slowly or are spread out (a sign the ball has been set for a free kick, goal
  kick, or throw-in) → `D`

A ball that is not detected is **not** evidence of a dead ball. See R-5.1.

**R-2.3** ⚠️ **A dead ball is not always short.** In the 5 minutes of public GT there are three dead
balls that last **20.4 seconds**, **18.3 seconds**, and **14.5 seconds**, making up 17.7% of the graded
window. A normal throw-in lasts only 5–8 seconds, so a dead ball that long is most likely due to an
injury, a substitution, or a VAR check. Any rule that says "the ball will soon be live again" is
**wrong**, and would damage the three most conspicuous moments in that window.

**R-2.4** Weight of each class: `H` 46%, `A` 34%, `D` 20% of graded frames. Class `D` is only **4
segments** out of 21, but contains 1,469 frames. This means one mistake on `D` damages **three**
possessions at once: the two that get cut and the one that appears out of nowhere. Treat `D` as the
class with the highest risk.

---

## 3. What "having the ball" means

`CHALLENGE.md` admits that this part is not very clear, and offers two approaches:

- a player holds the ball for a few seconds
- one team completes more than two consecutive passes

**R-3.1** We chose the first definition: **a player holds the ball**. The "more than two passes"
definition is rejected because it requires detecting passes, and that means building event data, which
we do not have.

A team **has** the ball in a frame if:

- the player nearest to the ball is from that team, **and**
- their distance to the ball is `<= d_control`, **and**
- that condition holds for at least `K_control` consecutive frames.

Distance is computed in metres (0–1 coordinates times the pitch size 105.3 × 68.0). To compare two
teams, use the distance of the 2–3 nearest players of each team, not just the single nearest player
overall. A player moving **towards** the ball is preferred over one who just happens to pass by.

**R-3.2** What is **not** a change of possession (from `CHALLENGE.md`):

- a fleeting touch with no control
- a pass that is only deflected without being intercepted
- an aerial duel won without follow-up control by the winning team

**R-3.3** From tracking data, these three things cannot always be recognised.

| Thing | Recognisable? | What the system does |
|---|---|---|
| Fleeting touch | Partly. The contact is shorter than `K_control` | Ignored by R-3.1 |
| Deflection | Partly. The ball passes at high speed without slowing | Not counted as control |
| Aerial duel | **No.** Ball coordinates do not store height | The old label is kept (R-4.1) until there is evidence the new team has held for `N_switch` frames |

In other words: the system does not try to recognise aerial duels. It only refuses to switch too
quickly.

---

## 4. Possession must persist

A possession is a **state that persists**, not a decision made separately in every frame. A frame is
labelled `H` mostly because the previous frame was `H`.

**R-4.1** If there is not enough evidence from the opposing team, then the label **stays the same** as
the previous frame, with no time limit. A possession does not end because of time, only because of
evidence from the opposing team (R-4.2) or a dead ball (R-2.2). When the two teams are about equally
close (a difference below `distance_margin`), the previous owner is kept.

**R-4.2** If a candidate from the opposing team (per R-3.1) appears **continuously for `N_switch`
frames**, then the label switches. One frame, or a few interrupted frames, is not enough. `N_switch`
must be **below 19**, because the shortest real possession in the public GT is 19 frames.

**R-4.3** When a switch has been confirmed by R-4.2, the start of the new possession is **moved back to
the first frame of the run of evidence**, not to the confirmation frame. Without this, every switch is
late by `N_switch` frames, and a short possession (for example 19 frames) loses half of its content so
that its IoU falls below the threshold. This is safe because processing is done offline over the whole
match.

---

## 5. The `X` policy

The scorer replaces every `X` with the last non-`X` label **in the same half**, before possessions are
built. So `H H H X X X H H H` counts as **one** `H` possession nine frames long.

**`X` is not a give-up button. `X` is the "same as before" button.**

| Situation | Action | Reason |
|---|---|---|
| Ball missing **in the middle of** a possession | `X` | Costs nothing. The possession stays whole. Safer than a guess that could split it |
| When **possession switches to the opposing team** | **Must guess** | `X` pulls the old label into the opposing team's territory, and that is very costly |
| Outside the graded window (frame < 11,185, breaks, > 190,197) | `X` | Not counted at all |

**R-5.1** The system knows whether it is in the middle of a possession or at a switch by **comparing the
two ends of the gap** (a period where the ball is not detected):

- Take the owner **before** the gap (`T_before`) and the first candidate **after** the gap (`T_after`).
- If `T_before == T_after` → write `X` for the whole gap. That is the middle of a possession.
- If `T_before != T_after` → the switch happened **inside** the gap. Must guess. For now, frames in the
  first half of the gap get `T_before` and the second half get `T_after` (the midpoint of the gap).
- If either end has no owner (for example the start of a half) → write `X`.

The midpoint is the weakest guess in this document. It is noted in section 7 so that it is fixed first
once there is player-position data around the gap that can be used.

**R-5.2** A note on cost: `macroF1` counts `X` as wrong, but `macroF1` is only the tiebreaker.
`spellF1`, which decides the ranking, never sees it. So `X` is cheap, and there is no reason to be
stingy with it.

---

## 6. Minimum possession length ⚠️

**A finding that can directly save the score:**

> The shortest possession in the public GT is **19 frames (0.76 seconds)**, and it is a **real**
> possession. The second shortest is 33 frames (1.32 seconds).

The scorer does **not** merge short possessions. If you set an aggressive minimum, for example "merge
anything under 1 second" or "drop anything under 30 frames", you will **delete possessions that really
exist**. One lost possession ≈ **6 points** of `spellF1` on this window.

For comparison, `baseline_raw` reports **131 possessions** for these 5 minutes, when the correct number
is **17**.

**R-6.1** The minimum possession length we chose: **12 frames (0.48 seconds)**. Reason: it must be well
below 19 frames so that real short possessions are not erased, but large enough to remove 1–5 frame
flickers caused by a player who just happens to pass by.

**R-6.2** Fragments shorter than that limit are **merged**, not dropped, and only if they are sandwiched
between two possessions of the same team (the pattern `H A H` becomes `H H H`). If sandwiched by a
different team or by `D`, the fragment is **left alone**.

**R-6.3** Merging **must not cross teams**. Two adjacent `H` and `A` possessions are never merged. In
the pattern `H A H`, only the short `A` fragment changes. A dead ball `D` is never changed.

**Parameter table.** Every number below is a **starting point based on reasoning, not yet verified**.
Do not tune them using the 5-minute public score (only 17 possessions; one missed possession ≈ 6
points). Verify with checks that do not need the correct answer: the number of possessions reported
(the baseline reports 131 for 5 minutes; the correct number is 17), the number of fragments under 19
frames, and `H → A` switches that the data does not support.

| Parameter | Starting point | Used in | Basis |
|---|---|---|---|
| `d_control` | ±2 m | R-2.1, R-3.1 | A reasonable reach for a player controlling the ball. Needs checking in the data |
| `K_control` | 5 frames (0.2 s) | R-3.1 | Filters fleeting touches |
| `N_switch` | 10 frames (0.4 s) | R-4.2 | Must be < 19 |
| `distance_margin` | ±1 m | R-4.1 | Below this counts as level |
| `v_still` | ±1 m/s | R-2.1, R-2.2 | Ball nearly still. Check against the `D` blocks in the GT |
| `T_still` | 25 frames (1 s) | R-2.2 | Separates a truly still ball from a momentary pause |
| `min_possession` | 12 frames | R-6.1 | Must be well < 19 |

---

## 7. Undecided cases

Whenever a situation comes up that is not covered above, **do not improvise in the code**. Write it down
here first, then decide.

| # | Case | Example frame | Decision | Date |
|---|---|---|---|---|
| 1 | The team switch happens inside a ball-missing gap: where is the boundary? | *(find in the data)* | For now the midpoint of the gap (R-5.1). **Not decided**; to be improved first | 26 Oct 2026 |
| 2 | Aerial duel: cannot be recognised from coordinates | *(find in the data)* | Not recognised; kept through R-4.1 and R-4.2 | 26 Oct 2026 |
| 3 | The two teams are equally close to the ball | *(find in the data)* | Keep the previous owner (R-4.1) | 26 Oct 2026 |
| 4 | Start of a half or after a dead ball: no previous owner yet | *(find in the data)* | Use the first candidate that satisfies R-3.1 | 26 Oct 2026 |
| 5 | A long dead ball (14–20 seconds) with the ball still detected | *(find in the public GT)* | **Not decided.** R-2.2(b) may not catch it; check in the data first | 26 Oct 2026 |

---

## 8. Compliance limits

The rules in this document **must not** come from:

- ❌ anyone's memory of the real Barça–Athletic match
- ❌ any match report, news article, or summary
- ❌ event data from any provider (Opta, StatsBomb, Wyscout, LaLiga, or anyone else)
- ❌ manual annotation of any frame

Sources that **are allowed**: **the supplied tracking data, Smart Tagging, and homography · the 5 minutes
of public GT · general understanding of how football works.**

If a rule feels like it "comes from memory", note it in `docs/decisions.md` and ask through the
official issue before using it. `FAQ.md` openly invites this:

> *"If a rule is unclear or your approach sits near a line, ask before you build on it."*
