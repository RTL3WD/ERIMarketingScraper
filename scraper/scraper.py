# Standard library imports
import os
from datetime import datetime

# Related third-party imports
import pandas as pd
from dotenv import load_dotenv

# Local application/library-specific imports
from .extract_court_results import extract_table_data
from .init_driver import init_driver
from .pagination import find_and_click_next_page
from .random_delay import random_delay
from .select_court import select_court_try_except as select_court
from .sort_results import sort_results
from .exit_scraper import exit_scraper

# Define a function to initialize the Chrome driver


# Scraper
def scraper():
    # Start time of scraper
    original_start = datetime.now()

    # Check for directory and create if it doesn't exist

    csv_directory = os.path.join(os.getcwd(), 'tmp', 'csv')

    # Check if the directory exists
    if not os.path.exists(csv_directory):
        # Create the directory if it doesn't exist
        os.makedirs(csv_directory)
        print(f"Directory '{csv_directory}' was created.")
    else:
        print(f"Directory '{csv_directory}' already exists.")

    # Load environment variables from a .env file
    load_dotenv()
    anticaptcha_key = os.getenv('ANTICAPTCHA_API_KEY')

    # Export Dataframe
    export_df = pd.DataFrame(columns=['Link', 'Case #/Received Date',
                                      'eFiling Status/Case Status', 'Caption', 'Court/Case Type', 'Empty'])

    # Initialize the Chrome driver
    driver = init_driver()

    # Set court index to 1 to start with the first court
    court_index = 1

    # Select a court using a custom function and anticaptcha_key
    court_index, _ = select_court(driver, court_index, None)
    random_delay(3, 5)

    # Check if the results page is displayed and sort results
    sort_results(driver, anticaptcha_key)

    random_delay(5, 7)

    # Create a DataFrame to store the results
    existing_df = pd.DataFrame(columns=['Link', 'Case #/Received Date',
                                        'eFiling Status/Case Status', 'Caption', 'Court/Case Type', 'Empty'])
    html = driver.page_source
    existing_df = extract_table_data(html, existing_df)

    # Loop through courts until a certain condition is met (court_index < 61)
    loop_count = 1
    while court_index < 61:
        if loop_count != 2 and court_index != 61:
            # Get current time for start time
            start_time = datetime.now()
            print(f'Start Time: {start_time}')

            try:
                # Select a court, introduce a random delay, and sort results
                court_index, existing_df = select_court(
                    driver, court_index, existing_df)
            except:
                print('Closing Scraper')
                exit_scraper(driver, existing_df)
                print('Scraper Finished')
            random_delay(5, 7)
            sort_results(driver, anticaptcha_key)
            random_delay(5, 7)
            html = driver.page_source
            existing_df = extract_table_data(html, existing_df)

            # Find and click the "Next Page" button and update the DataFrame
            existing_df = find_and_click_next_page(
                driver, anticaptcha_key, existing_df, court_index)

            # Dropping duplicates based on the 'Link' column, keeping the first occurrence
            df_unique = existing_df.drop_duplicates(
                subset='Link', keep='first')

            export_df = pd.concat([export_df, df_unique], ignore_index=True)
            export_df.drop_duplicates(inplace=True)
            csv_file_path = os.path.join(csv_directory, 'scrape-results.csv')
            export_df.to_csv(csv_file_path, index=False)

            print(export_df)
            # End time and duration
            final_time = datetime.now()
            duration = final_time - start_time
            print(f"End Time: {final_time}")
            print(f"Duration: {duration}")

    # End time and duration
    final_time = datetime.now()
    duration = final_time - original_start
    print(f"Final Run Time: {final_time}")
    print(f"Duration: {duration}")
    driver.quit()
    print('Scraper Finished')
