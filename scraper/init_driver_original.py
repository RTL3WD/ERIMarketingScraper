from undetected_chromedriver import Chrome, options
# from webdriver_manager.chrome import ChromeDriverManager


def init_driver():
    # Configure undetected-chromedriver options
    undetected_options = options.ChromeOptions()
    undetected_options.add_argument('--headless')  # Run Chrome in headless mode
    undetected_options.add_argument('--disable-gpu')
    undetected_options.add_argument('--disable-software-rasterizer')
    undetected_options.add_argument('--no-sandbox')
    undetected_options.add_argument('--disable-dev-shm-usage')
    undetected_options.add_argument('--disable-extensions')
    undetected_options.add_argument(
        '--kiosk-printing')
    undetected_options.add_argument("enable-automation")
    undetected_options.add_argument("--window-size=1920,1080")
    undetected_options.add_argument("--no-sandbox")
    undetected_options.add_argument("--dns-prefetch-disable")

    # Set the default download directory
    undetected_options.add_experimental_option("prefs", {
        # Replace with your download directory
        "download.default_directory": r".\\tmp\\pdf",
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })

    # Initialize the Chrome driver with webdriver_manager and undetected-chromedriver
    # driver_manager = ChromeDriverManager().install()
    driver = Chrome(options=undetected_options, enable_console_log=True, driver_executable_path="./chromedriver")
    return driver
