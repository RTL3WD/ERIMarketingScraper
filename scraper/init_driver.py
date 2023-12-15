import os
from selenium import webdriver

def init_driver():

    # Start with the current working directory
    current_dir = os.getcwd()

    # Navigate to the download directory
    download_directory = os.path.join(current_dir, 'tmp', 'pdf')
    print(f'Download directory is: {download_directory}')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--kiosk-printing')
    chrome_options.add_argument("enable-automation")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--dns-prefetch-disable")

    # Set the default download directory
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_directory,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })

    return webdriver.Chrome(options=chrome_options)
