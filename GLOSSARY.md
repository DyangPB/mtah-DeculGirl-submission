# More than a Hack 2027 — Phase 1: Ball Possession

The challenge from Metrica Sports, FC Barcelona, and Mobile World Capital: give one ball-possession
label to **every frame** of one LaLiga match (Barça vs Athletic).

This glossary fixes the standard terms used in the docs, the code, and conversation. If you are unsure
what a term means, look here first. The _Avoid_ lines list words that are often used for the same
thing but cause misunderstandings.

## Time and frame numbers

**Video frame**:
The sequence number of a frame in the tactical video, at 25 frames per second (fps), from 0 to 199318.
This is the content of the `frame` column in the submission file.
_Avoid_: frame_id, timestamp, "seconds"

**Frame ID**:
The sequence number of a frame in the ATD tracking file. It starts at 1, so the range is 1–199319.
The conversion formula: `video_frame = frame_id - 1`.
_Avoid_: "frame" on its own without qualification

**Half**:
Half 1 or half 2. The scorer replaces `X` labels per half; a replacement never crosses a half boundary.

**Graded frame**:
A frame that has ground truth, so it counts toward the score. There are 158,857 of the 199,319 frames,
namely the contents of both halves. Breaks and time outside the match are not graded.

**Public window**:
The first 5 minutes of play: video frames 11185–18684, containing 7,500 graded frames and 17
possessions. This is the only ground truth we hold. It is for checking that the pipeline is correct.
Do not use it to rank versions, as training data, or to tune parameters.

**Private ground truth**:
The ground truth for the whole match, held only by the organisers. It decides the ranking.

## State and labels

**Possession**:
A run of consecutive frames with the same label (`H` or `A`) while the ball is live, which ends when the
label changes. A possession is the unit that `spellF1` counts.
_Avoid_: spell, phase, sequence

**Controlled possession**:
Ball possession that counts. A fleeting touch, a ball that only deflects, or an aerial duel with no
follow-up control does not count.

**Change of possession**:
The moment the ball passes to the opposing team, i.e. when an opposing player gains controlled
possession.

**Dead ball** (label `D`):
The ball is not in play. This is a stoppage, not a possession. Who holds the ball during a dead ball is
deliberately not asked.

**Ball alive**:
The ball is in play. Every graded frame with a live ball must be labelled `H` or `A`.

**Stoppage**:
A period of dead ball. It separates two possessions: `H H D D H H` is two possessions, not one.

**Abstention** (label `X`):
The system chooses not to answer for that frame. `macroF1` treats `X` as a wrong answer. `spellF1`
replaces `X` with the last non-`X` label in the same half.

**macroF1**:
The mean F1 over the three classes `H`, `A`, and `D` on graded frames. This score is reported alongside
`spellF1` and is the first tiebreaker when `spellF1` is tied. Noise is about 0.01; the lowest possible
score is about 0.16.

**spellF1**:
The metric that decides the ranking. How it is computed: predicted possessions are matched one-to-one
with real possessions by temporal IoU, then the F1 is averaged over five thresholds
(0.3 / 0.4 / 0.5 / 0.6 / 0.7). Noise is about 0.04 on the full match. The same label for every frame
always scores exactly 0.

**Temporal IoU**:
The ratio between the length of time two spans overlap and the length of their union. It shows how
closely one predicted possession lies over one real possession.

## Data assets

**ATD** (automatic tracking data):
Automatic tracking data from Metrica in the FIFA/EPTS format: one XML file with metadata and one txt
file with the raw data. It holds 25 records per second, with coordinates normalised to the range 0–1
(not metres) and no player identities. There are 199,319 records for the tactical feed and 164,488 for
the broadcast feed.
_Avoid_: "tracking data" without qualification

**Track slot**:
One "place" in the ATD (`Track 1`…`Track 46` on the tactical feed; 51 on the broadcast feed). A slot is
not a specific person and not a shirt number; the player occupying that slot can change from frame to
frame.
_Avoid_: player, shirt number

**Smart Tagging**:
Automatic tactical annotation (SportsCode XML, 638 phases) with tags such as `BUILD UP`, `SET PIECES`,
and `BALL IN THE BOX`. It contains phases of play, not possessions.
_Avoid_: event, possession label

**Homography**:
A 3×3 matrix for each frame that converts normalised pitch coordinates into pixel coordinates on the
image, with a `valid` flag. On the tactical feed it is 100% valid; on the broadcast feed only 65.8%.

**Tactical feed** and **broadcast feed**:
The two supplied videos. The tactical feed's timeline is the reference for the submission. The broadcast
feed has its own timeline (it has cuts and replays), so its frame numbers do not match the tactical
feed's.
_Avoid_: "the main video" without saying which one

**Baseline floor**:
`baseline_smooth50` with a `spellF1` of 0.2433 on the full match. This is the minimum number that has to
be beaten.
