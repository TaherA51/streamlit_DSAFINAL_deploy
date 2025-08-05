#script to filter the top 100k articles using harmonic mean calculation formula.
from collections import defaultdict
from tqdm import tqdm #(THIS MODULE IS FOR PROGRESS BARS DO NOT REMOVE.)

link_file = "data/raw_links.tsv"
output_file = "data/top100k.txt"

in_deg = defaultdict(int)
out_deg = defaultdict(int)

with open(link_file, encoding="utf-8") as f:
    lines = sum(1 for _ in f)

with open(link_file, encoding="utf-8") as f:
    for line in tqdm(f, total=lines, desc="Counting degrees"):
        if '\t' not in line:
            continue
        src, dst = line.strip().split('\t', 1)
        out_deg[src] += 1
        in_deg[dst] += 1

all_nodes = set(in_deg) | set(out_deg)
scores = {}

for node in tqdm(all_nodes, desc="Scoring nodes"):
    indeg = in_deg.get(node, 0)
    outdeg = out_deg.get(node, 0)
    if indeg + outdeg == 0:
        continue
    scores[node] = (2 * indeg * outdeg) / (indeg + outdeg)

top_k = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:100_000]
top_ids = [node for node, _ in top_k]

with open(output_file, "w", encoding="utf-8") as f_out:
    for pid in top_ids:
        f_out.write(pid + "\n")

print(f"Wrote {len(top_ids):,} node IDs to {output_file}")
