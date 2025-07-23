from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
import time
import re
import tempfile
import shutil

# ----------- SETTINGS -------------
START_INDEX = 0
END_INDEX = 2260
INPUT_JSON = os.path.expanduser("~/Desktop/all_dhatu_links.json")
OUTPUT_DIR = os.path.expanduser("~/Desktop/dhatu_scraped_chunks")
WAIT_TIMEOUT = 100
SLEEP_BETWEEN_REQUESTS = 2.0
MAX_THREADS = 5
HEADLESS = True
CHECKPOINT_INTERVAL = 250
# ----------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)
devanagari_re = re.compile(r'[\u0900-\u097F]')

# Load all links
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    all_links = json.load(f)
subset_links = all_links[START_INDEX:END_INDEX]

print(f"🔍 Scraping dhatus {START_INDEX} to {END_INDEX} using {MAX_THREADS} threads")

def scrape_one(idx, url):
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    user_data_dir = tempfile.mkdtemp(prefix=f"chrome_thread_{idx}_")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        print(f"[{idx}] Scraping: {url}")

        driver.get(url)

        if not driver.page_source.strip():
            raise Exception("❌ Empty page source. Likely failed to load.")

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card tbody tr")))
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        heading_block = soup.select_one("#dhatu-title-extra-info")
        heading = ' '.join(heading_block.get_text(separator=' ').split()) if heading_block else "N/A"

        table_lines = []
        for card in soup.select(".card"):
            header_div = card.select_one(".card-header")
            if header_div:
                header_text = header_div.get_text(strip=True)
                junk = ["loading", "offline", "please", "chrome", "update", "reset", "enable"]
                if not devanagari_re.search(header_text) or any(j in header_text.lower() for j in junk):
                    continue
                table_lines.append(header_text)

            for row in card.select("tbody tr"):
                row_data = []
                for td in row.select("td"):
                    spans = [span.get_text(strip=True) for span in td.select("span")]
                    combined = " | ".join(spans) if spans else ""
                    row_data.append(combined)
                if row_data:
                    table_lines.append("    " + " | ".join(row_data))

            table_lines.append("")

        block = f"""
[{idx + 1}]
==============================
Heading: {heading}
Table:
{chr(10).join(table_lines)}
==============================
""".strip()

        driver.quit()
        shutil.rmtree(user_data_dir)
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        return (idx, block, None)

    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        shutil.rmtree(user_data_dir)
        return (idx, None, url)

# ---- Auto-resuming with Checkpoints ----
for batch_start in range(0, len(subset_links), CHECKPOINT_INTERVAL):
    batch_end = min(batch_start + CHECKPOINT_INTERVAL, len(subset_links))
    output_path = os.path.join(OUTPUT_DIR, f"dhatus_{START_INDEX + batch_start}_{START_INDEX + batch_end}.txt")

    if os.path.exists(output_path):
        print(f"✅ Skipping already completed batch: {START_INDEX + batch_start} to {START_INDEX + batch_end}")
        continue

    print(f"\n🚧 Processing batch: {START_INDEX + batch_start} to {START_INDEX + batch_end - 1}")

    batch_links = subset_links[batch_start:batch_end]
    results = []
    batch_failed = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {
            executor.submit(scrape_one, START_INDEX + idx, link): (START_INDEX + idx, link)
            for idx, link in enumerate(batch_links, start=batch_start)
        }

        for future in as_completed(futures):
            idx, link = futures[future]
            try:
                result_idx, content, failed = future.result()
                if content:
                    results.append((result_idx, content))
                if failed:
                    batch_failed.append(failed)
            except Exception as exc:
                batch_failed.append(link)

    # Save checkpoint output
    results.sort(key=lambda x: x[0])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(block for _, block in results))
    print(f"✅ Checkpoint saved: {output_path}")

    if batch_failed:
        failed_file = os.path.join(
            OUTPUT_DIR, f"dhatus_failed_{START_INDEX + batch_start}_{START_INDEX + batch_end}.json"
        )
        with open(failed_file, "w", encoding="utf-8") as f:
            json.dump(batch_failed, f, indent=2, ensure_ascii=False)
        print(f"⚠️ Failed links saved: {failed_file}")

print(f"\n🎉 ALL DONE. Output stored in folder: {OUTPUT_DIR}")
