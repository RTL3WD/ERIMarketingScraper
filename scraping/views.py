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
from datetime import datetime, timedelta
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
import psutil
from imutils import contours
from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
import fitz
import logging
import threading
import concurrent.futures
from .models import Lead
from urllib.parse import unquote

logger = logging.getLogger(__name__)

api_key = 'e77cab79ca105a72b529f7b0026b7ee1'
url = 'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange'


def index(request):
    context = {'segment': 'index'}
    context['records'] = []
    leads = Lead.objects.all()
    context['records'] = leads
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

def download_pdfs(link,records):      
    optionsUC = webdriver.ChromeOptions()
    optionsUC.add_argument('--window-size=360,640')
    optionsUC.add_argument('--no-sandbox')
    # optionsUC.add_argument('--headless')
    optionsUC.add_argument('start-maximized')
    elemntDriver = webdriver.Chrome(options=optionsUC)
    elemntDriver.get(link)
    docs_elements = elemntDriver.find_elements(By.CSS_SELECTOR, 'table.NewSearchResults > tbody > tr')
    docs = []
    for doc in docs_elements:
        if 'processed' in doc.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').get_attribute('innerHTML').strip().lower():
            docs.append(doc.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a'))
    contentName= elemntDriver.find_element(By.CSS_SELECTOR, '#row').get_attribute('value').strip()
    hrefs = []
    
    for doc in docs:
        hrefs.append({'href': doc.get_attribute('href'), 'name': doc.get_attribute('innerHTML').strip(),'contentName': contentName})
    
    ActionChains(elemntDriver).key_down(Keys.CONTROL).send_keys("t").key_up(Keys.CONTROL).perform()
    elemntDriver.execute_script('''window.open("http://bings.com","_blank");''')
    sleep(5)
    elemntDriver.switch_to.window(elemntDriver.window_handles[1])
    if len(docs_elements)>2:
        for href in hrefs:
            if 'summons' in href['name'].lower() or 'exhibit' in href['name'].lower() or 'statement of authorization' in href['name'].lower() or 'complaint' in href['name'].lower(): 
                try:
                    elemntDriver.get(href['href'])
                    download_file(href)
                    sleep(5)
                except Exception as e:
                    print(e)
                sleep(5)
        elemntDriver.quit()
        existing_lead = Lead.objects.filter(folder_id=f'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId={contentName.replace("-","/")}&display=all').first()
        # if not existing_lead:
        extract_texts(contentName,records)
    else:
        elemntDriver.quit()
    sleep(3)          
    
    
def extract_texts(folder,records):
    folder_path='pdfs'
    files = [file for file in os.listdir(folder_path + '/' + folder) if file.endswith(".pdf")]
    record = {}
    
    record['folder'] = f'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId={folder.replace("-","/")}&display=all'
    if folder != '':
        for pdf_file in files:
            if 'complaint' in pdf_file.lower():
                pdf_path = os.path.join(folder_path + '/' + folder, pdf_file)
                numbers = []
                county = ''
                try:
                    images = convert_from_path(pdf_path)
                    for i, image in enumerate(images):
                        text = pytesseract.image_to_string(image, lang='eng')
                        for info in re.findall('.*\\n' ,text):
                            if(len(re.findall('FILED:[\s\S]*?COUNTY',info))>0) and county == '':
                                try:
                                    county = re.findall('FILED:[\s\S]*?COUNTY',info)[0].replace('FILED:','')
                                    record['county'] = county
                                except Exception as e:
                                    print('business zip2 error'+str(e))
                            for number in re.findall('\$\d+,\d+\.\d+|\$\d+,\d+|\$\d+',info):
                                number = number.replace('$','').replace(',','')
                                numbers.append(float(number))
                    if len(numbers)>0:
                        price = max(numbers)
                        record['price'] = price
                except Exception as e:
                    print('complaint error'+str(e))
        print(record['price'] if 'price' in record else 'less')
        if 'price' in record and record['price'] >= 20000: 
            for pdf_file in files:
                try:
                    pdf_path = os.path.join(folder_path + '/' + folder, pdf_file)
                    print(pdf_path)
                    if 'summons' in pdf_file.lower() or 'petition' in pdf_file.lower():
                        try:
                            images = convert_from_path(pdf_path, first_page=0, last_page=2)
                            for i, image in enumerate(images):
                                if i == 0 or i == 1:
                                    custom_config = r'--oem 3 --psm 6'
                                    #(left, upper, right, lower)
                                    cropped_image = image.crop((1, 100, 1000, 1000))
                                    text = pytesseract.image_to_string(cropped_image, lang='eng')
                                    creadetor_name = ''
                                    company_suid = ''
                                    #(left, upper, right, lower)
                                    cropped_image = image.crop((1, 150, 1500, 1000))
                                    img_bytes = io.BytesIO()
                                    cropped_image.save(img_bytes, format='JPEG')  # Save as JPEG (or other supported format)
                                    img_bytes = img_bytes.getvalue()
                                    
                                    # # Decode the image bytes using OpenCV
                                    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
                                    kernel_size = 5
                                    blur_gray = cv2.GaussianBlur(img,(kernel_size, kernel_size),0)
                                    low_threshold = 50
                                    high_threshold = 150
                                    edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
                                    rho = 1  # distance resolution in pixels of the Hough grid
                                    theta = np.pi / 180  # angular resolution in radians of the Hough grid
                                    threshold = 15  # minimum number of votes (intersections in Hough grid cell)
                                    min_line_length = 250  # minimum number of pixels making up a line
                                    max_line_gap = 5  # maximum gap in pixels between connectable line segments
                                    line_image = np.copy(img) * 0  # creating a blank to draw lines on

                                    # Run Hough on edge detected image
                                    # Output "lines" is an array containing endpoints of detected line segments
                                    lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                                                        min_line_length, max_line_gap)
                                    image_height, image_width = img.shape[:2]
                                    upper_x1 = 0
                                    upper_y1 = 0
                                    for i,line in enumerate(lines):
                                        x1, y1, x2, y2 = line[0]
                                        slope = (y2 - y1) / (x2 - x1 + 1e-5)  # Calculate slope while avoiding division by zero
                                        angle = np.arctan(slope) * 180 / np.pi
                                        average_y = (y1 + y2) / 2
                                        try:
                                            if abs(angle) < 10:
                                                if average_y < image_height / 2:
                                                    for x1,y1,x2,y2 in line:
                                                        upper_x1 = x1
                                                        upper_y1 = y1 +70
                                        except Exception as e:
                                            pass
                                                        
                                    
                                    for i,line in enumerate(lines):
                                        x1, y1, x2, y2 = line[0]
                                        slope = (y2 - y1) / (x2 - x1 + 1e-5)  # Calculate slope while avoiding division by zero
                                        angle = np.arctan(slope) * 180 / np.pi
                                        average_y = (y1 + y2) / 2
                                        try:
                                            if abs(angle) < 10:
                                                if average_y < image_height / 2:
                                                    for x1,y1,x2,y2 in line:
                                                        if creadetor_name == '':
                                                            text_region = img[y1:y2 + 400, x1:x2]
                                                            box_test = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                            print(re.findall('[\s\S]*?Plaintiff' ,box_test))
                                                            if(len(re.findall('[\s\S]*?Plaintiff' ,box_test))>0):
                                                                creadetor_name = re.findall('[\s\S]*?Plaintiff' ,box_test)[0].replace('Plaintiff','').strip()
                                                            else:
                                                                text_region = img[y1:y2 + 70, x1:x2]
                                                                creadetor_name = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                            cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
                                                            cv2.rectangle(img, (x1, y1), (x2, y2+400), (67, 255, 100), 2)
                                                else:
                                                    for x1,y1,x2,y2 in line:
                                                        text_region = img[y1 - 500:y2 , x1:x2]
                                                        box_test = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                        if(len(re.findall('against-\\n.*?,|against-\\n\\n.*?,|against-\\n\\n.*?;|-against-[\s\S]*Defendants' ,box_test))>0):
                                                            company_suid = re.findall('against-\\n.*?,|against-\\n\\n.*?,|against-\\n\\n.*?;|-against-[\s\S]*Defendants' ,box_test)[0].replace('Defendants','').strip()
                                                            if(len(re.findall('against-\\n|against-\\n\\n' ,company_suid))>0):
                                                                company_suid = company_suid.replace(re.findall('against-\\n|against-\\n\\n' ,company_suid)[0], '')
                                                        if(len(re.findall('[\s\S]*?Plaintiff' ,box_test))>0 and creadetor_name == ''):
                                                                creadetor_name = re.findall('[\s\S]*?Plaintiff' ,box_test)[0].replace('Plaintiff','').strip()

                                                        
                                                        cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
                                                        cv2.rectangle(img, (upper_x1 if upper_x1 else x1, upper_y1 if upper_y1 else y1 - 500), (x2, y2), (67, 255, 100), 2)
                                            else:
                                                pass
                                        except Exception as e:
                                            print('creadetor_name2 error'+str(e))
                                    cv2.imwrite(folder_path+ "/" + folder + '/' + "text_under_line.jpg", img)
                                    
                                    
                                    if( len(creadetor_name) == 0 ):
                                        img = convertImg(image)
                                        # threshold the grayscale image
                                        thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

                                        # use morphology erode to blur horizontally
                                        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (151, 3))
                                        morph = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)

                                        # find contours
                                        cntrs = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                        cntrs = cntrs[0] if len(cntrs) == 2 else cntrs[1]

                                        # find the topmost box
                                        ythresh = 1000000
                                        for c in cntrs:
                                            box = cv2.boundingRect(c)
                                            x,y,w,h = box
                                            if y < ythresh:
                                                topbox = box
                                                ythresh = y

                                        # Draw contours excluding the topmost box
                                        result = img.copy()
                                        x_index = 1
                                        for i,c in enumerate(cntrs):
                                            box = cv2.boundingRect(c)
                                            if box != topbox:
                                                x,y,w,h = box
                                                text_region = thresh[y:y + h, x:x + w]
                                                # enhanced_region = cv2.bitwise_not(text_region)
                                                custom_config = r'--oem 3 --psm 6'
                                                extracted_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                # cv2.imshow("GRAY", text_region)
                                                # cv2.waitKey(0)
                                                if(extracted_text == 'ne,' or extracted_text == 'nD,' or extracted_text == 'er,' or '— - X' in extracted_text or 'a , INDEX' in extracted_text or '— — XX' in extracted_text or 'asescs K INDEX N' in extracted_text or 'XxX' in extracted_text or '+--+' in extracted_text or '=== X' in extracted_text or 'eenX' in extracted_text):
                                                    try:
                                                        if x_index == 1:
                                                            # text_region = thresh[y:y + h - 90, x:x + w]
                                                            cv2.rectangle(result, (x, y), (x+w, y+h-90), (0, 0, 255), 2)
                                                            x_index = x_index +1
                                                        else:
                                                            text_region = thresh[y+15:y + h + 70, x:x + w]
                                                            creadetor_name = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                            creadetor_name = creadetor_name.replace('werewerewenecncecncecnncncrener ener eserccccccccwooe XK INDEX N','').replace('Fa nnn nnn nnn nnn INDEX N','').replace('Fa nnn nnn nnn nnn INDEX N','')
                                                            cv2.rectangle(result, (x, y+15), (x+w, y+h+70), (67, 255, 100), 2)
                                                    except Exception as e:
                                                        print('creadetor_name error'+str(e))
                                                else:
                                                    pass
                                                    # cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)

                                        # write result to disk
                                        cv2.imwrite(folder_path+ "/" + folder + '/'  + "text_above_lines_lines.jpg", result)
                                        

                                    if(len(re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text))>0) and company_suid == '':
                                        company_suid = re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text)[0]
                                        if(len(re.findall('-against-\\n|-against-\\n\\n' ,company_suid))>0):
                                            company_suid = company_suid.replace(re.findall('-against-\\n|-against-\\n\\n' ,company_suid)[0], '')

                                    if creadetor_name != '':
                                        record['creadetor_name'] = creadetor_name.replace('Return To','').replace('Document Type: SUMMONS + COMPLAINT','')
                                    if company_suid != '':
                                        record['company_suid'] = company_suid
                        except Exception as e:
                            print('error credtor '+ str(e))

                                
                                
                    if 'exhibit' in pdf_file.lower() or 'statement of authorization' in pdf_file.lower():
                        exhibit_info(pdf_path,record,folder_path,folder,pdf_file.lower())
                                    
                            
                    
                except Exception as e:
                    print('error 1'+str(e))
            print("="*100)
            print(record)
            print("="*100)
            records.append(record)
            at = airtable.Airtable('appho2OWyOBvn6PPU', 'patwsQ3w8O4VGC05S.01759369d41db17822bcf0074f5daf046cc68ef136677dd68a15550f0e843bef')
            print(record['email'] if 'email' in record else None)
            existing_lead = Lead.objects.filter(folder_id=record['folder'] if 'folder' in record else '').first()

            if existing_lead:
                # Update the existing lead record
                existing_lead.first_name = record['first_name'] if 'first_name' in record else ''
                existing_lead.last_name = record['last_name'] if 'last_name' in record else ''
                existing_lead.email = record['email'] if 'email' in record else ''
                existing_lead.phone = record['tel'] if 'tel' in record else ''
                existing_lead.creditor_name = record['creadetor_name'] if 'creadetor_name' in record else ''
                existing_lead.company_suied = record['company_suid'] if 'company_suid' in record else ''
                existing_lead.price = record['price'] if 'price' in record else ''
                existing_lead.county = record['county'] if 'county' in record else ''
                existing_lead.date = record['date'] if 'date' in record else ''
                existing_lead.business_address = record['business_address'] if 'business_address' in record else ''
                # ... Update other fields as needed ...
                existing_lead.save()
                at.update('Scrape Leads',existing_lead.airtable_id, {
                    'Page Link': record['folder'] if 'folder' in record else None,
                    'First Name': record['first_name'] if 'first_name' in record else None,
                    'Last Name': record['last_name'] if 'last_name' in record else None,
                    'phone': record['tel'] if 'tel' in record else None,
                    'email': record['email'] if 'email' in record else None,
                    'CREDITOR NAME': record['creadetor_name'] if 'creadetor_name' in record else None,
                    'COMPANY SUED': record['company_suid'] if 'company_suid' in record else None,
                    'BALANCE': record["price"] if 'price' in record else 0,
                    'BUSINESS ADDRESS': record['business_address'] if 'business_address' in record else None,
                    'COUNTY': record['county'] if 'county' in record else None,
                    'DATE': record['date'] if 'date' in record else None
                })
            else:
                id = at.create('Scrape Leads', {
                    'Page Link': record['folder'] if 'folder' in record else None,
                    'First Name': record['first_name'] if 'first_name' in record else None,
                    'Last Name': record['last_name'] if 'last_name' in record else None,
                    'phone': record['tel'] if 'tel' in record else None,
                    'email': record['email'] if 'email' in record else None,
                    'CREDITOR NAME': record['creadetor_name'] if 'creadetor_name' in record else None,
                    'COMPANY SUED': record['company_suid'] if 'company_suid' in record else None,
                    'BALANCE': record["price"] if 'price' in record else 0,
                    'BUSINESS ADDRESS': record['business_address'] if 'business_address' in record else None,
                    'COUNTY': record['county'] if 'county' in record else None,
                    'DATE': record['date'] if 'date' in record else None
                })
                Lead.objects.create(
                    first_name=record['first_name'] if 'first_name' in record else '',
                    last_name=record['last_name'] if 'last_name' in record else '',
                    email=record['email'] if 'email' in record else '',
                    phone=record['tel'] if 'tel' in record else '',
                    creditor_name=record['creadetor_name'] if 'creadetor_name' in record else '',
                    company_suied=record['company_suid'] if 'company_suid' in record else '',
                    price=record["price"] if 'price' in record else '',
                    county=record["county"] if 'county' in record else '',
                    date=record["date"] if 'date' in record else '',
                    business_address=record["business_address"] if 'business_address' in record else '',
                    folder_id=record['folder'] if 'folder' in record else '',
                    status='done',
                    airtable_id = id.get('id', None)
                )
            
            
            

