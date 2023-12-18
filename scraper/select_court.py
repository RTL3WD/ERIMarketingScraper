# Import necessary libraries
from datetime import date
from .exit_scraper import exit_scraper
from .random_delay import random_delay
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def select_court(driver, court_index, df=None):
    """
    Selects a court on a web page, enters today's date, and submits a form.

    :param driver: The Selenium WebDriver object.
    :param anticaptcha_key: Your AntiCaptcha API key.
    :param court_index: Index of the court to be selected.
    :return: The updated court index.
    """

    # Get today's date
    today = date.today()

    # Open the website
    url = "https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange"
    driver.get(url)

    # Introduce a random delay to mimic human behavior
    random_delay(5, 7)

    # Locate and interact with the court selection dropdown
    court_dropdown = driver.find_element(By.ID, 'selCountyCourt')
    court_options = court_dropdown.find_elements(By.TAG_NAME, 'option')
    try:
        pick_court = court_options[court_index]
        current_court = pick_court.text
        pick_court.click()
    except:
        exit_scraper(driver, df)

    # Introduce another random delay
    random_delay(5, 7)

    # Fill in the date input field with today's date
    filing_date_input = driver.find_element(By.ID, 'txtFilingDate')
    # filing_date_input.clear()
    random_delay(2, 4)
    filing_date_input.send_keys(today.strftime("%m/%d/%Y"))
    # filing_date_input.send_keys(today.strftime(
    #    "12/15/2023"))  # TESTING PURPOSES ONLY

    # Print information about the selected court and index
    print(f'Currently Searching: {current_court}...')
    print(f'At Index Number: {court_index}...')
    random_delay(3, 5)

    # Submit the form by sending an Enter key press to the date input field
    filing_date_input.send_keys(Keys.ENTER)

    random_delay(3, 5)
    try:
        error_msg = driver.find_element(By.CLASS_NAME, 'MsgBox_Error')
        if error_msg:
            filing_date_input = driver.find_element(By.ID, 'txtFilingDate')
            # filing_date_input.clear()
            random_delay(2, 3)
            filing_date_input.send_keys(today.strftime("%m/%d/%Y"))
            # filing_date_input.send_keys(today.strftime(
            #   "12/15/2023"))  # TESTING PURPOSES ONLY
    except:
        pass

    # Increment the court index for the next iteration
    return court_index + 1, df


# Select court loop with try/except block
def select_court_try_except(driver, court_index, df):
    try:
        return select_court(driver, court_index, df)
    except:
        return select_court(driver, court_index, df)
