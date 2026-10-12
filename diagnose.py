import re, json, collections, sys, os

fn = sys.argv[1]
gt = json.load(open(os.path.expanduser("~/workspace/EAS510_Assignment1/ground_truth.json")))
gt = {os.path.basename(k): v for k, v in gt.items()}

stats = collections.defaultdict(lambda: [0, 0, 0])  # correct, wrong, rejected
cur = None
for line in open(fn):
    m = re.match(r"Processing: (.+)", line)
    if m:
        cur = m.group(1).strip()
    m = re.match(r"Final Score: (\d+)/100 -> (.+)", line)
    if m and cur in gt and "__" in cur:
        kind = re.sub(r"-?\d+", "#", cur.split("__")[1])
        verdict = m.group(2).strip()
        if verdict == "REJECTED":
            stats[kind][2] += 1
        elif gt[cur] in verdict:
            stats[kind][0] += 1
        else:
            stats[kind][1] += 1

print(f"{'type':28} correct wrong rejected")
for k, (c, w, r) in sorted(stats.items()):
    print(f"{k:28} {c:7} {w:5} {r:8}")
