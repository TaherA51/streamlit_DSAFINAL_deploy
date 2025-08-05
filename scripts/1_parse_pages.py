from tqdm import tqdm

#script to parse the page sql file into two simpler tsv files: one mapping page_id to title for non-redirects, and one listing redirect candidates to resolve later.

input_file = "data/enwiki-latest-page.sql"
output_file_main = "data/page_id_title.tsv"      
output_file_redirects = "data/redirect_candidates.tsv"  

with open(input_file, "r", encoding="utf-8") as f_in, \
     open(output_file_main, "w", encoding="utf-8") as f_main, \
     open(output_file_redirects, "w", encoding="utf-8") as f_redirects:

    for line in tqdm(f_in, desc="Filtering page.sql"):
        if not line.startswith("INSERT INTO"):
            continue

        values = line.split("VALUES", 1)[-1].strip().rstrip(";")
        entries = values.split("),(")
        entries[0] = entries[0].lstrip("(")
        entries[-1] = entries[-1].rstrip(")")

        for row in entries:
            parts = row.split(",", 4) 

            if len(parts) < 4:
                continue

            page_id = parts[0].strip()
            namespace = parts[1].strip()
            title_raw = parts[2].strip()
            is_redirect = parts[3].strip()

            if namespace != "0":
                continue  

            title = title_raw.strip("'").replace("\\'", "'").replace("_", " ")

            if is_redirect == "1":
                f_redirects.write(f"{page_id}\t{title}\n")
            else:
                f_main.write(f"{page_id}\t{title}\n")
