import os
import shutil


def clean_directory(dir_path):
    # Remove the directory and its contents if it exists
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    # Recreate the directory
    os.makedirs(dir_path)
