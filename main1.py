from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
# from selenium_recaptcha_solver import RecaptchaSolver
from selenium.webdriver.chrome.service import Service
import threading
from selenium.webdriver.common.proxy import Proxy, ProxyType
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from urllib.request import urlretrieve
import urllib.error
import os
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfWriter, PdfReader 
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
# from solverecaptchas.solver import Solver
import asyncio

api_key = 'fb30449e4a2eedddda251a47e9596970'
site_key = '6LfmfjYUAAAAAMujuZ5wPlqjGqVYr7Ie4okh5aF-'  # grab from site
url = 'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange'

timeout_duration = 60  # Timeout duration in seconds

def click_recaptcha_with_timeout(solver, iframe):
    event = threading.Event()

    def click_recaptcha():
        try:
            solver.click_recaptcha_v2(iframe=iframe)
        except Exception as e:
            print(e)
        event.set()

    thread = threading.Thread(target=click_recaptcha)
    thread.start()

    # Wait for the timeout duration or until the thread finishes
    event.wait(timeout_duration)

    if thread.is_alive():
        raise TimeoutError("Timeout reached for click_recaptcha_v2().")
    
def download_file(download_url):
    try:
        file_name = download_url['contentName'] + '-' + download_url['name'] + '.pdf'
        file_name = file_name.replace('/','-').replace(':', '')
        if not os.path.exists('pdfs/' + file_name):
            urlretrieve(download_url['href'], 'pdfs/' + file_name)
            print(f"File downloaded successfully: {file_name}")
    except urllib.error.URLError as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
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
        
        if 'summons' in pdf_file.lower():
            for i, image in enumerate(images):
                if i == 0:
                    #(left, upper, right, lower)
                    cropped_image = image.crop((1, 100, 1000, 1000))
                    text = pytesseract.image_to_string(cropped_image, lang='eng')
                    # print(text)
                    creadetor_name = ''
                    company_suid = ''
                    officers_comany = ''
                    
                    if(len(re.findall('x\\n.*?,' ,text))>0):
                        creadetor_name = re.findall('x\\n.*?,' ,text)[0].replace('x\\n', '')
                        
                    if(len(re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text))>0):
                        company_suid = re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text)[0]
                        company_suid = company_suid.replace(re.findall('-against-\\n|-against-\\n\\n' ,company_suid)[0], '')
                        
                        
                    if(len(re.findall('-against-\\n.*?,[\s\S]*?,|-against-\\n\\n.*?,[\s\S]*?,|-against-\\n\\n.*?;[\s\S]*?;|-against-\\n\\n.*?;[\s\S]*?\\n\\n' ,text))>0):
                        officers_comany = re.findall('-against-\\n.*?,[\s\S]*?,|-against-\\n\\n.*?,[\s\S]*?,|-against-\\n\\n.*?;[\s\S]*?;|-against-\\n\\n.*?;[\s\S]*?\\n\\n' ,text)[0]
                        officers_comany = officers_comany.replace(re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,officers_comany)[0], '').strip()
                    
                    print(creadetor_name)
                    print(company_suid)
                    print(officers_comany)
                    
                    
        if 'exhibit' in pdf_file.lower():
            for i, image in enumerate(images):
                if i == 0:
                    #(left, upper, right, lower)
                    cropped_image = image.crop((1, 200, 3000, 1100))
                    # Perform OCR on each image
                    text = pytesseract.image_to_string(cropped_image, lang='eng')
                        
                    for info in re.findall('.*\\n' ,text):
                        info = info.replace('\n','')
                        if info != '':
                            
                            if len(re.findall('Business Address:.*?:',info)) > 0:
                                business_address = re.findall('Business Address:.*?:',info)[0].replace('Business Address:','')
                                business_address = business_address.replace(re.findall('[a-zA-Z]+?:',business_address)[0],'')
                                print(f'business_address: ${business_address}')
                                
                                if len(re.findall('City:.*?:',info)) > 0:
                                    business_city = re.findall('City:.*?:',info)[0].replace('City:','')
                                    business_city = business_city.replace(re.findall('[a-zA-Z]+?:',business_city)[0],'')
                                    print(f'business_city: ${business_city}')
                                    
                                if len(re.findall('State:.*?:',info)) > 0:
                                    business_state = re.findall('State:.*?:',info)[0].replace('State:','')
                                    business_state = business_state.replace(re.findall('[a-zA-Z]+?:',business_state)[0],'')
                                    print(f'business_state: ${business_state}')
                                    
                                if len(re.findall('Zip:.*?:',info)) > 0:
                                    business_zip = re.findall('Zip:.*?:',info)[0].replace('Zip:','')
                                    business_zip = business_zip.replace(re.findall('[a-zA-Z]+?:',business_zip)[0],'')
                                    print(f'business_zip: ${business_zip}')
                                    
                            if len(re.findall('Contact Address:.*?:',info)) > 0:
                                contact_address = re.findall('Contact Address:.*?:',info)[0].replace('Contact Address:','')
                                contact_address = contact_address.replace(re.findall('[a-zA-Z]+?:',contact_address)[0],'')
                                print(f'contact_address: ${contact_address}')
                                
                                if len(re.findall('City:.*?:',info)) > 0:
                                    contact_city = re.findall('City:.*?:',info)[0].replace('City:','')
                                    contact_city = contact_city.replace(re.findall('[a-zA-Z]+?:',contact_city)[0],'')
                                    print(f'contact_city: ${contact_city}')
                                    
                                if len(re.findall('State:.*?:',info)) > 0:
                                    contact_state = re.findall('State:.*?:',info)[0].replace('State:','')
                                    contact_state = contact_state.replace(re.findall('[a-zA-Z]+?:',contact_state)[0],'')
                                    print(f'contact_state: ${contact_state}')
                                    
                                if len(re.findall('Zip:.*?:',info)) > 0:
                                    contact_zip = re.findall('Zip:.*?:',info)[0].replace('Zip:','')
                                    contact_zip = contact_zip.replace(re.findall('[a-zA-Z]+?:',contact_zip)[0],'')
                                    print(f'contact_zip: ${contact_zip}')
                                
                           
                                
                            if len(re.findall('[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}',info)) > 0:
                                tel = re.findall('[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}',info)[0]
                                print(f'tel: ${tel}')
                                
                            if len(re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',info)) > 0:
                                email = re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',info)[0]
                                print(f'email: ${email}')
                        

                # Save the OCR text to a text file
                # txt_file_name = f"{pdf_file.replace('.pdf', '')}_page_{i + 1}.txt"
                # txt_file_path = os.path.join(output_folder, txt_file_name)

                # with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                #     txt_file.write(text)
                
        if 'complaint' in pdf_file.lower():
            numbers = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='eng')
                for info in re.findall('.*\\n' ,text):
                    for number in re.findall('\$\d+,\d+\.\d+|\$\d+,\d+|\$\d+',info):
                        number = number.replace('$','').replace(',','')
                        numbers.append(float(number))
            price = max(numbers)
            print(f'price: ${price}')
                
