"""Start a dedicated ngrok tunnel for the backend, auto-update mobile/.env."""
import subprocess
import sys
import time
import json
import urllib.request
import re
import os

ENV_FILE = os.path.join(os.path.dirname(__file__), "mobile", ".env")

def find_tunnel_for_port(port):
    """Scan ngrok API ports 4040-4045 for a tunnel pointing to the given port."""
    for api_port in range(4040, 4046):
        try:
            url = f"http://localhost:{api_port}/api/tunnels"
            with urllib.request.urlopen(url, timeout=1) as r:
                data = json.loads(r.read())
            for t in data.get("tunnels", []):
                addr = t.get("config", {}).get("addr", "")
                if t.get("proto") == "https" and str(port) in addr:
                    return t["public_url"]
        except Exception:
            pass
    return None

# Start our own ngrok process for port 8000
print("Starting ngrok for port 8000...")
proc = subprocess.Popen(["ngrok", "http", "8000"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting for tunnel URL...")
url = None
for _ in range(20):
    time.sleep(1)
    url = find_tunnel_for_port(8000)
    if url:
        break

if not url:
    print("ERROR: Could not get ngrok tunnel URL for port 8000")
    proc.terminate()
    sys.exit(1)

print(f"Tunnel URL: {url}")

with open(ENV_FILE, encoding="utf-8") as f:
    content = f.read()

content = re.sub(r"EXPO_PUBLIC_API_BASE=.*", f"EXPO_PUBLIC_API_BASE={url}", content)

with open(ENV_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated {ENV_FILE}")
print("Keep this window open while using the app.")
proc.wait()
