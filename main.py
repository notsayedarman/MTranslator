import os
import base64
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---- Config ----
URL = str(input("Please Enter Webpage Url:"))
MEDIA_FOLDER = "media"
OUTPUT_FOLDER = "output"
OUTPUT_PREFIX = "stitched"
MAX_MB = 10
MAX_BYTES = MAX_MB * 1024 * 1024

os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---- Selenium setup ----
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)

# Wait until at least one image is visible
WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.TAG_NAME, "img"))
)

seen = set()
saved_files = []

# ---- Scroll & download images ----
while True:
    imgs = driver.find_elements(By.TAG_NAME, "img")
    for img in imgs:
        src = img.get_attribute("src")
        if src in seen:
            continue

        try:
            b64data = driver.execute_script("""
                let c = document.createElement('canvas');
                let ctx = c.getContext('2d');
                c.width = arguments[0].naturalWidth;
                c.height = arguments[0].naturalHeight;
                ctx.drawImage(arguments[0], 0, 0);
                return c.toDataURL('image/png').substring(22);
            """, img)
        except Exception:
            b64data = None

        if b64data:
            raw = base64.b64decode(b64data)
            image = Image.open(BytesIO(raw)).convert("RGB")

            file_path = os.path.join(MEDIA_FOLDER, f"page_{len(saved_files)+1}.png")
            image.save(file_path, "PNG", optimize=True)
            saved_files.append(file_path)
            seen.add(src)

            print(f"Saved image {len(saved_files)}: {file_path} ({image.width}x{image.height})")

    # Scroll down
    driver.execute_script("window.scrollBy(0, window.innerHeight);")
    new_height = driver.execute_script("return window.scrollY + window.innerHeight")
    total_height = driver.execute_script("return document.body.scrollHeight")
    if new_height >= total_height:
        break

driver.quit()

# ---- Stitch images into batches by MAX_MB ----
def save_stitched_by_size(image_files, output_folder, prefix="stitched"):
    batches = []
    current_batch = []
    current_size = 0

    for file_path in image_files:
        size = os.path.getsize(file_path)
        if current_size + size > MAX_BYTES:
            if current_batch:
                batches.append(current_batch)
            current_batch = [file_path]
            current_size = size
        else:
            current_batch.append(file_path)
            current_size += size

    if current_batch:
        batches.append(current_batch)

    print(f"Total batches created: {len(batches)}")

    stitched_files = []
    for idx, batch in enumerate(batches, 1):
        images = [Image.open(f).convert("RGB") for f in batch]
        total_width = max(im.width for im in images)
        total_height = sum(im.height for im in images)

        stitched = Image.new("RGB", (total_width, total_height))
        y_offset = 0
        for im in images:
            stitched.paste(im, (0, y_offset))
            y_offset += im.height

        out_file = os.path.join(output_folder, f"{prefix}_{idx}.png")
        stitched.save(out_file, "PNG", optimize=True)
        size_mb = os.path.getsize(out_file) / 1024 / 1024
        stitched_files.append(out_file)
        print(f"Saved {out_file} ({size_mb:.2f} MB)")

    return stitched_files

if saved_files:
    final_stitched = save_stitched_by_size(saved_files, OUTPUT_FOLDER, OUTPUT_PREFIX)
    print(f"\nFinished. Total {len(final_stitched)} stitched images in '{OUTPUT_FOLDER}'.")
else:
    print("No images extracted")
