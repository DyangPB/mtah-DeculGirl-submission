"""A tiny end-to-end example: position data -> guesses -> possessions -> score.

This script is for LEARNING, not part of the submission pipeline. The data is
made up (14 frames), so every step can be read and computed by hand.

    python tools/score_example.py                  # with clean-up (min-spell 2)
    python tools/score_example.py --min-spell 1    # no clean-up, watch the score drop
    python tools/score_example.py --min-spell 3    # more aggressive clean-up

The flow is the same as the real one:

    position data -> features -> per-frame guess -> clean up into possessions
                  -> fill X (done by the scorer) -> compute spellF1

The scoring mimics the logic of the official scorer
(``third_party/mtah2027/evaluation/possession_metrics.py``): possessions are
matched one-to-one within the same team, in order of largest IoU, and count as
a match when IoU >= the threshold. The official scorer still decides the real
number.
"""

import argparse
import sys

# Windows often uses a default encoding that is not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IOU_THRESHOLDS = (0.3, 0.4, 0.5, 0.6, 0.7)

# --- 1. Made-up data ---------------------------------------------------------
# One row per frame:
#   (ball_detected, nearest_player_team, ball_speed, players_walking)
# In the real data these come from ATD (x, y positions of the ball and players
# per frame).
DATA = [
    (True,  "H", 5.0, False),   # frame 0
    (True,  "H", 5.0, False),   # frame 1
    (False, None, None, None),  # frame 2: ball not detected
    (True,  "H", 5.0, False),   # frame 3
    (True,  "A", 5.0, False),   # frame 4: an Athletic player happens to pass by
    (True,  "H", 5.0, False),   # frame 5
    (True,  "H", 5.0, False),   # frame 6
    (True,  "H", 0.1, True),    # frame 7: ball almost still, players walking
    (True,  "A", 0.1, True),    # frame 8
    (True,  "A", 0.1, True),    # frame 9
    (True,  "A", 5.0, False),   # frame 10
    (True,  "A", 5.0, False),   # frame 11
    (True,  "A", 5.0, False),   # frame 12
    (True,  "A", 5.0, False),   # frame 13
]

# The true answer. In the competition the organisers keep this and we never see it.
TRUE_LABELS = list("HHHHHHH" + "DDD" + "AAAA")


# --- 2. The rule (what possession-rules.md writes down) -----------------------
def guess_one_frame(ball_detected, nearest_team, ball_speed, players_walking):
    """If the ball is missing -> X. If the ball is almost still and players are
    walking -> D. Otherwise, the team of the nearest player has the ball."""
    if not ball_detected:
        return "X"          # no guess; the scorer will fill it with the previous label
    if ball_speed < 1.0 and players_walking:
        return "D"
    return nearest_team


# --- 3. Clean-up (anti-fragmentation) -----------------------------------------
def segments(labels):
    """List of (start, end, label), end exclusive. Consecutive equal labels = one segment."""
    result, start = [], 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            result.append((start, i, labels[start]))
            start = i
    return result


def fill_x(labels):
    """Mimic the scorer: X is replaced by the previous non-X label; at the start
    it is filled with the first non-X label."""
    result = list(labels)
    first = next((x for x in result if x != "X"), None)
    last = first
    for i, x in enumerate(result):
        if x == "X":
            result[i] = last
        else:
            last = x
    return result


def clean_up(labels, min_spell):
    """A short possession sandwiched between the opposing team is changed to
    follow the team around it.

    Only changes H/A segments sandwiched between two segments of the same team.
    A dead ball (D) is never changed. min_spell=1 means no clean-up at all.

    Note: the real data has possessions as short as 19 frames that are genuine,
    so the real min_spell value must be small, and ideally use the strength of
    the evidence, not length alone.
    """
    filled = fill_x(labels)
    segs = segments(filled)
    for i in range(1, len(segs) - 1):
        start, end, team = segs[i]
        before, after = segs[i - 1][2], segs[i + 1][2]
        if team in "HA" and end - start < min_spell and before == after and before in "HA":
            for k in range(start, end):
                filled[k] = before
    # An original X is still written as X in the file; the scorer fills it in.
    return [("X" if original == "X" else new) for original, new in zip(labels, filled)]


