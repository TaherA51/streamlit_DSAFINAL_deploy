from tqdm import tqdm #(THIS MODULE IS FOR PROGRESS BARS DO NOT REMOVE.)
import os

#script to convert the top 100k links found in earlier steps into a usable graph.csv file for c++ code

top_ids = set()
with open("data/top100k.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            top_ids.add(line)

print(f"Loaded {len(top_ids):,} top page IDs.")

raw_links_path = "data/raw_links.tsv"
print("Counting total lines...")
with open(raw_links_path, "r", encoding="utf-8") as f:
    total_lines = sum(1 for _ in f)

#progress bar so time estimate is possible
edges = set()
skipped = 0
examples = set()

with open(raw_links_path, "r", encoding="utf-8") as f:
    for line in tqdm(f, desc="Processing raw_links.tsv", total=total_lines):
        line = line.strip()
        if "\t" not in line:
            continue
        from_id, to_id = line.split("\t", 1)

        if from_id not in top_ids or to_id not in top_ids:
            skipped += 1
            if len(examples) < 10:
                examples.add(to_id)
            continue

        edges.add((from_id, to_id))

print(f"Collected {len(edges):,} valid edges.")
print(f"Skipped {skipped:,} links due to missing or non-top100k pages.")
if examples:
    print("Sample of unmatched to_id values:")
    for example in sorted(examples):
        print(f"  → '{example}'")

with open("data/graph.csv", "w", encoding="utf-8") as f_out:
    for a, b in edges:
        weight = 1 if (b, a) not in edges else 2
        f_out.write(f"{a},{b},{weight}\n")

print(f"Finished exporting graph.csv with {len(edges):,} edges.")
