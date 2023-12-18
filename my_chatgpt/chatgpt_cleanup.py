import os
from dotenv import load_dotenv

from openai import OpenAI


def cleanup():
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv('OPENAI_API'),
    )

    my_files = client.files.list()

    for file in my_files.data:
        del_file_response = client.files.delete(file.id)
        print(del_file_response)

    my_assistants = client.beta.assistants.list(
        order='desc',
        limit=100
    )

    assistants_list = my_assistants.data

    for assistant in assistants_list:
        del_assistant_response = client.beta.assistants.delete(assistant.id)
        print(del_assistant_response)
