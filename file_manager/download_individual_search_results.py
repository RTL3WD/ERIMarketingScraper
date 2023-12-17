import csv
import time
from selenium.webdriver.common.by import By
from scraper.scraper import init_driver


def download_search_result(csv_file):
    driver = init_driver()

    # Read URLs from CSV file
    with open(csv_file, newline='') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip the header row

        for row in reader:
            # Check if cell B (index 1) contains "Not Assigned"
            if "Not Assigned" in row[1]:
                continue  # Skip this row

            url = row[0]  # Assuming the URL is in the first cell of each row
            driver.get(url)
            print(url)

            time.sleep(5)

            # Specify the keywords you're looking for (case-insensitive)
            keywords = ['SUMMONS', 'EXHIBIT']  # Replace with your keywords

            # Construct XPath expression to find links containing any of the keywords
            xpath_expression = " | ".join(
                [f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]" for keyword in keywords])

            # Find elements using the constructed XPath
            links = driver.find_elements(By.XPATH, xpath_expression)

            # Extract and print the URLs
            for link in links:
                link_url = link.get_attribute('href')
                print(link_url)
                driver.get(link_url)
                time.sleep(5)

                # Execute print command to save page as PDF
                print_settings = {
                    'recentDestinations': [{
                        'id': 'Save as PDF',
                        'origin': 'local',
                        'account': '',
                    }],
                    'selectedDestinationId': 'Save as PDF',
                    'version': 2,
                    'isHeaderFooterEnabled': False  # Disable header and footer
                }
                driver.execute_cdp_cmd('Page.printToPDF', print_settings)
                print(f'Downloaded pdf for {link_url}.')
