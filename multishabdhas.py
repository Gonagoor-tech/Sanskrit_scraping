from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import json

# ----------- SETTINGS -------------
START_INDEX = 0
END_INDEX = 50
LINK_FILE = os.path.expanduser("~/Desktop/all_shabda_links.json")
OUTPUT_FILE = os.path.expanduser(f"~/Desktop/shabda_output_{START_INDEX}_{END_INDEX}.txt")
WAIT_TIME = 40
SLEEP_BETWEEN_REQUESTS = 1.5
MAX_THREADS = 10  # Adjust as per machine capacity
# ----------------------------------

# Load full link list
with open(LINK_FILE, "r", encoding="utf-8") as f:
    all_links = json.load(f)

subset_links = all_links[START_INDEX:END_INDEX]
print(f"🔍 Scraping links {START_INDEX} to {END_INDEX} using {MAX_THREADS} threads (Total: {len(subset_links)})")

def scrape_one(index, link):
    result = f"[{index}] {link}\n"
    try:
        # Setup headless Chrome per thread
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, WAIT_TIME)

        driver.get(link)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-bordered")))
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Header
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
        table = soup.find("table", class_="table table-layout-fixed bg-light table-bordered")
        table_lines = []
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


                full = f"{header_info}\n"
                full += "<<TABLE>>\n" + "\n".join(table_lines) + "\n</TABLE>"
                if info_section:
                    full += "\n<<INFO>>\n" + "\n".join(info_section) + "\n</INFO>"
                    full += "\n" + ("-" * 60)


        driver.quit()
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        return index, full

    except Exception as e:
        return index, f"[{index}] {link}\n⚠️ Error: {e}\n{'-'*60}"

# --- Multithreading block with ordered output ---
results_dict = {}
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = {
        executor.submit(scrape_one, idx, link): idx for idx, link in enumerate(subset_links, START_INDEX)
    }
    for future in as_completed(futures):
        idx, content = future.result()
        results_dict[idx] = content

# Sort and write output
ordered_results = [results_dict[i] for i in sorted(results_dict)]
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n\n".join(ordered_results))

print(f"\n✅ Done. Output saved to: {OUTPUT_FILE}")