def extract_folders(records):  
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(extract_texts, folder,records) for folder in [folders[4],folders[5],folders[6],folders[7]]]
        for future in futures:
            future.result()  
            
def extract_folder(request, folder):  
    folder_path='pdfs'
    decoded_folder = unquote(folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    decoded_folder = decoded_folder.replace('https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=','').replace('&display=all','')
    records = []
    extract_texts(decoded_folder,records)

    context = {'segment': 'index'}
    context['records'] = []
    leads = Lead.objects.all()
    context['records'] = leads
    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))
    
        
    
                         
def scrape(request):
    print('start')
    try:
        optionsUC = webdriver.ChromeOptions()
        optionsUC.add_argument('--window-size=360,640')
        optionsUC.add_argument('--no-sandbox')
        # optionsUC.add_argument('--headless')
        optionsUC.add_argument('start-maximized')
        count_types = ['Kings County Supreme Court', 'Monroe County Supreme Court', 'Washington County Supreme Court', 'Ontario County Supreme Court']
        # count_types = ['Kings County Supreme Court']
        try:
            current_date = datetime.utcnow()
            one_day = timedelta(days=1)
            previous_date = (current_date - one_day).strftime('%m/%d/%Y')
            today_date = current_date.strftime('%m/%d/%Y')
            driver =  webdriver.Chrome(options=optionsUC)
            context = {'segment': 'index'}
            records = []
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
                links = []
                # links = ['https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=6CzEOPZ4wBXnn82tiYqYgA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=r0E4BC2EgrZI/KN5CpzBKA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=JDTS8QN2TKPvaKBrFe58SQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=u98w6YW8UhImr_PLUS_BWEbY59A==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=/Yb7NLyBLCxABuHvyLuVEg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=LqmxxrHEReHvyLNM4l6wsg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=EsSanqJNqb327dQGHZ1O7w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=KrWeqDrAc7h8cJcqwdXA/w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=mrHNYelQiHxX8yG5rJNjFA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=kQVFljUhzsGj/_PLUS_2e5F9QoA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=IYUeRaUzMfIrKj9sMyHiNw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=jWgWo2d3zbUyStU6x0mBZw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=od6QI1QWzCt45v5kCC3MjA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=uGjn4lniMqIcwyyQetEjkg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=5jpaFKhFP1m_PLUS__PLUS_KvAiIYS8g==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Hx/G9HukBjVLV0RcBAqcmg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=JlKWZktI8XMPSJZQ4lHo8A==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=K2js6yM1U/AHB5YUh/84iQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=NtMcSBQrgMUbv5_PLUS_rXnhbNA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=NZNtrl/IjF7Z_PLUS_Lzi_PLUS_Gcqlw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=T0Tkv9Bkf8Y5UrtrtkTS6w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Hpg3KzqczIyDXgEgAKDTUA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=dURZvpqORcmDH6wLvkYLDQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=YxvdBXdxEOfew9H0u83g1w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7BgFhwmg2PtvHU3DK/tIZw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=zwNnWYEHl/ac3Ga9K_PLUS_CzoA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=4ycbbBmtMTLrEQ0nYdN3bA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=4ugv9o3JbGZr9RDHe2LKgQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=8_PLUS_IeOXp1fJA2ONwXhMYrMw==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=uDwYFiZPt1CyIL2L7H2Y1w==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=ciqunxGdMsA3QuiMeiysbQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Mn3KIbUkUIykNLxTWCEuNQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=P8EU0NCKn0tq5eRh7i5UKw==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=k2vFe_PLUS_yJKqwFcX9gzzzQIA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=K9mqj0spB4xEA6yumvLaDg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=H8bQa0OE3pE48yGRNwBbOg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=1x6EYpFnnfOl7w8m6vrKeA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=fJqfoFAV6QSY_PLUS_AGFg1_PLUS_4YA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=VW4Bl0fdy3wNvF7rB6sjmA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=rOib/bOkq3cdrwA1dejkOw==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=jpFeFB5dGGYVJR1Pa5Zb7g==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=t_PLUS_4iuCGAydUBSfHrgAcrvg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=VlDH9eyHbQncH8tbvbyLiQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=gdVLT77qfLUR5PRJG2QBCA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=tk1jTFrQ4dNZ8gZ5r0hD4Q==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=dczcJtxfBxeR_PLUS_O6PV8a9oA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=xVBfTRyk4pwkJfZ0TXMWSg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=yDtqSnAupg9Gt0qYdXr6yA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=_PLUS_zgRQlpoVnm_PLUS_DrYTlr4dbg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=dHFddSH1EhGjXwFyq0_PLUS_fNA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=OHXXDkXG0ecm50eQFJxZ8w==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=8t3OcDXHNWkxg0Aev9JTcg==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7_PLUS_94/P2tEklkdXTy5b1eCg==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Wy22M2xLmryIM6gaon_PLUS_9mw==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=_PLUS_9elz/oDYvyvNZDAquFD6A==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7xakO4BRwcIY9wW/lIk/RA==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=NBZ1a2nU_PLUS_AnnxNuTt3J9Eg==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=N_PLUS_5plvpCtoEdaqwawViOuw==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7PcFOT8qbgtVoNpLhszgJw==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=LYGAUcblTZul08Ei2ywAwA==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=AHGRF7292wnlDnXdrlyzmA==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=HFIq0sdbS8X2K4326vTgjg==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=oaZo34J3wB/1yWBfPGM7Mg==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=lNpqocMVadGvLaajX3I0gA==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1']
                for count_type in count_types:
                    try:
                        driver.get('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange')
                        sleep(5)
                        if(len(driver.find_elements(By.CSS_SELECTOR,'div.g-recaptcha'))>0):
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
                        WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH,f'//*[@id="selCountyCourt"]/option[text()="{count_type}"]')))
                        driver.find_element(By.XPATH,f'//*[@id="selCountyCourt"]/option[text()="{count_type}"]').click()
                        driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(Keys.BACKSPACE * 50)
                        driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(previous_date)
                        driver.find_element(By.CSS_SELECTOR,'input[type*="submit"]').click()
                        sleep(7)
                        driver.find_element(By.XPATH,'//*[@id="selSortBy"]/option[text()="Case Type"]').click()
                        driver.find_element(By.CSS_SELECTOR,'caption input[type*="submit"]').click()
                        sleep(6)
                        elements = driver.find_elements(By.CSS_SELECTOR, '#form > table.NewSearchResults > tbody > tr > td:nth-child(1) > a')
                        for i,e in enumerate(elements):
                            links.append(e.get_attribute('href'))
                        next_page = True
                        while(next_page):
                            next_page_elemnt = driver.find_elements(By.XPATH,'//*[@class="pageNumbers"]/a[text()=">>"]')
                            if len(next_page_elemnt)>0:
                                driver.get(next_page_elemnt[0].get_attribute('href'))
                                sleep(4)
                                elements = driver.find_elements(By.CSS_SELECTOR, '#form > table.NewSearchResults > tbody > tr > td:nth-child(1) > a')
                                for i,e in enumerate(elements):
                                    links.append(e.get_attribute('href'))
                            else:
                                next_page = False
                                        
                        # driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    except Exception as e:
                        print(e)
                
                # print(links)
                # return False
                driver.quit()
                PROCNAME = "chromedriver" # or chromedriver or IEDriverServer
                for proc in psutil.process_iter():
                    # check whether the process name matches
                    if proc.name() == PROCNAME:
                        proc.kill()
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(download_pdfs, link, records) for link in links]
                    for future in futures:
                        future.result()
            except Exception as e:
                print('-'*50)
                print(e)
            finally:
                PROCNAME = "chromedriver" # or chromedriver or IEDriverServer
                for proc in psutil.process_iter():
                    # check whether the process name matches
                    if proc.name() == PROCNAME:
                        proc.kill()
                context['records'] = records
                html_template = loader.get_template('home/index.html')
                return HttpResponse(html_template.render(context, request))
        except Exception as e:
            print('error2'+str(e))
            pass
        sleep(20)
    except Exception as e:
        print('error3'+str(e))
        pass
    
    
