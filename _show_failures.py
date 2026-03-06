import json

data = json.load(open("_agent_reports/test_results.json", "r", encoding="utf-8"))
for r in data["results"]:
    if r["score"] < 10:
        print(f"\n=== {r['file']}: score={r['score']} ===")
        for leak in r.get("pii_leaks", []):
            print(f"  {leak}")
