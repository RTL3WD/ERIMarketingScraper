import datetime
import os
# Local application/library-specific imports
from my_airtable.send_to_airtable import send_to_airtable
from file_manager.file_cleanup import clean_directory
from file_manager.download_individual_search_results import download_search_result
from file_manager.load_csv_as_list import load_csv_list
from scraper.scraper import scraper
from my_chatgpt.my_openai import send_to_chatgpt
from my_chatgpt.chatgpt_cleanup import cleanup


# Main program execution
if __name__ == "__main__":

    # Get the current day of the week (0 is Monday, 6 is Sunday)
    current_day = datetime.datetime.today().weekday()
    # Check if it's Monday (0) through Friday (4)
    if 0 <= current_day <= 4:
        # Place the code you want to execute here
        print("Executing the code")

        # Set directory paths
        base_directory = os.path.dirname(os.path.abspath(__file__))
        tmp_directory = os.path.join(base_directory, "tmp")
        csv_directory = os.path.join(tmp_directory, "csv")
        pdf_directory = os.path.join(tmp_directory, "pdf")

        # Run the scraper
        scraper()

        # # Get the path to the CSV file
        scrape_results = os.path.join(csv_directory, "scrape-results.csv")

        # download_search_result(scrape_results)
        send_to_chatgpt(base_directory)

        chatgpt_results = os.path.join(csv_directory, "chatgpt-results.csv")

        chatgpt_leads = load_csv_list(chatgpt_results)
        scrape_leads = load_csv_list(scrape_results)

        # Iterate through rows of scrape_leads and extract links based on Case Number
        for row_scrape in scrape_leads:
            # Assuming this column contains the Case Number
            case_number_scrape = row_scrape.get('Case #/Received Date')
            # Assuming this column contains the Link
            link = row_scrape.get('Link')

            # Iterate through rows of chatgpt_leads and find matching Case Number
            for row_chatgpt in chatgpt_leads:
                # Assuming this column contains the Case Number
                case_number_chatgpt = row_chatgpt.get('Case Number')

                # Check if case_number_chatgpt matches case_number_scrape
                if case_number_chatgpt in case_number_scrape:
                    # Store the link in the extracted_links dictionary
                    # extracted_links[case_number_chatgpt] = link
                    row_chatgpt['Link'] = link
                    break  # Exit the inner loop once a match is found

        for lead in chatgpt_leads:
            print(f"Lead Data: {lead}")
            string_balance = lead['Balance']
            if string_balance == 'unavailable':
                string_balance = '0.00'
            float_balance_tmp = float(string_balance)
            balance = round(float_balance_tmp, 2)
            lead['Balance'] = balance
            if balance >= 20000.00:
                send_to_airtable(lead)
            else:
                print('Balance too low. Not sending to Airtable.')
                print(f"Balance: {balance}")
        clean_directory(csv_directory)
        clean_directory(pdf_directory)
        cleanup()
    else:
        print("No work today. It's the weekend.")
