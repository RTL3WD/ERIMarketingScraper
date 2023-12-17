# Import necessary libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .extract_court_results import extract_table_data
from .select_court import select_court_try_except as select_court
from selenium.common.exceptions import StaleElementReferenceException

# Define a function to find and click the next page link


def find_and_click_next_page(driver, anticaptcha_key, existing_df, next_court):
    """
    Finds and clicks the 'Next Page' link on a web page, extracts and processes data from the next page.

    :param driver: The Selenium WebDriver object.
    :param anticaptcha_key: Your AntiCaptcha API key.
    :param existing_df: DataFrame containing existing data.
    :param next_court: Index of the next court to select.
    :return: Updated DataFrame with extracted data.
    """
    while True:
        try:
            # Re-find the link to the next page (if any) in each iteration
            next_page_links = driver.find_elements(
                By.CSS_SELECTOR, ".pageNumbers a")
            next_page_link = None

            # Look for the link with '>>' text (indicating the next page)
            for link in next_page_links:
                if '>>' in link.text:
                    next_page_link = link
                    break

            if next_page_link:
                # Use explicit wait to ensure the link is clickable
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(next_page_link)
                )
                next_page_link.click()

                # Call the extract_table_data function to process the new page's data
                existing_df = extract_table_data(
                    driver.page_source, existing_df)

                # Uncomment the following line if you want to stop after processing one page
                # break

            else:
                # If there is no next page link with '>>', select the next court and exit the loop
                select_court(driver, anticaptcha_key, next_court, existing_df)
                break

        except StaleElementReferenceException:
            # If StaleElementReferenceException is caught, continue the loop
            # This will cause the elements to be re-found
            existing_df.to_csv('results.csv', index=False)
            continue

    return existing_df
