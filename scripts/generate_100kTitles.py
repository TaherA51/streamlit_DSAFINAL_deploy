#script to generate the respective titles for the top 100k page ids

input_tsv = "data/page_id_title.tsv"
top_ids_file = "data/top100k.txt"
output_file = "data/top100k_id_title.tsv"

with open(top_ids_file, "r", encoding="utf-8") as f:
    top_ids = set(line.strip() for line in f if line.strip().isdigit())

matched = 0
skipped = 0

with open(input_tsv, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line_num, line in enumerate(f_in, 1):
        line = line.strip()
        if not line or "\t" not in line:
            skipped += 1
            continue
        try:
            page_id, title = line.split("\t", 1)
        except ValueError:
            skipped += 1
            continue
        if page_id in top_ids:
            f_out.write(f"{page_id}\t{title}\n")
            matched += 1

print(f" Saved {matched:,} entries to {output_file}")
if skipped:
    print(f"Skipped {skipped:,} malformed or unmatched lines")
