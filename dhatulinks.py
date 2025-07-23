from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json, os, time

# --------------- SETUP ----------------
# Headless Chrome browser setup
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# Target URL
dhatu_url = "https://ashtadhyayi.com/dhatu"

# Output file path
output_file = os.path.expanduser("~/Desktop/all_dhatu_links.json")
# --------------------------------------

# Load the main dhātu page
driver.get(dhatu_url)
WebDriverWait(driver, 60).until(
    EC.presence_of_element_located((By.CLASS_NAME, "list-group-content"))
)

# Scroll until all dhātu entries load
print("🔄 Scrolling to load all dhātu entries...")
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

print("✅ All dhātu entries should be loaded.")

# Parse the page content
soup = BeautifulSoup(driver.page_source, "html.parser")

# Select all <a> tags with IDs like dhatulist-entry-...
entries = soup.select('a[id^="dhatulist-entry-"]')

# Extract links
links = []
for a in entries:
    href = a.get("href")
    if href:
        full_link = "https://ashtadhyayi.com" + href
        links.append(full_link)

driver.quit()

# Save to JSON file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(links, f, indent=2)

print(f"✅ Extracted {len(links)} dhātu links. Saved to:\n→ {output_file}")
