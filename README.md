# EAS 510 - Assignment 1: Digital Forensics Apprentice

A rule-based expert system that matches modified images back to their originals.

This is the **starter repository** for Project 1. Two repositories matter:

| Repository | Role |
|------------|------|
| `delveccj/EAS510_Assignment1_starter` (this repo) | Your **code** lives here. You will fork it, work in your fork, and push your final submission here. |
| `delveccj/EAS510_Assignment1` | The **dataset** (read-only). Clone it for the images; never commit it to your fork. |

## Setup on your Codio box

```bash
# 1. Fork this repo on GitHub, then in your box:
git clone https://github.com/YOUR-USERNAME/EAS510_Assignment1_starter.git
cd EAS510_Assignment1_starter

# 2. Clone the read-only dataset as a sibling folder (images live there):
cd ~/workspace
git clone https://github.com/delveccj/EAS510_Assignment1.git

# 3. Install dependencies:
cd ~/workspace/EAS510_Assignment1_starter
python3 -m pip install -r requirements.txt

# 4. Point this box at YOUR fork (run once):
./setup_git.sh
```

## Repository layout

```
forensics_detective.py   SimpleDetector: register targets + find_best_match
rules.py                 Rule functions (Rule 1: Metadata, Rule 2: Histogram, Rule 3: Template)
test_system.py           Runs the detector over the data folders and writes results_*.txt
scripts/check_output_format.py   Validates a results file against the required format
setup_git.sh, submit.sh  One-time setup + commit/push helper ("backup button")
```

## The task in one paragraph

Implement three interpretable rules (metadata, color histogram, template matching)
that combine into a 0-100 confidence score. Run your system on `modified_images/`
and `random/` and save the full output as `results_v1.txt`. In Phase 2, run on
`hard/`, diagnose a systematic failure, add a **Rule 4**, and save
`results_v1_hard.txt` and `results_v2.txt`. Full instructions are in the Codio guide
and in the assignment PDF in UBLearns.

## Running

```bash
# Phase 1 (easy + random) -> results_v1.txt
python3 test_system.py --modified --random --output results_v1.txt

# Phase 1 on hard cases -> results_v1_hard.txt
python3 test_system.py --hard --output results_v1_hard.txt

# Phase 2 (everything) -> results_v2.txt
python3 test_system.py --modified --hard --random --output results_v2.txt

# Validate any results file against the required format:
python3 scripts/check_output_format.py results_v1.txt
```

The data folders are resolved from a sibling clone of `EAS510_Assignment1`.
If your data is elsewhere, pass `--data-dir /path/to/EAS510_Assignment1`.

## Output format (do not alter)

```
Processing: modified_image_01.jpg
Rule 1 (Metadata): FIRED - Size ratio 0.85 -> 20/30 points
Rule 2 (Histogram): FIRED - Correlation 0.92 -> 25/30 points
Rule 3 (Template): FIRED - Match score 0.76 -> 30/40 points
Final Score: 75/100 -> MATCH to original_03.jpg
```

## Backup doctrine

Your Codio box can be reset at any time. **Your fork on GitHub is the only safe
copy.** After every milestone run `./submit.sh "describe what you did"`. A box
restart never touches GitHub.

## License

Apache 2.0. See `LICENSE`.
## Phase 2 Reflection

**Failure diagnosed.** V1 falsely rejected cropped and rescaled hard images:
31 of 60 rejected (crop_keep 15/20, crop_offcenter 10/10, resize_scale 6/10),
with zero wrong matches. Example: original_00__crop_offcenter_keep75 scored
28/100 (Rule 1 = 0.39, Rule 2 = 0.93, Rule 3 = 0.14) and was REJECTED even
though the histogram identified the right original.

**Cause.** Rules 1 and 3 depend on file size and on pixel scale/alignment,
which crops destroy. Only the histogram survived, and one rule cannot reach
the 50-point threshold.

**Rule 4 (Features).** SIFT keypoints on CLAHE-normalized grayscale, Lowe ratio
test (0.75), then a RANSAC similarity-transform fit. The score is the number of
geometrically consistent inliers; the rule fires only with at least 10, so
unrelated images score 0. It tolerates crops, scaling and small rotations.

**Reweighting.** Weights are 10/10/20/60 (sum 100). An earlier 15/20/25/40 split
still rejected 25% crops because Rule 4 could not reach 50 alone.

**Results (hard set).**

| Type | V1 correct/wrong/rejected | V2 correct/wrong/rejected |
|---|---|---|
| contrast | 10/0/0 | 10/0/0 |
| crop_keep | 5/0/15 | 18/0/2 |
| crop_offcenter | 0/0/10 | 9/0/1 |
| resize_scale | 4/0/6 | 9/0/1 |
| rotate | 10/0/0 | 10/0/0 |
| Total | 29/0/31 | 56/0/4 |

**Where things ended up.** After the final changes, the system handled all 135 images
without a single wrong match. Every one of the 15 random images was rejected (the
highest score was 21/100), and 12 of the non-random images were rejected when they
shouldn't have been.

The change that made the biggest difference came late. At first I gave Rule 4 full
credit at 30 inliers, but that turned out to be too generous. For modified_04_crop_50pct,
original_00 and original_04 both maxed out at 60, so the two weak rules (size and
histogram) ended up deciding the winner, and they picked the wrong one. Raising full
credit to 60 inliers meant the score now grows with how many keypoints agree, so the
true original pulled ahead and every wrong match disappeared.

The 12 images that are still rejected fall into two groups. Seven involve original_09,
which has very little texture, so SIFT finds too few keypoints to work with. The other
five are 25% crops that keep too little of the image to match reliably. If I had more
time, I would try AKAZE or ORB as a fallback for low-texture images, multi-scale
feature matching, or a quick texture check to decide when SIFT is likely to struggle.