def crop_pdfs(folder_path):
    # Get a list of all files in the pdfs folder
    files = [file for file in os.listdir(folder_path) if file.endswith(".pdf")]

    for pdf_file in files:
        pdf_path = os.path.join(folder_path, pdf_file)

        with open(pdf_path, "rb") as in_f: 
            input1 = PdfReader(in_f) 
            output = PdfWriter()
            print(input1.pages) 

            numPages = len(input1.pages)
            for i in range(numPages): 
                if(i == (numPages-1)):
                    page = input1.pages[i]
                    page.trimbox.lower_left = (500, 160) 
                    page.trimbox.upper_right = (255, 20)
                    page.cropbox.lower_left = (500, 160) 
                    page.cropbox.upper_right = (255, 20) 
                    output.add_page(page) 

        with open(pdf_path, "wb") as out_f: 
            output.write(out_f)

def main():
    try:
        optionsUC = webdriver.ChromeOptions()
        service = Service(executable_path='./chromedriver.exe')
        print('+'*50)
        optionsUC.add_argument('--window-size=360,640')
        optionsUC.add_argument('--no-sandbox')
        try:
            profile_directory = r'C:\ChromeDevSession'
            # optionsUC.add_argument(f'--user-data-dir={profile_directory}')
            driver =  webdriver.Chrome(options=optionsUC)
            try:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
                # solver = RecaptchaSolver(driver=driver)
                # client = Solver('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange', site_key)
                # result = asyncio.run(client.start())
                # if result:
                #     print(result)
                # driver.get('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange')
                # sleep(5)
                # recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
                # client = AnticaptchaClient(api_key)
                # task = NoCaptchaTaskProxylessTask(url, site_key)
                # job = client.createTask(task)
                # print("Waiting to solution by Anticaptcha workers")
                # job.join()
                # # Receive response
                # response = job.get_solution_response()
                # print("Received solution", response)
                # recaptcha_textarea = driver.find_element(By.ID, "g-recaptcha-response")
                # driver.execute_script(f"arguments[0].innerHTML = '{response}';", recaptcha_textarea)
                # driver.execute_script("document.getElementById('captcha_form').submit();")
                
                # # click_recaptcha_with_timeout(solver, recaptcha_iframe)
                # if recaptcha_iframe:
                #     print('resolve')
                #     sleep(40)
                # # WebDriverWait(driver, 600).until(EC.presence_of_element_located(By.XPATH,'//*[@id="selCountyCourt"]/option[text()="Albany County Supreme Court"]'))
                # driver.find_element(By.XPATH,'//*[@id="selCountyCourt"]/option[text()="Albany County Supreme Court"]').click()
                # driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(Keys.BACKSPACE * 50)
                # driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(datetime.utcnow().strftime('%m/%d/%Y'))
                # driver.find_element(By.CSS_SELECTOR,'input[type*="submit"]').click()
                # sleep(30)
                # driver.find_element(By.XPATH,'//*[@id="selSortBy"]/option[text()="Case Type"]').click()
                # driver.find_element(By.CSS_SELECTOR,'caption input[type*="submit"]').click()
                # sleep(14)
                # elements = driver.find_elements(By.CSS_SELECTOR, '#form > table.NewSearchResults > tbody > tr > td:nth-child(1) > a')
                # for e in elements:
                #     href = e.get_attribute('href')
                #     elemntDriver = Chrome()
                #     elemntDriver.get(href)
                #     sleep(20)
                #     elemntDriver.quit()
                #     sleep(3)
                driver.get('https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=zQD2/s9RZWPxYIwzQ0DUjw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1')
                docs = driver.find_elements(By.CSS_SELECTOR, 'table.NewSearchResults > tbody > tr > td:nth-child(2) > a')
                contentName= driver.find_element(By.CSS_SELECTOR, '#content').get_attribute('innerHTML').strip()
                hrefs = []
                
                for doc in docs:
                    hrefs.append({'href': doc.get_attribute('href'), 'name': doc.get_attribute('innerHTML').strip(),'contentName': contentName})
                
                ActionChains(driver).key_down(Keys.CONTROL).send_keys("t").key_up(Keys.CONTROL).perform()
                driver.execute_script('''window.open("http://bings.com","_blank");''')
                sleep(5)
                driver.switch_to.window(driver.window_handles[1])
                
                for href in hrefs:
                    print(href)
                    driver.get(href['href'])
                    download_file(href)
                    sleep(10)
                    
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
            except Exception as e:
                print('-'*50)
                print(e)
            finally:
                driver.quit()
                # perform_ocr_on_pdfs('pdfs', 'ocr')
        except Exception as e:
            print(e)
            pass
        sleep(20)
    except Exception as e:
        print(e)
        pass    
    
main()
# crop_pdfs('pdfs')
perform_ocr_on_pdfs('pdfs', 'ocr')