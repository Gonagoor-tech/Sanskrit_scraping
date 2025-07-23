from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import time
import json

# ----------- SETTINGS -------------
START_INDEX = 0     # Change this to your starting index (e.g. 0, 1000, 2000...)
END_INDEX = 10      # Change this to your ending index (e.g. 1000, 2000, 3000...)
LINK_FILE = os.path.expanduser("~/Desktop/all_shabda_links.json")
OUTPUT_FILE = os.path.expanduser(f"~/Desktop/shabda_output_{START_INDEX}_{END_INDEX}.txt")
WAIT_TIME = 40
SLEEP_BETWEEN_REQUESTS = 1.5
# ----------------------------------

# Load full link list
with open(LINK_FILE, "r", encoding="utf-8") as f:
    all_links = json.load(f)

# Subset your range
subset_links = all_links[START_INDEX:END_INDEX]
print(f"🔍 Scraping links {START_INDEX} to {END_INDEX} (Total: {len(subset_links)})")

# Setup headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

results = []

for idx, link in enumerate(subset_links, START_INDEX):
    print(f"🔗 Scraping {idx}: {link}")
    try:
        driver.get(link)
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table-bordered"))
        )
    except Exception as e:
        print(f"⚠️ Timeout or error on: {link}")
        results.append(f"{link}\n⚠️ Timeout or error loading table.\n{'-'*60}\n")
        continue

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ---- Header Extraction ----
    header_div = soup.find("div", class_="pt-2 mb-2 d-flex justify-content-between")
    header_info = ""

    if header_div:
        sanskrit = header_div.find("span", class_="title-font font-weight-bold")
        number = header_div.find("span", class_="text-font align-middle text-secondary")
        extra = header_div.find("span", class_="align-middle ml-2 list-item-title-color text-font")
        subtext = header_div.find("div", class_="mt-2 mb-2 align-middle subtext-font grey")

        header_info = "Sanskrit Header: "
        if number: header_info += number.get_text(strip=True) + " "
        if sanskrit: header_info += sanskrit.get_text(strip=True) + " "
        if extra: header_info += extra.get_text(strip=True) + " "
        if subtext: header_info += "| " + subtext.get_text(strip=True)
    else:
        header_info = "❌ No header content found."

    # ---- Table Extraction ----
    table = soup.find("table", class_="table table-layout-fixed bg-light table-bordered")
    table_lines = []
    if table:
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if cols:
                line = "\t".join(col.get_text(strip=True) for col in cols)
                table_lines.append(line)
    else:
        table_lines.append("❌ No table found.")

    # ---- Info Section Extraction ----
    info_section = []

    for label in soup.find_all("span", class_="list-item-title-color"):
        next_sibling = label.find_next_sibling("span", class_="dark")
        if next_sibling:
            info_section.append(f"{label.get_text(strip=True)}: {next_sibling.get_text(strip=True)}")

    for block in soup.find_all("div", class_="text-font"):
        label = block.find("span", class_="list-item-title-color")
        value = block.find("span", class_="dark")
        if label and value:
            info_section.append(f"{label.get_text(strip=True)}: {value.get_text(strip=True)}")

    kosha_blocks = soup.find_all("div", class_="text-font default-english-font list-group-item p-2")
    for block in kosha_blocks:
        if not block.find("span", class_="dark"):
            label = block.get_text(strip=True)
            if label:
                info_section.append(f"Kosha Name: {label}")

    sanskrit_details = soup.find_all("span", class_="default-sanskrit-font dark")
    for span in sanskrit_details:
        long_text = span.get_text(strip=True)
        if long_text and len(long_text) > 20:
            info_section.append(f"Sanskrit Detail: {long_text}")

    # ---- Combine All ----
    combined = f"\u27eaHEADER\u27eb {header_info}\n"
    combined += "\u27eaTABLE\u27eb\n" + "\n".join(table_lines) + "\n\u27ea/TABLE\u27eb\n"
    if info_section:
        combined += "\n\u27eaINFO\u27eb\n" + "\n".join(info_section) + "\n\u27ea/INFO\u27eb"
    combined += "\n" + ("-" * 60) + "\n"
    results.append(combined)

    time.sleep(SLEEP_BETWEEN_REQUESTS)

# Save to text file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"✅ Finished batch {START_INDEX}-{END_INDEX}. Output saved to:\n{OUTPUT_FILE}")
