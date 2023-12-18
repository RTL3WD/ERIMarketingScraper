import os
import json
import requests

from datetime import datetime
from dotenv import load_dotenv


def send_to_airtable(json_data):

    load_dotenv()
    airtable_api = os.getenv('AIRTABLE_API')

    date = datetime.utcnow()

    # Format the date as an ISO 8601 string (YYYY-MM-DD)
    date = date.strftime('%Y-%m-%d')

    url = "https://api.airtable.com/v0/appho2OWyOBvn6PPU/tblGGlwnda0skq18F"

    payload = json.dumps({
        "records": [
            {
                "fields": {
                    # "Name": json_data,
                    "DATE": date,
                    "Page Link": json_data['Link'],
                    # "Status": json_data,
                    "phone": json_data['Phone Number'],
                    "email": json_data['Email'],
                    "COMPANY SUED": json_data['Companies Sued'],
                    "BALANCE": json_data['Balance'],
                    "First Name": json_data['First Name'],
                    "Last Name": json_data['Last Name'],
                    "CREDITOR NAME": json_data['Creditor'],
                    "COUNTY": json_data['County'],
                    "BUSINESS ADDRESS": json_data['Address'],
                    "NOTES": json_data['Notes'],
                }
            }
        ]
    })
    headers = {
        'Authorization': f'Bearer {airtable_api}',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.json())
