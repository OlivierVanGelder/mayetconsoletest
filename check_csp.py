import json, os, sys, time, urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = sys.argv[1] if len(sys.argv) > 1 else "https://mayetmediators.nl"
WEBHOOK = os.environ.get("N8N_WEBHOOK_URL")

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
# optioneel: mobielprofiel, zelfde als jouw test
opts.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

driver = webdriver.Chrome(options=opts)

nav_error = None
logs = []

try:
    driver.set_page_load_timeout(25)
    driver.get(URL)
    time.sleep(3)  # korte wachttijd voor late console output
    for entry in driver.get_log("browser"):
        logs.append({
            "type": entry.get("level", "LOG").lower(),
            "text": entry.get("message", ""),
            "timestamp": entry.get("timestamp")
        })
except Exception as e:
    nav_error = str(e)
finally:
    driver.quit()

payload = {
    "url": URL,
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "navError": nav_error,
    "consoleAll": len(logs),
    "messages": logs
}

print(json.dumps(payload))

if WEBHOOK:
    try:
        req = urllib.request.Request(
            WEBHOOK,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            print(f"Webhook POST -> {resp.getcode()}")
    except Exception as e:
        print(f"Webhook POST failed: {e}")
        sys.exit(1)