def getRecordsFromPhoneBurner(request):
    return HttpResponse('ok')

def convertImg(image):
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')  # Save as JPEG (or other supported format)
    img_bytes = img_bytes.getvalue()
    
    # # Decode the image bytes using OpenCV
    return cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)

def getBylocation(image):
    # Decode the image bytes using OpenCV
    img = convertImg(image)
    # choose_location(image)
    height, width, channel = img.shape
    # Resizing image if required
    img = cv2.resize(img, (width//2, height//2))

    # Convert image to grey scale
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Converting grey image to binary image by Thresholding
    threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # roi_coordinate = [[(9, 84), (486, 119)]]
    roi_coordinate = [[(100, 174), (375, 198)]]
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

    cv2.putText(img, f'{creadetor_name}', (top_left_x-25, top_left_y - 10), font, 0.5, red_color, 1)
    # cv2.imshow('img', img)
    # cv2.waitKey(0)
    return creadetor_name


def exhibit_info(pdf_path, record, folder_path, folder,pdf_file):
    tel = []
    email = []
    business_address = ''
    business_city = ''
    business_state = ''
    business_zip = ''
    first_name = ''
    last_name = ''
    date = ''
    county = ''
    try:
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            if i != -1:
                # Perform OCR on each image
                text = pytesseract.image_to_string(image, lang='eng')
                try:
                    img = convertImg(image)
                    kernel_size = 5
                    blur_gray = cv2.GaussianBlur(img,(kernel_size, kernel_size),0)
                    low_threshold = 50
                    high_threshold = 150
                    edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
                    rho = 1 
                    theta = np.pi / 180 
                    threshold = 15 
                    min_line_length = 250
                    max_line_gap = 5
                    line_image = np.copy(img) * 0
                    lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                                        min_line_length, max_line_gap)
                    for line in lines:
                        try:
                            for x1,y1,x2,y2 in line:
                                cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
                        except Exception as e:
                            print('creadetor_name2 error'+str(e))
                    img = cv2.addWeighted(img, 1, line_image, 1, 0)
                    
                    # threshold the grayscale image
                    thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

                    # use morphology erode to blur horizontally
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (151, 3))
                    morph = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)

                    # find contours
                    cntrs = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cntrs = cntrs[0] if len(cntrs) == 2 else cntrs[1]

                    # find the topmost box
                    ythresh = 1000000
                    for c in cntrs:
                        box = cv2.boundingRect(c)
                        x,y,w,h = box
                        if y < ythresh:
                            topbox = box
                            ythresh = y

                    # Draw contours excluding the topmost box
                    result = img.copy()
                    x_index = 1
                    for c in cntrs:
                        box = cv2.boundingRect(c)
                        if box != topbox:
                            x,y,w,h = box
                            text_region = thresh[y:y + h, x:x + w]
                            # enhanced_region = cv2.bitwise_not(text_region)
                            custom_config = r'--oem 3 --psm 6'
                            extracted_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                            # cv2.imshow("GRAY", text_region)
                            # cv2.waitKey(0)
                            if 'phone' in extracted_text.lower() or '| ' in extracted_text and len(re.findall('Cell Phone:[\s\S]*[0-9]{9,10}|[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\) [0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\)[0-9]{2,3}-[0-9]{2,5}',extracted_text)) > 0:
                                try:
                                    tel.append(re.findall('Cell Phone:[\s\S]*[0-9]{9,10}|[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\) [0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\)[0-9]{2,3}-[0-9]{2,5}',extracted_text)[0])
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('phone error'+str(e))

                            
                            if len(re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com|[a-zA-Z0-9._%+ -]*@[a-zA-Z0-9.-]+ com|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.net|[a-zA-Z0-9._%+ -]*@[a-zA-Z0-9.-]+ net|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9]{1,4}',extracted_text)) > 0:
                                try:
                                    email.append(re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com|[a-zA-Z0-9._%+ -]*@[a-zA-Z0-9.-]+ com|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.net|[a-zA-Z0-9._%+ -]*@[a-zA-Z0-9.-]+ net|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9]{1,4}',extracted_text)[0])
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('email error'+str(e))
                                
                            if len(re.findall('Full Name:.*|Full Name;.*|Contact Name:.*|Contact Name;.*|Owner: Name:.*',extracted_text))> 0 and first_name == '' and last_name == '':
                                try:
                                    name = re.findall('Full Name:.*|Full Name;.*|Contact Name:.*|Contact Name;.*|Owner: Name:.*',extracted_text)[0].replace('Full Name:','').replace('Full Name;','').replace('Contact Name:','').replace('Contact Name;','').replace('Owner: Name:','').strip()
                                    first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                    last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                    record['first_name'] = first_name
                                    record['last_name'] = last_name
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('full name error'+str(e))
                                    
                            if len(re.findall('First Name:.*',extracted_text)) > 0 and first_name == '':
                                try:
                                    first_name = re.findall('First Name:.*',extracted_text)[0].replace('First Name:','')
                                    record['first_name'] = first_name
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('first name error'+str(e))
                            
                            if len(re.findall('Last Name:.*',extracted_text)) > 0 and last_name == '':
                                try:
                                    last_name = re.findall('Last Name:.*',extracted_text)[0].replace('Last Name:', '')
                                    record['last_name'] = last_name
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('last name error'+str(e))
                                
                                
                            if 'OWNER/GUARANTOR #1' in extracted_text and first_name == '' and last_name == '':
                                try:
                                    text_region = thresh[y+15:y + h + 140, x:x + w]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x, y), (x+w, y+h+140), (0, 0, 255), 2)
                                    if len(re.findall('Name:.*|Name;.*',croped_text))> 0:
                                        name = re.findall('Name:.*|Name;.*',croped_text)[0].replace('Name:','').replace('Name;','').replace('By:','').strip()
                                        first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                        last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                        record['first_name'] = first_name
                                        record['last_name'] = last_name
                                except Exception as e:
                                    print('OWNER/GUARANTOR #1 error'+str(e))
                            if 'GUARANTOR\'S INFORMATION' in extracted_text and first_name == '' and last_name == '':
                                try:
                                    text_region = thresh[y+15:y + h + 140, x:x + w]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x, y), (x+w, y+h+140), (0, 0, 255), 2)
                                    if len(re.findall('| ',croped_text))> 0:
                                        name = re.findall('| ',croped_text)[0].replace('| ','').strip()
                                        first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                        last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                        record['first_name'] = first_name
                                        record['last_name'] = last_name
                                except Exception as e:
                                    print('GUARANTOR\'S INFORMATION error'+str(e))
                                    
                            if 'OWNER/GUARANTOR (#1)' in extracted_text and first_name == '' and last_name == '':
                                try:
                                    text_region = thresh[y+15:y + h + 140, x:x + w + 200]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x, y), (x+w+ 200, y+h+140), (0, 0, 255), 2)
                                    if len(re.findall('Name:.*|Name;.*|By:.*',croped_text))> 0:
                                        name = re.findall('Name:.*|Name;.*|By:.*',croped_text)[0].replace('Name:','').replace('Name;','').replace('By:','').strip()
                                        first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                        last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                        record['first_name'] = first_name
                                        record['last_name'] = last_name
                                except Exception as e:
                                    print('OWNER/GUARANTOR (#1) error'+str(e))
                                    
                            if 'Name of Owner Guarantor 1:' in extracted_text and first_name == '' and last_name == '':
                                try:
                                    text_region = thresh[y:y + h + 10, x:x + w]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).replace('Name of Owner Guarantor 1:','').strip()
                                    cv2.rectangle(result, (x, y), (x+w, y+h+10), (0, 0, 255), 2)
                                    name = croped_text.strip()
                                    first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                    last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                    record['first_name'] = first_name
                                    record['last_name'] = last_name
                                except Exception as e:
                                    print('Name of Owner Guarantor 1: error'+str(e))

                            if 'Guarantor(s) Name:' in extracted_text and first_name == '' and last_name == '':
                                try:
                                    text_region = thresh[y:y + h + 10, x:x + w]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).replace('Guarantor(s) Name:','').replace('_','').replace('—','').strip()
                                    cv2.rectangle(result, (x, y), (x+w, y+h+10), (0, 0, 255), 2)
                                    name = croped_text.strip()
                                    first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                    last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                    record['first_name'] = first_name
                                    record['last_name'] = last_name
                                except Exception as e:
                                    print('Name of Owner Guarantor Name: error'+str(e))
                                    
                            
                            if 'Phone' in extracted_text:
                                try:
                                    text_region = thresh[y-50:y + h, x:x + w+40]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x+40, y-50), (x+w, y+h), (0, 0, 255), 2)
                                    if len(re.findall('Cell Phone:[\s\S]*[0-9]{9,10}|[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\) [0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\)[0-9]{2,3}-[0-9]{2,5}',croped_text)) > 0:
                                        tel.append(re.findall('Cell Phone:[\s\S]*[0-9]{9,10}|[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\) [0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\)[0-9]{2,3}-[0-9]{2,5}',croped_text)[0])
                                    
                                except Exception as e:
                                    print('Name of Owner Guarantor Name: error'+str(e)) 
                            
                            if 'Print Name' in extracted_text and first_name == '' and last_name == '':
                                try:
                                    text_region = thresh[y-50:y + h, x-40:x + w+40]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x-40, y-50), (x+w+40, y+h), (0, 0, 255), 2)
                                    name = croped_text.replace('PrintName','').replace('Print Name','').strip().replace('()','')
                                    first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                    last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                    record['first_name'] = first_name
                                    record['last_name'] = last_name
                                except Exception as e:
                                    print('Name of Owner Guarantor Name: error'+str(e))    
                            
                            if 'Street Address' in extracted_text and business_address == '':
                                try:
                                    text_region = thresh[y-50:y + h, x:x + w+40]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x, y-50), (x+w+40, y+h), (0, 0, 255), 2)
                                    business_address = croped_text.replace('Street Address', '').replace('gS','').replace(':','').strip()
                                    record['business_address'] = business_address.replace('SAME AS ABOVE','')
                                except Exception as e:
                                    print('Street Address'+str(e))
                                    
                            if 'City, State and Zip Code' in extracted_text and business_zip == '' and business_state == '' and business_city == '':
                                try:
                                    text_region = thresh[y-50:y + h, x:x + w]
                                    croped_text = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                    cv2.rectangle(result, (x, y-50), (x+w, y+h), (0, 0, 255), 2)
                                    text = croped_text.replace('City, State and Zip Code', '').strip()
                                    business_zip = re.findall('\d+',text)[0].replace(',', '').strip() if len(re.findall('\d+',text)) > 0 else ''
                                    business_state = re.findall(',.*?\d+',text)[0].replace(business_zip, '').replace(',', '').strip() if len(re.findall(',.*?\d+',text)) > 0 else ''
                                    business_city = re.findall('.*?,',text)[0].replace(',', '').strip() if len(re.findall('.*?,',text)) > 0 else ''
                                    record['business_city'] = business_city
                                    record['business_state'] = business_state
                                    record['business_zip'] = business_zip
                                except Exception as e:
                                    print('City, State and Zip Code'+str(e))
                                    
                            if len(re.findall('Business Address:.*?:|Business street address:.*|Business Location Street Address:.*?city|Physical Address:.*|Home Address:.*|Address:.*',extracted_text)) > 0 and (business_address == '' or business_address == ', ,'):
                                try:
                                    business_address = re.findall('Business Address:.*?:|Business street address:.*|Business Location Street Address:.*?city|Physical Address:.*|Home Address:.*|Address:.*',extracted_text)[0].replace('Business Location Street Address:','').replace('Business Address:','').replace('Business street address:','').replace('city','').replace('Physical Address:','').replace('Home Address:','').replace('Address:.*','')
                                    if(len(re.findall('[a-zA-Z]+?:',business_address))>0):
                                        business_address = business_address.replace(re.findall('[a-zA-Z]+?:',business_address)[0],'')
                                    record['business_address'] = business_address.replace('SAME AS ABOVE','')
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('business address error'+str(e))
                                    
                                    
                            if len(re.findall('City/State:.*',extracted_text)) > 0 and business_city == '' and business_state == '':
                                try:
                                    city_state= re.findall('City/State:.*',extracted_text)[0].split(',')
                                    if len(city_state)>1:
                                        record['business_city'] = city_state[0]
                                        record['business_state'] = city_state[1]
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('city/state error'+str(e)) 
                                    
                                    
                            if len(re.findall('City:.*?:|Business city:.*?:|Business Location Street Address:.*?Stata|City:.*|city:.*',extracted_text)) > 0 and business_city == '':
                                try:
                                    business_city = re.findall('City:.*?:|Business city:.*?:|Business Location Street Address:.*?Stata|City:.*|city:.*',extracted_text)[0].replace('City:','').replace('Business city:','').replace('—', '').replace('city','').replace('Business Location Street Address:','').replace('Stata','').replace(business_address,'')
                                    if(len(re.findall('[a-zA-Z]+?:',business_city))>0):
                                        business_city = business_city.replace(re.findall('[a-zA-Z]+?:',business_city)[0],'')
                                    record['business_city'] = business_city
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('city error'+str(e))
                                    
                            if len(re.findall('State:.*?:|State:.*?;|Business state:.*?:|State:.*',extracted_text)) > 0 and business_state == '':
                                try:
                                    business_state = re.findall('State:.*?:|State:.*?;|Business state:.*?:|State:.*',extracted_text)[0].replace(';','').replace('State:','').replace('Business state:','').replace('_', '').replace('—', '').strip()
                                    if(len(re.findall('[a-zA-Z]+?:',business_state))>0):
                                        business_state = business_state.replace(re.findall('[a-zA-Z]+?:',business_state)[0],'')
                                    record['business_state'] = business_state
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('business state error'+str(e))
                                    
                            if len(re.findall('Zip:.*?:|Business zip:.*|Zip:.*',extracted_text)) > 0 and business_zip == '':
                                try:
                                    business_zip = re.findall('Zip:.*?:|Business zip:.*|Zip:.*',extracted_text)[0].replace('Zip:','').replace('Business zip:','').replace('—', '')
                                    if(len(re.findall('[a-zA-Z]+?:',business_zip))>0):
                                        business_zip = business_zip.replace(re.findall('[a-zA-Z]+?:',business_zip)[0],'')
                                    record['business_zip'] = business_zip
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('business zip error'+str(e))
                                    
                            if len(re.findall('[0-9]{2}/[0-9]{2}/[0-9]{4}',extracted_text)) > 0 and date == '' and ('NYSCEF' in extracted_text or 'CLERK' in extracted_text) and 'date' not in record:
                                try:
                                    date = re.findall('[0-9]{2}/[0-9]{2}/[0-9]{4}',extracted_text)[0]
                                    print(extracted_text)
                                    record['date'] = date
                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                except Exception as e:
                                    print('date error'+str(e))
                                    
                            if(len(re.findall('FILED:[\s\S]*?COUNTY',extracted_text))>0) and county == '':
                                try:
                                    county = re.findall('FILED:[\s\S]*?COUNTY',extracted_text)[0].replace('FILED:','')
                                    record['county'] = county
                                except Exception as e:
                                    print('business zip2 error'+str(e))
                                
                                
     
                    cv2.imwrite(folder_path + "/" + folder + '/'  +pdf_file+str(i)+".jpg", result)            
                    
                except Exception as e:
                    print('error in text_info'+str(e))
                    
                    
                if(len(re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text))>0) and business_zip == '':
                    try:
                        business_zip = re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text)[0].replace('Signature City, State and Zip Code','')
                        if(len(re.findall('\d+',business_zip))>0):
                            business_zip = re.findall('\d+',business_zip)[0]
                        record['business_zip'] = business_zip
                    except Exception as e:
                        print('business zip2 error'+str(e))
                        
                    
                if(len(re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text))>0) and business_city == '':
                    try:
                        business_city = re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text)[0].replace('Signature City, State and Zip Code','')
                        if(len(re.findall(',.*\d*',business_city))>0):
                            business_city = business_city.replace(re.findall(',.*\d*',business_city)[0],'')
                        record['business_city'] = business_city
                    except Exception as e:
                        print('business city2 error'+str(e))
                    
                if(len(re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text))>0) and business_state == '':
                    try:
                        business_state = re.findall(' [a-zA-Z]+?,.*?\d*\\nSignature City, State and Zip Code',text)[0].replace('Signature City, State and Zip Code','')
                        if(len(re.findall('.*,',business_state))>0):
                            business_state = business_state.replace(re.findall('.*,',business_state)[0],'')
                        if(len(re.findall('\d+',business_state))>0):
                            business_state = business_state.replace(re.findall('\d+',business_state)[0],'')
                        record['business_state'] = business_state
                    except Exception as e:
                        print('business state2 error'+str(e))
    except Exception as e:
        print('error in text'+str(e))
        
    if(',' not in business_address and business_address != ''):
        record['business_address'] = business_address + (', ' + business_city if business_city else '') + (', ' + business_state if business_state else '') + ' '+ business_zip  
    

    for t in tel:
        if 'Cell Phone' in t:
            record['tel'] = t.replace('Cell Phone','').replace(':','')  
    if 'tel' not in record and len(tel)>0:
        record['tel'] = tel[0]
        
    try:
        print(os.getcwd().replace('scraping','')+'/' + pdf_path)
        doc = fitz.open(os.getcwd().replace('scraping','')+'/' + pdf_path)
        page = doc.load_page(0)
        page_text = page.get_text("text")
        [email.append(word) for word in page_text.split() if len(re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com|[a-zA-Z0-9._%+ -]*@[a-zA-Z0-9.-]+ com|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.net|[a-zA-Z0-9._%+ -]*@[a-zA-Z0-9.-]+ net',word))>0]
        doc.close()
    except Exception as e:
        print('email pdf error'+str(e))
        
    print(email)
    
    if 'email' not in record and len(email)>1:
        record['email'] = email[len(email)-1].strip()
    if 'email' not in record and len(email)>0:
        record['email'] = email[0].strip()
        
        
        
def run_cron(request):
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
            
                    
def scrape_cron():
    print('start')
    try:
        optionsUC = webdriver.ChromeOptions()
        optionsUC.add_argument('--window-size=360,640')
        optionsUC.add_argument('--no-sandbox')
        # optionsUC.add_argument('--headless')
        optionsUC.add_argument('start-maximized')
        count_types = ['Kings County Supreme Court', 'Monroe County Supreme Court', 'Washington County Supreme Court', 'Ontario County Supreme Court']
        # count_types = ['Kings County Supreme Court']
        try:
            current_date = datetime.utcnow()
            one_day = timedelta(days=1)
            previous_date = (current_date - one_day).strftime('%m/%d/%Y')
            today_date = current_date.strftime('%m/%d/%Y')
            driver =  webdriver.Chrome(options=optionsUC)
            context = {'segment': 'index'}
            records = []
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
                links = []
                # links = ['https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=6CzEOPZ4wBXnn82tiYqYgA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=r0E4BC2EgrZI/KN5CpzBKA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=JDTS8QN2TKPvaKBrFe58SQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=u98w6YW8UhImr_PLUS_BWEbY59A==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=/Yb7NLyBLCxABuHvyLuVEg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=LqmxxrHEReHvyLNM4l6wsg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=EsSanqJNqb327dQGHZ1O7w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=KrWeqDrAc7h8cJcqwdXA/w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=mrHNYelQiHxX8yG5rJNjFA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=kQVFljUhzsGj/_PLUS_2e5F9QoA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=IYUeRaUzMfIrKj9sMyHiNw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=jWgWo2d3zbUyStU6x0mBZw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=od6QI1QWzCt45v5kCC3MjA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=uGjn4lniMqIcwyyQetEjkg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=5jpaFKhFP1m_PLUS__PLUS_KvAiIYS8g==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Hx/G9HukBjVLV0RcBAqcmg==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=JlKWZktI8XMPSJZQ4lHo8A==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=K2js6yM1U/AHB5YUh/84iQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=NtMcSBQrgMUbv5_PLUS_rXnhbNA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=NZNtrl/IjF7Z_PLUS_Lzi_PLUS_Gcqlw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=T0Tkv9Bkf8Y5UrtrtkTS6w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Hpg3KzqczIyDXgEgAKDTUA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=dURZvpqORcmDH6wLvkYLDQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=YxvdBXdxEOfew9H0u83g1w==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7BgFhwmg2PtvHU3DK/tIZw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=zwNnWYEHl/ac3Ga9K_PLUS_CzoA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=4ycbbBmtMTLrEQ0nYdN3bA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=4ugv9o3JbGZr9RDHe2LKgQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=8_PLUS_IeOXp1fJA2ONwXhMYrMw==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=uDwYFiZPt1CyIL2L7H2Y1w==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=ciqunxGdMsA3QuiMeiysbQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Mn3KIbUkUIykNLxTWCEuNQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=P8EU0NCKn0tq5eRh7i5UKw==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=k2vFe_PLUS_yJKqwFcX9gzzzQIA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=K9mqj0spB4xEA6yumvLaDg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=H8bQa0OE3pE48yGRNwBbOg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=1x6EYpFnnfOl7w8m6vrKeA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=fJqfoFAV6QSY_PLUS_AGFg1_PLUS_4YA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=VW4Bl0fdy3wNvF7rB6sjmA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=rOib/bOkq3cdrwA1dejkOw==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=jpFeFB5dGGYVJR1Pa5Zb7g==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=t_PLUS_4iuCGAydUBSfHrgAcrvg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=VlDH9eyHbQncH8tbvbyLiQ==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=gdVLT77qfLUR5PRJG2QBCA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=tk1jTFrQ4dNZ8gZ5r0hD4Q==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=dczcJtxfBxeR_PLUS_O6PV8a9oA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=xVBfTRyk4pwkJfZ0TXMWSg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=yDtqSnAupg9Gt0qYdXr6yA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=_PLUS_zgRQlpoVnm_PLUS_DrYTlr4dbg==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=dHFddSH1EhGjXwFyq0_PLUS_fNA==&display=all&courtType=Monroe%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=OHXXDkXG0ecm50eQFJxZ8w==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=8t3OcDXHNWkxg0Aev9JTcg==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7_PLUS_94/P2tEklkdXTy5b1eCg==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=Wy22M2xLmryIM6gaon_PLUS_9mw==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=_PLUS_9elz/oDYvyvNZDAquFD6A==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7xakO4BRwcIY9wW/lIk/RA==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=NBZ1a2nU_PLUS_AnnxNuTt3J9Eg==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=N_PLUS_5plvpCtoEdaqwawViOuw==&display=all&courtType=Washington%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=7PcFOT8qbgtVoNpLhszgJw==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=LYGAUcblTZul08Ei2ywAwA==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=AHGRF7292wnlDnXdrlyzmA==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=HFIq0sdbS8X2K4326vTgjg==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=oaZo34J3wB/1yWBfPGM7Mg==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=lNpqocMVadGvLaajX3I0gA==&display=all&courtType=Ontario%20County%20Supreme%20Court&resultsPageNum=1']
                for count_type in count_types:
                    try:
                        driver.get('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange')
                        sleep(5)
                        if(len(driver.find_elements(By.CSS_SELECTOR,'div.g-recaptcha'))>0):
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
                        WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH,f'//*[@id="selCountyCourt"]/option[text()="{count_type}"]')))
                        driver.find_element(By.XPATH,f'//*[@id="selCountyCourt"]/option[text()="{count_type}"]').click()
                        driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(Keys.BACKSPACE * 50)
                        driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(previous_date)
                        driver.find_element(By.CSS_SELECTOR,'input[type*="submit"]').click()
                        sleep(7)
                        driver.find_element(By.XPATH,'//*[@id="selSortBy"]/option[text()="Case Type"]').click()
                        driver.find_element(By.CSS_SELECTOR,'caption input[type*="submit"]').click()
                        sleep(6)
                        elements = driver.find_elements(By.CSS_SELECTOR, '#form > table.NewSearchResults > tbody > tr > td:nth-child(1) > a')
                        for i,e in enumerate(elements):
                            links.append(e.get_attribute('href'))
                                        
                        # driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    except Exception as e:
                        print(e)
                
                # print(links)
                # return False
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(download_pdfs, link, records) for link in links]
                    for future in futures:
                        future.result()
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
                
                # extract_folders(records)
                    

                context['records'] = records
                html_template = loader.get_template('home/index.html')
                return HttpResponse(html_template.render(context, request))
        except Exception as e:
            print('error2'+str(e))
            pass
        sleep(20)
    except Exception as e:
        print('error3'+str(e))
        pass