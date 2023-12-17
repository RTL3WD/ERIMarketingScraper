import os
# Local application/library-specific imports
from my_airtable.send_to_airtable import send_to_airtable
from file_manager.download_individual_search_results import download_search_result
from file_manager.load_csv_as_list import load_csv_list
from scraper.scraper import scraper
from my_chatgpt.my_openai import send_to_chatgpt


# Main program execution
if __name__ == "__main__":

    # Get the base directory of the project
    base_directory = os.path.dirname(os.path.abspath(__file__))

    # Run the scraper
    # scraper()

    # # Get the path to the CSV file
    file_path = os.path.join(base_directory, "tmp",
                             "csv", "scrape-results.csv")

    # download_search_result(file_path)
    send_to_chatgpt(base_directory)

    filename = os.path.join(base_directory, "tmp",
                            "csv", "chatgpt-results.csv")
    leads = load_csv_list(filename)

    for lead in leads:
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
