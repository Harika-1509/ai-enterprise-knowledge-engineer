"""
Tests the /ask/stream SSE endpoint directly via httpx, bypassing
PowerShell's curl quoting issues entirely.
Run with: python test_streaming.py
"""

import httpx

BASE_URL = "http://127.0.0.1:8000"

# Paste a fresh token here (login via Swagger if this one has expired)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZmU4YzAxZC1iNjFiLTRmMDQtYjZmYy0xZDM3OGY3MTNjMjciLCJleHAiOjE3ODQxMTMyMTl9.Qo0zygn2HNzM4JVY6Xl09jFUjYhaxBc_0ZBoZe7YeZ8"

QUERY = "What is the full form of OCR used here?"

payload = {"query": QUERY, "limit": 5}
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

print(f"Streaming answer for: {QUERY}\n")
print("-" * 60)

token_count = 0
full_text = ""

with httpx.stream(
    "POST", f"{BASE_URL}/api/v1/ask/stream", json=payload, headers=headers, timeout=60.0
) as response:
    if response.status_code != 200:
        print(f"ERROR: status {response.status_code}")
        print(response.read())
        exit(1)

    for line in response.iter_lines():
        if not line or not line.startswith("data:"):
            continue

        import json
        data = json.loads(line[len("data:"):].strip())

        if data["type"] == "token":
            print(data["content"], end="", flush=True)
            full_text += data["content"]
            token_count += 1
        elif data["type"] == "citations":
            print("\n" + "-" * 60)
            print(f"CITATIONS ({len(data['citations'])}):")
            for c in data["citations"]:
                print(f"  [Source {c['source_number']}] {c['filename']} ({c.get('location')})")
        elif data["type"] == "done":
            print("\n" + "-" * 60)
            print(f"STREAM COMPLETE - {token_count} token chunks received")

print(f"\nFull assembled answer:\n{full_text}")