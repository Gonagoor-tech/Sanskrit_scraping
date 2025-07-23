import os
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------- SETTINGS ----------
FAILED_JSON = os.path.expanduser("~/Desktop/shabda_failed.json")
OUTPUT_TXT = os.path.expanduser("~/Desktop/shabda_retry_output.txt")
FAILED_OUT_JSON = os.path.expanduser("~/Desktop/shabda_failed.json")
WAIT_TIMEOUT = 100
SLEEP_BETWEEN = 1.5
# ----------------------------

# Load failed links
with open(FAILED_JSON, "r", encoding="utf-8") as f:
    failed_links = json.load(f)

results = []
still_failed = []

print(f"🔁 Retrying {len(failed_links)} failed shabda links...\n")

# Setup Chrome driver
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, WAIT_TIMEOUT)

for idx, link in enumerate(failed_links):
    try:
        print(f"[{idx}] Retrying: {link}")
        driver.get(link)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-bordered")))
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        header_div = soup.find("div", class_="pt-2 mb-2 d-flex justify-content-between")
        header_info = "Sanskrit Header: "
        if header_div:
            parts = [
                header_div.find("span", class_="text-font align-middle text-secondary"),
                header_div.find("span", class_="title-font font-weight-bold"),
                header_div.find("span", class_="align-middle ml-2 list-item-title-color text-font"),
                header_div.find("div", class_="mt-2 mb-2 align-middle subtext-font grey")
            ]
            header_info += " ".join(p.get_text(strip=True) for p in parts if p)
        else:
            header_info += "❌ No header content found."

        # Table
        table_lines = []
        table = soup.find("table", class_="table table-layout-fixed bg-light table-bordered")
        if table:
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                line = "\t".join(col.get_text(strip=True) for col in cols)
                if line:
                    table_lines.append(line)
        else:
            table_lines.append("❌ No table found.")

        # Info Section
        info_section = []
        for label in soup.find_all("span", class_="list-item-title-color"):
            sibling = label.find_next_sibling("span", class_="dark")
            if sibling:
                info_section.append(f"{label.get_text(strip=True)}: {sibling.get_text(strip=True)}")

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

        full = f"[{idx}] {link}\n{header_info}\n<<TABLE>>\n" + "\n".join(table_lines) + "\n</TABLE>"
        if info_section:
            full += "\n<<INFO>>\n" + "\n".join(info_section) + "\n</INFO>"
        full += "\n" + ("-" * 60)

        results.append(full)
        time.sleep(SLEEP_BETWEEN)

    except Exception as e:
        print(f"❌ Failed again: {link}")
        still_failed.append(link)

driver.quit()

# Save output
with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n\n".join(results))
print(f"\n✅ Output saved to: {OUTPUT_TXT}")

# Save failed
if still_failed:
    with open(FAILED_OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(still_failed, f, indent=2, ensure_ascii=False)
    print(f"⚠️ Still failed links saved to: {FAILED_OUT_JSON}")
else:
    print("🎉 All links retried successfully!")
