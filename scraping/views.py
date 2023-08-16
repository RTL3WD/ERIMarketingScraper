from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from urllib.request import urlretrieve
import urllib.error
import re
import pytesseract
import os
from pdf2image import convert_from_path
from undetected_chromedriver import Chrome, ChromeOptions
import airtable
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import cv2
import io
import numpy as np  # Import NumPy
import os
import psutil

api_key = 'e77cab79ca105a72b529f7b0026b7ee1'
url = 'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange'


def index(request):
    context = {'segment': 'index'}
    context['records'] = []
    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    load_template = request.path.split('/')[-1]

    if load_template == 'admin':
        return HttpResponseRedirect(reverse('admin:index'))
    context['segment'] = load_template

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


def download_file(download_url):
    try:
        file_name = download_url['name'] + '.pdf'
        file_name = file_name.replace('/','-').replace(':', '')
        contentName = download_url['contentName'].replace('/','-')
        if not os.path.exists('pdfs/' + contentName):
                    os.makedirs('pdfs/' + contentName)
                    
        if not os.path.exists('pdfs/' + contentName + '/' + file_name):
            urlretrieve(download_url['href'], 'pdfs/' + contentName + '/' + file_name)
            print(f"File downloaded successfully: {file_name}")
    except urllib.error.URLError as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

            
circles = []
counter = 0
counter2 = 0
Clickpoint1 = []
Clickpoint2 = []
myCoordinates = []   
img = None
def mouseClickPoints(event, x, y, flags, params):
    global counter, Clickpoint1, Clickpoint2, counter2, circles
    if event == cv2.EVENT_LBUTTONDOWN:
        # Draw circle in red color
        cv2.circle(img, (x, y), 3, (0, 0, 255), cv2.FILLED)
        if counter == 0:
            Clickpoint1 = int(x), int(y)
            counter += 1
        elif counter == 1:
            Clickpoint2 = int(x), int(y)
            if counter2 == 0:
                myCoordinates.append([Clickpoint1, Clickpoint2])
            else:
                myCoordinates[-1][1] = Clickpoint2  # Update bottom-right corner
            counter = 0
            circles.append([x, y])
            counter2 += 1
            if counter2 == 2:  # Capture all four corners
                counter2 = 0
            
