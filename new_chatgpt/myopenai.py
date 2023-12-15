from dotenv import load_dotenv
import os
from openai import OpenAI
import openai
import time


# Workflow:
# 1. Upload files to OpenAI
# 2. Create an assistant with access to the previously uploaded files
# 3. Create a thread with the assistant
# 4. Send a message to the thread
# 5. Run the thread
# 6. Process the response
# 7. Repeat steps 4-6 until the thread is complete
# 8. Delete the assistant
# 9. Delete the files


def create_assistant(client, file_ids):
    client = OpenAI(
        api_key=os.getenv('OPENAI_API'),
    )

    my_assistant = client.beta.assistants.create(
        instructions="""
           You have uploaded files as input data to the assistant.

            Use the following step-by-step instructions to respond to user inputs:

            Step 1: Read all accessible files
            Step 2: Extract Plaintiff(s) data
                Step 2.1: Extract Plaintiff’(s) Balance Owed data (data type: float or "unavailable" if not present)
            Step 3: Extract Defendant(s) data
                Step 3.1: From the Defendant(s), extract the first full name that is not a business; this data will be used to save first and last names (data type: string or "unavailable" if not present)
                Step 3.2: Extract Defendant’(s) Phone Numbers data (data type: string, combine multiple numbers into a CSV list or "unavailable" if not present)
                Step 3.3: Extract Defendant’(s) Email Addresses data (data type: string, combine multiple emails into a CSV list or "unavailable" if not present)
                Step 3.4: Extract Defendant’(s) Address’(s) data as a single string with the entire address in it (data type: string or "unavailable" if not present)
                Step 3.5: Create a CSV list of the companies sued (data type: string or "unavailable" if not present)
            Step 4: Extract Court County data (data type: string or "unavailable" if not present)
            Step 5: Convert Balance value to a float number with two decimals
            Step 6: Please ensure that you follow these instructions precisely to generate the JSON object as described above. If any data is unavailable in the input, save it as "unavailable" as specified. Convert the data to a JSON object with the following key-value pairs. :

            {
                “Creditor”: Plaintiff(s) data (data type: string or "unavailable" if not present),
                “Balance”: Plaintiff’(s) Balance Owed data (data type: float or "unavailable" if not present),
                “Companies Sued”: CSV list of companies sued (data type: string or "unavailable" if not present),
                “First Name”: First Name Data Extracted data (data type: string or "unavailable" if not present),
                “Last Name”: Last Name Data Extracted data (data type: string or "unavailable" if not present),
                “Phone Number”: Defendant’(s) Phone Numbers data (data type: string, combine multiple numbers into a CSV list or "unavailable" if not present),
                “Email”: Defendant’(s) Email Addresses data (data type: string, combine multiple emails into a CSV list or "unavailable" if not present),
                “Address”: Defendant’(s) Address’(s) data (data type: string or "unavailable" if not present),
                “County”: Court County data (data type: string or "unavailable" if not present),
                "Notes": Any additional notes about the file (data type: string or "unavailable" if not present)
            }

""",
        name="MyAssistant",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=file_ids
    )

    assistant_id = my_assistant.id

    print(f"Assistant ID: {assistant_id}")

    return assistant_id


def create_message(client, thread_id, file_ids):
    # /v1/threads/thread_0spnmrJpArrNGRUmzt2IisHo/messages

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content="Please analyze the provided files and directly return the resulting JSON object. Refrain from giving any explanations, summaries, or additional comments.",
        file_ids=file_ids
    )


def run_thread(client, thread_id, assistant_id):

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    return run.id


def create_thread(client):

    client = OpenAI(
        api_key=os.getenv('OPENAI_API'),
    )

    thread = client.beta.threads.create()

    return thread.id


def get_messages(client, thread_id):

    thread_messages = client.beta.threads.messages.list(thread_id=thread_id)
    x = thread_messages['data'][0]['content']['text']
    print(f'Getting messages: {x}')
    return thread_messages.data.content.text


def get_status(client, thread_id, run_id):

    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )

    print(run.status)

    return run.status


def get_steps(client, thread_id, run_id):
    run_steps = client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run_id
    )
    print(run_steps)
    return run_steps


def list_of_file_paths():
    # Dynamically get the PDF directory path in the ./tmp/pdf directory
    pdf_dir = os.path.join(os.getcwd(), "tmp", "pdf")

    # Get a list of all files in the PDF directory
    files = os.listdir(pdf_dir)

    # Create a dictionary to group files by their PDF file name
    pdf_files_dict = {}

    # Group files by their PDF file name
    for file_name in files:
        pdf_name = file_name.split('_')[0]
        file_path = os.path.join(pdf_dir, file_name)  # Get the full file path
        if pdf_name in pdf_files_dict:
            pdf_files_dict[pdf_name].append(file_path)
        else:
            pdf_files_dict[pdf_name] = [file_path]

    # Create a list to store groups of files with the same PDF file name
    same_pdf_files = [
        files for files in pdf_files_dict.values() if len(files) > 1]

    # Return the list of groups of files with the same PDF file name
    return same_pdf_files


def upload_file(client, file_path):

    file_upload_response = client.files.create(
        file=open(file_path, "rb"),
        purpose="assistants"
    )
    print(
        f"File Name: {file_upload_response.filename} & File ID: {file_upload_response.id}")

    return file_upload_response.id


def process_files(directory):
    for file_name in os.listdir(directory):
        # Check if the file is a PDF
        if file_name.endswith(".pdf"):
            file_path = os.path.join(directory, file_name)
            print(f'File to be uploaded: {file_name}')
            print(f'File path: {file_path}')


def list_of_file_paths():
    # Dynamically get the PDF directory path in the ./tmp/pdf directory
    pdf_dir = os.path.join(os.getcwd(), "tmp", "pdf")

    # Get a list of all files in the PDF directory
    files = os.listdir(pdf_dir)

    # Create a dictionary to group files by their PDF file name
    pdf_files_dict = {}

    # Group files by their PDF file name
    for file_name in files:
        pdf_name = file_name.split('_')[0]
        file_path = os.path.join(pdf_dir, file_name)  # Get the full file path
        if pdf_name in pdf_files_dict:
            pdf_files_dict[pdf_name].append(file_path)
        else:
            pdf_files_dict[pdf_name] = [file_path]

    # Create a list to store groups of files with the same PDF file name
    same_pdf_files = [
        files for files in pdf_files_dict.values() if len(files) > 1]

    # Return the list of groups of files with the same PDF file name
    return same_pdf_files


def main():
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv('OPENAI_API'),
    )

    # Get a list of all files in the PDF directory
    case_files = list_of_file_paths()

    for case_file in case_files:
        file_ids = []
        for file in case_file:
            file_id = upload_file(client, file)
            file_ids.append(file_id)

        assistant_id = create_assistant(client, file_ids)
        thread_id = create_thread(client)
        create_message(client, thread_id, file_ids)
        time.sleep(1)
        run_id = run_thread(client, thread_id, assistant_id)
        time.sleep(2)
        while True:
            status = get_status(client, thread_id, run_id)

            if status == 'failed':
                assistant_id = create_assistant(client, file_ids)
                thread_id = create_thread(client)
                create_message(client, thread_id, file_ids)
                time.sleep(1)
                run_id = run_thread(client, thread_id, assistant_id)
                time.sleep(2)
            elif status == 'in_progress':
                print(f'Current Status: {status}')
                time.sleep(20)
                continue
            elif status == 'completed':
                break
            else:
                time.sleep(5)

        message = get_messages(client, thread_id)
        print(message)


if __name__ == "__main__":
    main()
