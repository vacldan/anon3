import json
data = json.load(open("_agent_reports/test_results.json", "r", encoding="utf-8"))
print(f"Total: {data['summary']['total']}, Passed: {data['summary']['passed']}, "
      f"Failed: {data['summary']['failed']}, Avg: {data['summary']['avg_score']}")
for r in data["results"]:
    print(f"  {r['file']}: {r['score']}/10")