def choose_location(image):
    global img
    # Convert image to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')  # Save as JPEG (or other supported format)
    img_bytes = img_bytes.getvalue()

    # Decode the image bytes using OpenCV
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), 1)
    height, width, channel = img.shape
    img = cv2.resize(img, (width//2, height//2))
    # Function to store left-mouse click coordinates
    
    while True:
        # To Display clicked points
        for x, y in circles:
            cv2.circle(img, (x, y), 3, (0,0,255), cv2.FILLED)
        # Display original image
        cv2.imshow('Original Image', img)
        # Collect coordinates of mouse click points
        cv2.setMouseCallback('Original Image', mouseClickPoints)
        # Press 'x' in keyboard to stop the program and print the coordinate values
        if cv2.waitKey(1) & 0xFF == ord('x'):
            print(myCoordinates)
            break         
                    
def scrape(request):
    print('start')
    try:
        optionsUC = webdriver.ChromeOptions()
        optionsUC.add_argument('--window-size=360,640')
        optionsUC.add_argument('--no-sandbox')
        try:
            driver =  webdriver.Chrome(options=optionsUC)
            try:
                # return False
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
                driver.get('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange')
                sleep(5)
                client = AnticaptchaClient(api_key)
                site_key = driver.find_element(By.CSS_SELECTOR, 'div.g-recaptcha').get_attribute('data-sitekey')  # grab from site
                task = NoCaptchaTaskProxylessTask(url, site_key)
                job = client.createTask(task)
                print("Waiting to solution by Anticaptcha workers")
                job.join()
                # Receive response
                response = job.get_solution_response()
                print("Received solution", response)
                recaptcha_textarea = driver.find_element(By.ID, "g-recaptcha-response")
                driver.execute_script(f"arguments[0].innerHTML = '{response}';", recaptcha_textarea)
                driver.execute_script("document.getElementById('captcha_form').submit();")

                WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH,'//*[@id="selCountyCourt"]/option[text()="Albany County Supreme Court"]')))
                driver.find_element(By.XPATH,'//*[@id="selCountyCourt"]/option[text()="Albany County Supreme Court"]').click()
                driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(Keys.BACKSPACE * 50)
                driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(datetime.utcnow().strftime('%m/%d/%Y'))
                driver.find_element(By.CSS_SELECTOR,'input[type*="submit"]').click()
                sleep(7)
                driver.find_element(By.XPATH,'//*[@id="selSortBy"]/option[text()="Case Type"]').click()
                driver.find_element(By.CSS_SELECTOR,'caption input[type*="submit"]').click()
                sleep(6)
                elements = driver.find_elements(By.CSS_SELECTOR, '#form > table.NewSearchResults > tbody > tr > td:nth-child(1) > a')
                for i,e in enumerate(elements):
                    href = e.get_attribute('href')
                    elemntDriver = Chrome()
                    elemntDriver.get(href)
                    docs = elemntDriver.find_elements(By.CSS_SELECTOR, 'table.NewSearchResults > tbody > tr > td:nth-child(2) > a')
                    contentName= elemntDriver.find_element(By.CSS_SELECTOR, '#row').get_attribute('value').strip()
                    hrefs = []
                    
                    for doc in docs:
                        hrefs.append({'href': doc.get_attribute('href'), 'name': doc.get_attribute('innerHTML').strip(),'contentName': contentName})
                    
                    ActionChains(elemntDriver).key_down(Keys.CONTROL).send_keys("t").key_up(Keys.CONTROL).perform()
                    elemntDriver.execute_script('''window.open("http://bings.com","_blank");''')
                    sleep(5)
                    elemntDriver.switch_to.window(elemntDriver.window_handles[1])
                    
                    for href in hrefs:
                        print(href)
                        try:
                            elemntDriver.get(href['href'])
                            download_file(href)
                            sleep(5)
                        except Exception as e:
                            print(e)
                        sleep(5)

                    elemntDriver.quit()
                    sleep(3)                
                    
                # driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
            except Exception as e:
                print('-'*50)
                print(e)
            finally:
                driver.quit()
                PROCNAME = "chromedriver" # or chromedriver or IEDriverServer
                for proc in psutil.process_iter():
                    # check whether the process name matches
                    if proc.name() == PROCNAME:
                        proc.kill()
                context = {'segment': 'index'}
                records = []
                folder_path='pdfs'
                output_folder='ocr'
                # Create the output folder if it doesn't exist
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                # Get a list of all files in the pdfs folder
                folders = os.listdir(folder_path)
                # folders = [folder for folder in folders if '907737-23' in folder]
                for folder in folders:
                    files = [file for file in os.listdir(folder_path + '/' + folder) if file.endswith(".pdf")]
                    record = {}
                    record['folder'] = folder
                    for pdf_file in files:
                        try:
                            pdf_path = os.path.join(folder_path + '/' + folder, pdf_file)
                            # Convert PDF to images
                            images = convert_from_path(pdf_path)
                            
                            if 'summons' in pdf_file.lower():
                                for i, image in enumerate(images):
                                    if i == 0:
                                        #(left, upper, right, lower)
                                        cropped_image = image.crop((1, 100, 1500, 1000))
                                        text = pytesseract.image_to_string(cropped_image, lang='eng')
                                        # print(text)
                                        creadetor_name = ''
                                        company_suid = ''
                                        officers_comany = ''
                                        creadetor_name_elments = [e for e in re.findall('wenn eee x\\n.*?,||wenn eee x\\n\\n.*?,' ,text) if len(e) > 0]
                                        if(len(creadetor_name_elments)>0):
                                            creadetor_name = creadetor_name_elments[0].replace('\\n','').replace('wenn eee x', '').replace('wenn eee x', '')
                                            if(',' in creadetor_name[len(creadetor_name)-1]):
                                                creadetor_name = creadetor_name.replace(',','')
                                        else:
                                            img_bytes = io.BytesIO()
                                            image.save(img_bytes, format='JPEG')  # Save as JPEG (or other supported format)
                                            img_bytes = img_bytes.getvalue()

                                            # Decode the image bytes using OpenCV
                                            img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), 1)
                                            # choose_location(image)
                                            height, width, channel = img.shape
                                            # Resizing image if required
                                            img = cv2.resize(img, (width//2, height//2))
                                            
                                            # Convert image to grey scale
                                            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                                            # Converting grey image to binary image by Thresholding
                                            threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                                            roi_coordinate = [[(9, 84), (486, 119)]]
                                            top_left_x = list(roi_coordinate[0])[0][0]
                                            bottom_right_x = list(roi_coordinate[0])[1][0]
                                            top_left_y = list(roi_coordinate[0])[0][1]
                                            bottom_right_y = list(roi_coordinate[0])[1][1]
                                            img_cropped = threshold_img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
                                            # Draw rectangle for area of interest (ROI)
                                            cv2.rectangle(img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 3)
                                            
                                            # OCR section to extract text using pytesseract in python
                                            # configuring parameters for tesseract
                                            custom_config = r'--oem 3 --psm 6'
                                            
                                            # Extract text within specific coordinate using pytesseract OCR Python
                                            # Providing cropped image as input to the OCR
                                            creadetor_name = pytesseract.image_to_string(img_cropped, config=custom_config, lang='eng')
                                            creadetor_name= creadetor_name.replace(',','')
                                            font = cv2.FONT_HERSHEY_DUPLEX
                                            # Red color code
                                            red_color = (0,0,255)
                                            
                                            # cv2.putText(img, f'{creadetor_name}', (top_left_x-25, top_left_y - 10), font, 0.5, red_color, 1)
                                            # cv2.imshow('img', img)
                                            # cv2.waitKey(0)

                                        if(len(re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text))>0):
                                            company_suid = re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text)[0]
                                            company_suid = company_suid.replace(re.findall('-against-\\n|-against-\\n\\n' ,company_suid)[0], '')
                                        else:
                                            img_bytes = io.BytesIO()
                                            image.save(img_bytes, format='JPEG')  # Save as JPEG (or other supported format)
                                            img_bytes = img_bytes.getvalue()

                                            # Decode the image bytes using OpenCV
                                            img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), 1)
                                            # choose_location(image)
                                            height, width, channel = img.shape
                                            # Resizing image if required
                                            img = cv2.resize(img, (width//2, height//2))
                                            
                                            # Convert image to grey scale
                                            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                                            # Converting grey image to binary image by Thresholding
                                            threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                                            roi_coordinate = [[(7, 205), (499, 239)]]
                                            top_left_x = list(roi_coordinate[0])[0][0]
                                            bottom_right_x = list(roi_coordinate[0])[1][0]
                                            top_left_y = list(roi_coordinate[0])[0][1]
                                            bottom_right_y = list(roi_coordinate[0])[1][1]
                                            img_cropped = threshold_img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
                                            # Draw rectangle for area of interest (ROI)
                                            cv2.rectangle(img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 3)
                                            
                                            # OCR section to extract text using pytesseract in python
                                            # configuring parameters for tesseract
                                            custom_config = r'--oem 3 --psm 6'
                                            
                                            # Extract text within specific coordinate using pytesseract OCR Python
                                            # Providing cropped image as input to the OCR
                                            company_suid = pytesseract.image_to_string(img_cropped, config=custom_config, lang='eng')
                                            company_suid = re.findall('.*?,|.*?;' ,company_suid)[0]
                                            company_suid= company_suid.replace(',','')
                                            font = cv2.FONT_HERSHEY_DUPLEX
                                            # Red color code
                                            red_color = (0,0,255)
                                            
                                            # cv2.putText(img, f'{company_suid}', (top_left_x-25, top_left_y - 10), font, 0.5, red_color, 1)
                                            # cv2.imshow('img', img)
                                            # cv2.waitKey(0)
                                            
                                        if(len(re.findall('-against-\\n.*?,[\s\S]*?,|-against-\\n\\n.*?,[\s\S]*?,|-against-\\n\\n.*?;[\s\S]*?;|-against-\\n\\n.*?;[\s\S]*?\\n\\n' ,text))>0):
                                            officers_comany = re.findall('-against-\\n.*?,[\s\S]*?,|-against-\\n\\n.*?,[\s\S]*?,|-against-\\n\\n.*?;[\s\S]*?;|-against-\\n\\n.*?;[\s\S]*?\\n\\n' ,text)[0]
                                            officers_comany = officers_comany.replace(re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,officers_comany)[0], '').strip()
                                        else:
                                            img_bytes = io.BytesIO()
                                            image.save(img_bytes, format='JPEG')  # Save as JPEG (or other supported format)
                                            img_bytes = img_bytes.getvalue()

                                            # Decode the image bytes using OpenCV
                                            img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), 1)
                                            # choose_location(image)
                                            height, width, channel = img.shape
                                            # Resizing image if required
                                            img = cv2.resize(img, (width//2, height//2))
                                            
                                            # Convert image to grey scale
                                            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                                            # Converting grey image to binary image by Thresholding
                                            threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                                            roi_coordinate = [[(7, 205), (499, 239)]]
                                            top_left_x = list(roi_coordinate[0])[0][0]
                                            bottom_right_x = list(roi_coordinate[0])[1][0]
                                            top_left_y = list(roi_coordinate[0])[0][1]
                                            bottom_right_y = list(roi_coordinate[0])[1][1]
                                            img_cropped = threshold_img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
                                            # Draw rectangle for area of interest (ROI)
                                            cv2.rectangle(img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 3)
                                            
                                            # OCR section to extract text using pytesseract in python
                                            # configuring parameters for tesseract
                                            custom_config = r'--oem 3 --psm 6'
                                            
                                            # Extract text within specific coordinate using pytesseract OCR Python
                                            # Providing cropped image as input to the OCR
                                            officers_comany = pytesseract.image_to_string(img_cropped, config=custom_config, lang='eng')
                                            officers_comany = re.findall('.*?,[\s\S]*?,|.*?;[\s\S]*?;' ,officers_comany)[0]
                                            officers_comany= officers_comany.replace(re.findall('.*?,|.*?;' ,officers_comany)[0],'')
                                            officers_comany= officers_comany.replace(',','')
                                            font = cv2.FONT_HERSHEY_DUPLEX
                                            # Red color code
                                            red_color = (0,0,255)
                                            
                                            # cv2.putText(img, f'{officers_comany}', (top_left_x-25, top_left_y - 10), font, 0.5, red_color, 1)
                                            # cv2.imshow('img', img)
                                            # cv2.waitKey(0)
                                            
                                        record['creadetor_name'] = creadetor_name
                                        record['company_suid'] = company_suid
                                        record['officers_comany'] = officers_comany
                                        print(creadetor_name)
                                        print(company_suid)
                                        print(officers_comany)
                                        
                                        
                            if 'exhibit' in pdf_file.lower() or 'statement of authorization' in pdf_file.lower():
                                for i, image in enumerate(images):
                                    if i == 0 or i == 1:
                                        # Perform OCR on each image
                                        text = pytesseract.image_to_string(image, lang='eng')
                                        # print(text)
                                        for info in re.findall('.*\\n' ,text):
                                            info = info.replace('\n','')
                                            if info != '':
                                                
                                                if len(re.findall('Business Address:.*?:',info)) > 0:
                                                    business_address = re.findall('Business Address:.*?:',info)[0].replace('Business Address:','')
                                                    business_address = business_address.replace(re.findall('[a-zA-Z]+?:',business_address)[0],'')
                                                    print(f'business_address: ${business_address}')
                                                    record['business_address'] = business_address
                                                    
                                                    if len(re.findall('City:.*?:',info)) > 0:
                                                        business_city = re.findall('City:.*?:',info)[0].replace('City:','')
                                                        business_city = business_city.replace(re.findall('[a-zA-Z]+?:',business_city)[0],'')
                                                        print(f'business_city: ${business_city}')
                                                        record['business_city'] = business_city
                                                        
                                                    if len(re.findall('State:.*?:',info)) > 0:
                                                        business_state = re.findall('State:.*?:',info)[0].replace('State:','')
                                                        business_state = business_state.replace(re.findall('[a-zA-Z]+?:',business_state)[0],'')
                                                        print(f'business_state: ${business_state}')
                                                        record['business_state'] = business_state
                                                        
                                                    if len(re.findall('Zip:.*?:',info)) > 0:
                                                        business_zip = re.findall('Zip:.*?:',info)[0].replace('Zip:','')
                                                        business_zip = business_zip.replace(re.findall('[a-zA-Z]+?:',business_zip)[0],'')
                                                        print(f'business_zip: ${business_zip}')
                                                        record['business_zip'] = business_zip
                                                        
                                                if len(re.findall('Contact Address:.*?:',info)) > 0:
                                                    contact_address = re.findall('Contact Address:.*?:',info)[0].replace('Contact Address:','')
                                                    contact_address = contact_address.replace(re.findall('[a-zA-Z]+?:',contact_address)[0],'')
                                                    print(f'contact_address: ${contact_address}')
                                                    record['contact_address'] = contact_address
                                                    
                                                    if len(re.findall('City:.*?:',info)) > 0:
                                                        contact_city = re.findall('City:.*?:',info)[0].replace('City:','')
                                                        contact_city = contact_city.replace(re.findall('[a-zA-Z]+?:',contact_city)[0],'')
                                                        print(f'contact_city: ${contact_city}')
                                                        record['contact_city'] = contact_city
                                                        
                                                    if len(re.findall('State:.*?:',info)) > 0:
                                                        contact_state = re.findall('State:.*?:',info)[0].replace('State:','')
                                                        contact_state = contact_state.replace(re.findall('[a-zA-Z]+?:',contact_state)[0],'')
                                                        print(f'contact_state: ${contact_state}')
                                                        record['contact_state'] = contact_state
                                                        
                                                    if len(re.findall('Zip:.*?:',info)) > 0:
                                                        contact_zip = re.findall('Zip:.*?:',info)[0].replace('Zip:','')
                                                        contact_zip = contact_zip.replace(re.findall('[a-zA-Z]+?:',contact_zip)[0],'')
                                                        print(f'contact_zip: ${contact_zip}')
                                                        record['contact_zip'] = contact_zip
                                                    
                                            
                                                    
                                                if len(re.findall('[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}',info)) > 0:
                                                    tel = re.findall('[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}',info)[0]
                                                    print(f'tel: ${tel}')
                                                    record['tel'] = tel
                                                    
                                                if len(re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',info)) > 0:
                                                    email = re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',info)[0]
                                                    print(f'email: ${email}')
                                                    record['email'] = email
                                        
                                        if(len(re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text))>0):
                                            business_city = re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text)[0].replace('Signature City, State and Zip Code','')
                                            business_city = business_city.replace(re.findall(',.*\d*',business_city)[0],'')
                                            print(f'business_city: ${business_city}')
                                            record['business_city'] = business_city
                                            
                                        if(len(re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text))>0):
                                            business_state = re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text)[0].replace('Signature City, State and Zip Code','')
                                            business_state = business_state.replace(re.findall('.*,',business_state)[0],'')
                                            business_state = business_state.replace(re.findall('\d+',business_state)[0],'')
                                            print(f'business_state: ${business_state}')
                                            record['business_state'] = business_state
                                            
                                        if(len(re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text))>0):
                                            business_zip = re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text)[0].replace('Signature City, State and Zip Code','')
                                            business_zip = re.findall('\d+',business_zip)[0]
                                            print(f'business_zip: ${business_zip}')
                                            record['business_zip'] = business_zip
                                            

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
                                record['price'] = price
                        except Exception as e:
                            print(e)
                            
                    records.append(record)
                            
                    
                context['records'] = records
                html_template = loader.get_template('home/index.html')
                return HttpResponse(html_template.render(context, request))
        except Exception as e:
            print(e)
            pass
        sleep(20)
    except Exception as e:
        print(e)
        pass
    
    
def getRecordsFromPhoneBurner(request):
    at = airtable.Airtable('appKpiXBqqK7QvT6u', 'patwsQ3w8O4VGC05S.01759369d41db17822bcf0074f5daf046cc68ef136677dd68a15550f0e843bef')
    at.create('Leads', {'First Name': 'test'})
    return HttpResponse('ok')