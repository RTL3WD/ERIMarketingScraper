
import csv


def load_csv_list(filename):
    """
    Load a CSV file and return its contents as a list of dictionaries.

    Parameters:
    filename (str): The name of the CSV file to be read.

    Returns:
    list of dict: A list containing dictionaries for each row in the CSV file.
    """
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                data.append(row)

        return data
    except FileNotFoundError:
        print(f"The file {filename} was not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
