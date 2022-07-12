import os
import requests
import selenium.common.exceptions
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:os.mkdir(".temp")
except FileExistsError:pass

## selenium config
furryfox_options = webdriver.FirefoxOptions()
furryfox_options.add_argument("--headless")
driver = webdriver.Firefox(
    service=Service("./src/geckodriver"),
    options=furryfox_options,
)
wait = WebDriverWait(driver, 10)  # max wait duration, in seconds

## requests config
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"
}
__soup__ = lambda url: BeautifulSoup(requests.get(url, headers=headers).text, "lxml")


# base_url = "https://www.mangago.me/read-manga/nan_hao_shang_feng/"
# chapter_range = (5, 6)
# base = sys.argv[1]
# try: chapter_range = (int(sys.argv[2]), int(sys.argv[3]))
# except IndexError: chapter_range = 0

soup = BeautifulSoup(
    requests.get(
        "https://www.mangago.me/r/l_search",
        params={"name": input("Enter manga: ")},
        headers=headers,
    ).text,
    "lxml",
)
results = soup.find("ul", id="search_list").findAll("a", class_="thm-effect")
for index, result in enumerate(results):
    print(f'[{index + 1}] {result["title"]}')
base = results[int(input("\nEnter choice: ")) - 1]["href"]

PAGE_COUNT = 0
progress = ""

soup = __soup__(base)
base_url = soup.find("a", class_="content-h1-btn yellow normal")["href"]
soup = __soup__(base_url)

chapters = soup.find("ul", class_="dropdown-menu chapter").findAll("a")
print("\nChapters:")
for chapter_no, chapter in enumerate(chapters):
    # print("https://www.mangago.me" + chapter["href"], "->", chapter_no)
    print(f"[{chapter_no+1}] {chapter.text}")
chapter_range = [int(_) for _ in input("\nEnter chapter range separated by space: ").strip().split()]

for chapter_no, chapter in enumerate(chapters):

    if chapter_range:
        if chapter_no < chapter_range[0]-1:
            continue
        elif chapter_no > chapter_range[1]-1:
            break

    chapter_url = "https://www.mangago.me" + chapter["href"]
    # print(chapter_url)

    ## Chapter cover image
    width, height = 700, 1300
    # message = chapter_url.replace('/', '-')[len(base)+3:]
    message = chapter.text
    font = ImageFont.truetype("./src/Noir_medium.otf", size=40)
    with Image.new(mode="RGB", size=(width, height), color=(0, 0, 0)) as img:
        canvas = ImageDraw.Draw(img)
        textWidth, textHeight = canvas.textsize(message, font=font)
        xText = (width - textWidth) / 2
        yText = (height - textHeight) / 2
        canvas.text((xText, yText), message, font=font, fill=(255, 255, 255))
        # img.save(f"./.temp/{message}.png")
        img.save(f"./.temp/{PAGE_COUNT}.png");PAGE_COUNT+=1
        # break

    

    _ = __soup__(chapter_url)
    no_of_pages = int(_.find("div", class_="multi_pg_tip left").text[:-1].split("/")[1])
    # print(no_of_pages)

    for page in range(1, no_of_pages + 1):
        print("\b"*len(progress), end="", flush=True)
        page_url = "/".join(chapter_url.split("/")[:-2]) + f"/pg-{page}/"
        if not requests.get(page_url, headers=headers).ok:
            # page_url = "/".join(chapter_url.split("/")[:-2]) + f"/{page}/"
            page_url = chapter_url + str(page)
        
        # filename = chapter_url.replace('/', '-')[len(base)+3:] + f'{page}'
        # print(page_url, filename)

        driver.get(page_url)
        driver.maximize_window()
        try:
            x = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, f"img.page{page}"))
            )  # gets the image
            with open(f"./.temp/{PAGE_COUNT}.png", mode="wb") as f:
                f.write(requests.get(x.get_attribute("src")).content)
        except selenium.common.exceptions.TimeoutException:
            x = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, f"span.page{page}"))
            )
            with open(f"./.temp/{PAGE_COUNT}.png", mode="wb") as f:
                f.write(x.screenshot_as_png)
        # print(f"Saved File ./.temp/{filename}.png")
        PAGE_COUNT+=1
        progress = f"Downloaded page {page} of {no_of_pages} of chapter '{chapter.text}' | Progress: {round((page)*100/no_of_pages, 2)}%   "
        print(progress, end="", flush=True)
        

driver.quit()

## Final PDF conversion
# import os
# from PIL import Image
# base="dsfs/dfsd/fsdfs/dfs/dfs"
print("\n\nDownload complete. Converting files to PDF...")
images = [Image.open(f"./.temp/{f}.png").convert("RGB") for f in range(len(os.listdir("./.temp/")))]
pdf_path = f"./{base.split('/')[-2]}.pdf"
images[0].save(
    pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:]
);print("Done!")

## cleanup
if input("\nClean ./.temp? [y/n] ").strip().lower() == "y":
    for _ in os.listdir('./.temp/'):
        os.remove(f'./.temp/{_}')
