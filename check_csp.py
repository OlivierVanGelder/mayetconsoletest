import json, os, re, sys, time, urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = sys.argv[1] if len(sys.argv) > 1 else "https://mayetmediators.nl"
WEBHOOK = os.environ.get("N8N_WEBHOOK_URL")

# Regex voor CSP-fouten
CSP_RE = [
    re.compile(r"Refused to load .* violates .* Content Security Policy", re.I),
    re.compile(r"violates the following Content Security Policy", re.I),
    re.compile(r"Content Security Policy.*violat", re.I),
    re.compile(r"\bcsp\b.*violat", re.I),
]
def is_csp(txt: str) -> bool:
    return any(r.search(txt) for r in CSP_RE)
def is_noise(txt: str) -> bool:
    return "ERR_BLOCKED_BY_CLIENT" in txt

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
# Optioneel: eenvoudige mobielprofiel om je iPhone-situatie te benaderen
# opts.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
# Browserconsole logs aan in Selenium 4
opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

driver = webdriver.Chrome(options=opts)

nav_error = None
logs = []
try:
    driver.set_page_load_timeout(25)
    driver.get(URL)
    time.sleep(2.5)  # korte extra wacht voor late console output
    for entry in driver.get_log("browser"):
        logs.append({
            "type": entry.get("level", "LOG").lower(),
            "text": entry.get("message", ""),
            "ts": entry.get("timestamp")
        })
except Exception as e:
    nav_error = str(e)
finally:
    driver.quit()

hits = [m for m in logs if m["type"] in ["severe", "error"] and not is_noise(m["text"]) and is_csp(m["text"])]

payload = {
    "url": URL,
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "navError": nav_error,
    "cspCount": len(hits),
    "cspErrors": hits,
    "consoleAll": len(logs)
}

print(json.dumps(payload))

# Post naar n8n Webhook
if WEBHOOK:
    req = urllib.request.Request(
        WEBHOOK,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        resp.read()
