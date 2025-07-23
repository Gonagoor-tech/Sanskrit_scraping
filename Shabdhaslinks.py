from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json, os, time

# Setup headless browser
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Load the main page
driver.get("https://ashtadhyayi.com/shabda")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CLASS_NAME, "list-group-content"))
)

# Scroll until all entries are loaded
print("🔄 Scrolling to load all entries...")
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

print("✅ All shabda entries should be loaded.")

# Parse and collect links
soup = BeautifulSoup(driver.page_source, "html.parser")
entries = soup.select('div[id^="shabdalist-entry-"]')
links = []
for e in entries:
    data_nav = e.get("data-nav")
    if data_nav:
        links.append("https://ashtadhyayi.com" + data_nav)

driver.quit()

# Save to JSON
output_file = os.path.expanduser("~/Desktop/all_shabda_links.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(links, f, indent=2)

print(f"✅ Extracted {len(links)} shabda links. Saved to:\n→ {output_file}")
