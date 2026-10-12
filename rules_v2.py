"""EAS 510 - Project 1 - Phase 2: V2 rule set.

Diagnosis: V1 falsely rejects cropped and rescaled suspects (31/60 hard
images). Rules 1 and 3 depend on matching size/scale, which crops destroy.
Rule 4 uses SIFT keypoints + RANSAC, which is scale/crop/rotation tolerant.
Weights: 15 + 20 + 25 + 40 = 100.
"""

from functools import lru_cache

import cv2
import numpy as np

import rules

RULES = ("rule1_metadata_v2", "rule2_histogram_v2",
         "rule3_template_v2", "rule4_features")

W1, W2, W3, W4 = 10, 10, 20, 60

MIN_INLIERS = 10    # fewer RANSAC inliers than this -> rule does not fire
INLIER_FULL = 60
RATIO = 0.75        # Lowe ratio test


def _rescaled(fn, out_of):
    """Reuse a V1 rule with a smaller point budget."""
    def wrapper(target, input_path):
        r = dict(fn(target, input_path))
        r["out_of"] = out_of
        r["score"] = int(round(r["metric"] * out_of)) if r["fired"] else 0
        return r
    return wrapper


rule1_metadata_v2 = _rescaled(rules.rule1_metadata, W1)
rule2_histogram_v2 = _rescaled(rules.rule2_histogram, W2)
rule3_template_v2 = _rescaled(rules.rule3_template, W3)

_sift = None
_matcher = cv2.BFMatcher(cv2.NORM_L2)


def _get_sift():
    global _sift
    if _sift is None:
        _sift = cv2.SIFT_create(nfeatures=1000)
    return _sift


@lru_cache(maxsize=128)
def _features(path):
    img = rules._arr(path)
    if img is None:
        return None
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    s = 640.0 / max(h, w)
    if s < 1:
        g = cv2.resize(g, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    g = cv2.createCLAHE(2.0, (8, 8)).apply(g)   # tolerate contrast/brightness shifts
    kp, des = _get_sift().detectAndCompute(g, None)
    if des is None or len(kp) < 2:
        return None
    pts = np.float32([k.pt for k in kp])
    return pts, des


def rule4_features(target, input_path):
    """SIFT + ratio test + RANSAC similarity transform; score = inlier count."""
    out = {"rule": 4, "name": "Features", "fired": False, "score": 0,
           "out_of": W4, "note": "Feature match 0.00", "metric": 0.0}
    try:
        a, b = _features(target["path"]), _features(input_path)
        if a is None or b is None:
            return out
        (pa, da), (pb, db) = a, b
        pairs = _matcher.knnMatch(db, da, k=2)
        good = [p[0] for p in pairs
                if len(p) == 2 and p[0].distance < RATIO * p[1].distance]
        inliers = 0
        if len(good) >= 8:
            src = pb[[m.queryIdx for m in good]].reshape(-1, 1, 2)
            dst = pa[[m.trainIdx for m in good]].reshape(-1, 1, 2)
            _, mask = cv2.estimateAffinePartial2D(
                src, dst, method=cv2.RANSAC, ransacReprojThreshold=4.0)
            if mask is not None:
                inliers = int(mask.sum())
        metric = min(1.0, inliers / INLIER_FULL)
        out["metric"] = round(metric, 3)
        out["note"] = f"Feature match {out['metric']:.2f}"
        if inliers >= MIN_INLIERS:
            out["fired"] = True
            out["score"] = int(round(W4 * metric))
    except Exception:
        pass
    return out
