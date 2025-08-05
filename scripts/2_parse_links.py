from tqdm import tqdm
import re

#script to parse the pagelinks sql file into a simpler raw_links.tsv file with resolved redirects

pagelinks_file = "data/enwiki-latest-pagelinks.sql"
page_id_title_file = "data/page_id_title.tsv"
redirect_candidates_file = "data/redirect_candidates.tsv"

raw_links_file = "data/raw_links.tsv"

title_to_id = {}
with open(page_id_title_file, encoding="utf-8") as f:
    for line in f:
        try:
            page_id, title = line.strip().split("\t", 1)
            title_to_id[title] = page_id
        except ValueError:
            continue

#FIXED: REDIRECT MAPPPINGS NOW IGNORED IF THEY POINT TO NON-EXISTENT PAGES
redirect_map = {}
with open(redirect_candidates_file, encoding="utf-8") as f:
    for line in f:
        try:
            redirect_id, title = line.strip().split("\t", 1)
            target_id = title_to_id.get(title)
            if target_id:
                redirect_map[redirect_id] = target_id
        except ValueError:
            continue

print(f"Loaded {len(title_to_id):,} canonical titles")
print(f"Resolved {len(redirect_map):,} redirects")

insert_pattern = re.compile(r"\((\d+),0,(\d+)\)")

count_written = 0
count_skipped = 0

with open(pagelinks_file, "r", encoding="utf-8") as f_in, \
     open(raw_links_file, "w", encoding="utf-8") as f_out:

    for line in tqdm(f_in, desc="Filtering pagelinks.sql"):
        if not line.startswith("INSERT INTO"):
            continue

        for from_id, to_id in insert_pattern.findall(line):
            resolved_to = redirect_map.get(to_id, to_id)
            if resolved_to:
                f_out.write(f"{from_id}\t{resolved_to}\n")
                count_written += 1
            else:
                count_skipped += 1

print(f"Wrote {count_written:,} resolved links to raw_links.tsv")
if count_skipped:
    print(f"Skipped {count_skipped:,} links with unresolved targets")
