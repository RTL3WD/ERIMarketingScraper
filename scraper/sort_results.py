# Import necessary libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from .random_delay import random_delay
from .recaptcha_solve import solve_recaptcha


def sort_results(driver, anticaptcha_key):
    """
    Sorts the search results on a web page by 'Case Type' and initiates a search.

    :param driver: The Selenium WebDriver object.
    :param anticaptcha_key: Your AntiCaptcha API key.
    """
    try:
        # Sort by case type
        sort_by_dropdown = Select(driver.find_element(By.ID, 'selSortBy'))
        sort_by_dropdown.select_by_visible_text('Case Type')
        random_delay(2, 5)  # Introduce a random delay for realism

        # Click the search button
        search_button = driver.find_element(
            By.CSS_SELECTOR, "#form > table.NewSearchResults > caption > span > input[type=submit]")
        search_button.click()
    except:
        try:
            if driver.find_element(By.ID, 'footer'):
                print('No results found for this court.')
        except:
            print('Trying to solve Recaptcha from sort results')
            solve_recaptcha(driver, anticaptcha_key)
