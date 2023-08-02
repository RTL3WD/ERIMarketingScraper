import os
import pytesseract
from pdf2image import convert_from_path
    
        
def perform_ocr_on_pdfs(folder_path, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get a list of all files in the pdfs folder
    files = [file for file in os.listdir(folder_path) if file.endswith(".pdf")]

    for pdf_file in files:
        pdf_path = os.path.join(folder_path, pdf_file)

        # Convert PDF to images
        images = convert_from_path(pdf_path)

        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image, lang='eng')
                    
            # Save the OCR text to a text file
            txt_file_name = f"{pdf_file.replace('.pdf', '')}_page_{i + 1}.txt"
            txt_file_path = os.path.join(output_folder, txt_file_name)

            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)
            

perform_ocr_on_pdfs('pdfs', 'ocr')