# --- 4. spellF1 score ---------------------------------------------------------
def possessions(labels):
    return [s for s in segments(labels) if s[2] in "HA"]


def iou(a, b):
    intersection = min(a[1], b[1]) - max(a[0], b[0])
    union = max(a[1], b[1]) - min(a[0], b[0])
    return intersection / union


def spell_score(truth, guess):
    """Return (mean F1, per-threshold breakdown). X is filled before computing."""
    gt, pred = possessions(fill_x(truth)), possessions(fill_x(guess))
    pairs = sorted(
        ((iou(g, p), i, j)
         for i, g in enumerate(gt) for j, p in enumerate(pred)
         if g[2] == p[2] and p[1] > g[0] and g[1] > p[0]),
        key=lambda t: (-t[0], t[1], t[2]),
    )
    breakdown, f1_list = [], []
    for threshold in IOU_THRESHOLDS:
        used_gt, used_pred = set(), set()
        for value, i, j in pairs:
            if value < threshold:
                break
            if i in used_gt or j in used_pred:
                continue
            used_gt.add(i)
            used_pred.add(j)
        correct = len(used_gt)
        wrong = len(pred) - correct      # guesses with no match (fp)
        missed = len(gt) - correct       # real possessions not detected (fn)
        f1 = 2 * correct / (2 * correct + wrong + missed) if (2 * correct + wrong + missed) else 0.0
        breakdown.append((threshold, correct, wrong, missed, f1))
        f1_list.append(f1)
    return sum(f1_list) / len(f1_list), breakdown


# --- 5. Run everything --------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--min-spell", type=int, default=2,
                        help="possessions shorter than this (and sandwiched by the same team) "
                             "are cleaned up. 1 = no clean-up. Default: 2")
    args = parser.parse_args()

    raw = [guess_one_frame(*row) for row in DATA]
    final = clean_up(raw, args.min_spell)

    print("STEPS 1-2. Data -> per-frame guess")
    print("frame  ball   nearest   speed      walking  guess    true")
    for i, (row, g, t) in enumerate(zip(DATA, raw, TRUE_LABELS)):
        detected, team, speed, walking = row
        print(f"{i:>5}  {'yes' if detected else 'NO':<5}  {str(team or '-'):<8}  "
              f"{str(speed if speed is not None else '-'):<9}  {str(walking if walking is not None else '-'):<7}  "
              f"{g:<7}  {t}")

    print("\nSTEP 3. After clean-up (min-spell =", args.min_spell, ")")
    print("raw guess   :", " ".join(raw))
    print("cleaned up  :", " ".join(final))
    print("true labels :", " ".join(TRUE_LABELS))

    filled = fill_x(final)
    correct_frames = sum(p == t for p, t in zip(filled, TRUE_LABELS))
    print(f"\nPer-frame accuracy (after X is filled): {correct_frames}/{len(filled)} "
          f"= {correct_frames / len(filled):.0%}")

    print("\nSTEP 4. Possessions")
    print("true possessions   :", [f"{t}[{a}-{b - 1}]" for a, b, t in possessions(TRUE_LABELS)])
    print("guessed possessions:", [f"{t}[{a}-{b - 1}]" for a, b, t in possessions(filled)])

    mean, breakdown = spell_score(TRUE_LABELS, final)
    print("\nSTEP 5. spellF1")
    print("threshold  correct  wrong_guesses  missed    F1")
    for threshold, correct, wrong, missed, f1 in breakdown:
        print(f"{threshold:>9}  {correct:>7}  {wrong:>13}  {missed:>6}  {f1:.2f}")
    print(f"\nspellF1 = {mean:.4f}")

    print("\nThe submitted CSV file looks like this:")
    print("frame,label")
    for i, x in enumerate(final):
        print(f"{i},{x}")


if __name__ == "__main__":
    main()
