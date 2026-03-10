import json, re
from run_anonymize_tests import OUT_DIR, get_all_text_from_docx

anon = get_all_text_from_docx(OUT_DIR / "smlouva0_anon.docx")
mjson = json.load(open(OUT_DIR / "smlouva0_map.json", encoding="utf-8"))

tags_text = sorted(set(re.findall(r"\[\[[A-Z_]+_\d+\]\]", anon)))
tags_map = sorted({e.get("tag", "").strip() for e in mjson.get("entities", []) if e.get("tag")})
orphans = sorted(set(tags_text) - set(tags_map))

print(f"Tags in text: {len(tags_text)}")
print(f"Tags in map:  {len(tags_map)}")
print(f"Orphans:      {len(orphans)}")
print()
for o in orphans[:15]:
    idx = anon.find(o)
    ctx = anon[max(0, idx - 30) : idx + len(o) + 30].replace("\n", " ")
    print(f"  {o} -> ...{ctx}...")
print()
print("Sample text tags:", tags_text[:15])
print("Sample map tags: ", tags_map[:15])
