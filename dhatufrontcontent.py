from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os
import time

# Setup headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# Step 1: Load dhatu page
driver.get("https://ashtadhyayi.com/dhatu")
time.sleep(2)

# Step 2: Scroll to load all entries
print("🔄 Scrolling to load all dhātu entries...")
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height
print("✅ All entries loaded. Extracting...")

# Step 3: Parse page content
soup = BeautifulSoup(driver.page_source, "html.parser")
blocks = soup.select('div.href.d-inline')
results = []

for block in blocks:
    try:
        # Extract full badge (e.g., "०१.०९३३ घटादयो मितः भ्वादिः")
        badge_el = block.find_previous("div", class_="badge")
        badge_text = " ".join(badge_el.stripped_strings) if badge_el else ""

        # Extract root word
        root_el = block.find("div", class_="list-item-title font-weight-bold")
        root = root_el.get_text(strip=True) if root_el else ""

        # Extract all forms (even after blank siblings)
        forms = [
            div.get_text(strip=True)
            for div in block.find_all("div", class_="d-inline dark")
            if div.get_text(strip=True)
        ]
        forms_str = "; ".join(forms) if forms else ""

        # Extract English gloss
        eng_el = block.find("div", class_="default-english-font")
        english = eng_el.get_text(strip=True) if eng_el else ""

        # Extract optional gloss (e.g. Hindi)
        gloss = ""
        if eng_el:
            gloss_div = eng_el.find_next_sibling("div")
            if gloss_div:
                gloss = gloss_div.get_text(strip=True)

        # Final line
        result_line = f"{badge_text} | {root} | {forms_str} | {english} | {gloss}\n" + "-" * 80
        results.append(result_line)

    except Exception as e:
        print(f"⚠️ Skipped a block due to error: {e}")

driver.quit()

# Step 4: Save output
output_path = os.path.expanduser("~/Desktop/dhatu_page_all_visible_content.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"\n✅ Done! Extracted {len(results)} entries.")
print(f"📄 Output saved to: {output_path}")
