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
        count_types = ['Kings County Supreme Court', 'Monroe County Supreme Court', 'Washington County Supreme Court', 'Ontario County Supreme Court']
        # count_types = ['Kings County Supreme Court']
        try:
            current_date = datetime.utcnow()
            one_day = timedelta(days=1)
            previous_date = (current_date - one_day).strftime('%m/%d/%Y')
            driver =  webdriver.Chrome(options=optionsUC)
            try:
                # hrefss = ['https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=6EX0TNNc0QnNa/CDGn0xCQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1','https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=sQFus2Np8nx1hj/YMI1IhA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=5','https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=xkrTPvUbcKSHTkheuDWkFA==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1','https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=b2tHRQg10udHQWOYfudvtQ==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1','https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=MzOiX75SO4ZjdZss/uPRUw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=3','https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=HPCQuFE9n9yQ5m7VXwzGSw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1','https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=FTuCmnOXNu4nPJ7rvoAiig==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=qiDJalt0vbDTfXP7pdZZLw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=FktbgjuFTBVcsejt0E_PLUS_pnw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=RVPU28ulkrScAxnUoEopqw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1', 'https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId=_PLUS_SyXPcSo0/R5Z4eBk4SFEw==&display=all&courtType=Kings%20County%20Supreme%20Court&resultsPageNum=1']
                # for href in [hrefss[0],hrefss[1],hrefss[2],hrefss[3]]:
                #     elemntDriver = Chrome()
                #     elemntDriver.get(href)
                #     docs = elemntDriver.find_elements(By.CSS_SELECTOR, 'table.NewSearchResults > tbody > tr > td:nth-child(2) > a')
                #     contentName= elemntDriver.find_element(By.CSS_SELECTOR, '#row').get_attribute('value').strip()
                #     hrefs = []
                    
                #     for doc in docs:
                #         hrefs.append({'href': doc.get_attribute('href'), 'name': doc.get_attribute('innerHTML').strip(),'contentName': contentName})
                    
                #     ActionChains(elemntDriver).key_down(Keys.CONTROL).send_keys("t").key_up(Keys.CONTROL).perform()
                #     elemntDriver.execute_script('''window.open("http://bings.com","_blank");''')
                #     sleep(5)
                #     elemntDriver.switch_to.window(elemntDriver.window_handles[1])
                    
                #     for href in hrefs:
                #         print(href)
                #         try:
                #             elemntDriver.get(href['href'])
                #             download_file(href)
                #             sleep(5)
                #         except Exception as e:
                #             print(e)
                #         sleep(5)
                #     elemntDriver.quit()
                #     sleep(3)    

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
                        for i,e in enumerate([elements[3],elements[4],elements[5],elements[6],elements[7]]):
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
                        print(e)
                
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
                    if folder != 'b2tHRQg10udHQWOYfudvtQ==':
                        for pdf_file in files:
                            try:
                                tel = ''
                                email = ''
                                business_name = ''
                                business_address = ''
                                business_city = ''
                                business_state = ''
                                business_zip = ''
                                contact_address = ''
                                contact_city = ''
                                contact_state = ''
                                contact_zip = ''
                                first_name = ''
                                last_name = ''
                                pdf_path = os.path.join(folder_path + '/' + folder, pdf_file)
                                # Convert PDF to images
                                images = convert_from_path(pdf_path)
                                
                                if 'summons' in pdf_file.lower() or 'petition' in pdf_file.lower():
                                    try:
                                        for i, image in enumerate([images[0],images[1],images[2]]):
                                            if i == 0:
                                                #(left, upper, right, lower)
                                                cropped_image = image.crop((1, 100, 1000, 1000))
                                                text = pytesseract.image_to_string(cropped_image, lang='eng')
                                                creadetor_name = ''
                                                company_suid = ''
                                                officers_comany = ''
                                                creadetor_name_elments = [e for e in re.findall('wenn eee x\\n.*?,||wenn eee x\\n\\n.*?,|ee ee ee XxX\\n.*?\\n' ,text) if len(e) > 0]
                                                if(len(creadetor_name_elments)>0):
                                                    creadetor_name = creadetor_name_elments[0].replace('\\n','').replace('wenn eee x', '').replace('ee ee ee XxX', '')
                                                    if(',' in creadetor_name[len(creadetor_name)-1]):
                                                        creadetor_name = creadetor_name.replace(',','')
                                                else:
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
                                                                if x_index == 1:
                                                                    # text_region = thresh[y:y + h - 90, x:x + w]
                                                                    # officers_comany = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h-90), (0, 0, 255), 2)
                                                                    x_index = x_index +1
                                                                else:
                                                                    text_region = thresh[y+15:y + h + 70, x:x + w]
                                                                    creadetor_name = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                                    creadetor_name = creadetor_name.replace('werewerewenecncecncecnncncrener ener eserccccccccwooe XK INDEX N','').replace('Fa nnn nnn nnn nnn INDEX N','').replace('Fa nnn nnn nnn nnn INDEX N','')
                                                                    cv2.rectangle(result, (x, y+15), (x+w, y+h+70), (67, 255, 100), 2)
                                                            else:
                                                                pass
                                                                # cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)

                                                    # write result to disk
                                                    cv2.imwrite("text_above_lines_lines.jpg", result)

                                                    #cv2.imshow("GRAY", gray)
                                                    # cv2.imshow("RESULT", result)
                                                    # cv2.waitKey(0)
                                                    # cv2.destroyAllWindows()
                                                    

                                                
                                                if( len(creadetor_name) == 0 ):
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

                                                    for i,line in enumerate(lines):
                                                        if i == 0:
                                                            for x1,y1,x2,y2 in line:
                                                                text_region = img[y1:y2 + 70, x1:x2]
                                                                creadetor_name = pytesseract.image_to_string(text_region, config=custom_config).strip()
                                                                cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
                                                                cv2.rectangle(img, (x1, y1), (x2, y2+70), (67, 255, 100), 2)
                                                        else:
                                                            cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
                                                            cv2.rectangle(img, (x1, y1), (x2, y2+70), (67, 255, 100), 2)
                                                    cv2.imwrite("text_under_line.jpg", img)

                                                if(len(re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text))>0):
                                                    company_suid = re.findall('-against-\\n.*?,|-against-\\n\\n.*?,|-against-\\n\\n.*?;' ,text)[0]
                                                    if(len(re.findall('-against-\\n|-against-\\n\\n' ,company_suid))>0):
                                                        company_suid = company_suid.replace(re.findall('-against-\\n|-against-\\n\\n' ,company_suid)[0], '')

                                                if(len(re.findall('Defendants\\n.*?,|Defendants\\n\\n.*?,|Defendants\\n\\n.*?;' ,text))>0):
                                                    officers_comany = re.findall('Defendants\\n.*?,|Defendants\\n\\n.*?,|Defendants\\n\\n.*?;' ,text)[0]
                                                    if(len(re.findall('Defendants\\n|Defendants\\n\\n' ,officers_comany))>0):
                                                        officers_comany = officers_comany.replace(re.findall('Defendants\\n|Defendants\\n\\n' ,officers_comany)[0], '')

                                                    
                                                record['creadetor_name'] = creadetor_name
                                                record['company_suid'] = company_suid
                                                record['officers_comany'] = officers_comany
                                    except Exception as e:
                                        print(e)

                                            
                                            
                                if 'exhibit' in pdf_file.lower() or 'statement of authorization' in pdf_file.lower():
                                    try:
                                        for i, image in enumerate([images[0],images[1],images[2]]):
                                            if i == 0 or i == 1:
                                                # Perform OCR on each image
                                                text = pytesseract.image_to_string(image, lang='eng')
                                                try:
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
                                                            if len(re.findall('[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\) [0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\)[0-9]{2,3}-[0-9]{2,5}',extracted_text)) > 0 and tel == '':
                                                                try:
                                                                    tel = re.findall('[0-9]{2,3}-[0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\) [0-9]{2,3}-[0-9]{2,5}|\([0-9]{2,3}\)[0-9]{2,3}-[0-9]{2,5}',extracted_text)[0]
                                                                    record['tel'] = tel
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('phone error'+str(e))
                                                            
                                                            if len(re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',extracted_text)) > 0 and email == '':
                                                                try:
                                                                    email = re.findall('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',extracted_text)[0]
                                                                    record['email'] = email
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('email error'+str(e))
                                                            
                                                            if len(re.findall('Full Name:.*|Full Name;.*',extracted_text))> 0 and first_name == '' and last_name == '':
                                                                try:
                                                                    name = re.findall('Full Name:.*|Full Name;.*',extracted_text)[0].strip().replace('Full Name:','').replace('Full Name;','')
                                                                    first_name = name.split(' ')[0] if len(name.split(' ')) > 0 else ''
                                                                    last_name = (name.split(' ')[1] if len(name.split(' ')) > 1 else '')+(name.split(' ')[2] if len(name.split(' ')) > 2 else '')
                                                                    record['first_name'] = first_name
                                                                    record['last_name'] = last_name
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h+140), (0, 0, 255), 2)
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
                                                                        print('='*100)
                                                                        print(croped_text)
                                                                        print(name)
                                                                        print('='*100)
                                                                except Exception as e:
                                                                    print('OWNER/GUARANTOR (#1) error'+str(e))
                                                                
                                                                    
                                                            if len(re.findall('Legal Name:.*',extracted_text)) > 0 and business_name == '':
                                                                try:
                                                                    business_name = re.findall('Legal Name:.*',extracted_text)[0].replace('Legal Name:','')
                                                                    if(len(re.findall('[a-zA-Z]+?:',business_name))>0):
                                                                        business_name = business_name.replace(re.findall('[a-zA-Z]+?:',business_name)[0],'')
                                                                    record['business_name'] = business_name
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('legal name error'+str(e))
                                                                
                                                                
                                                            if len(re.findall('Business Address:.*?:|Business street address:.*|Business Location Street Address:.*?city|Physical Address:.*',extracted_text)) > 0 and business_address == '':
                                                                try:
                                                                    business_address = re.findall('Business Address:.*?:|Business street address:.*|Business Location Street Address:.*?city|Physical Address:.*',extracted_text)[0].replace('Business Location Street Address:','').replace('Business Address:','').replace('Business street address:','').replace('city','').replace('Physical Address:','')
                                                                    if(len(re.findall('[a-zA-Z]+?:',business_address))>0):
                                                                        business_address = business_address.replace(re.findall('[a-zA-Z]+?:',business_address)[0],'')
                                                                    record['business_address'] = business_address
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('business address error'+str(e))
                                                                
                                                            if len(re.findall('City:.*?:|Business city:.*?:|Business Location Street Address:.*?Stata',extracted_text)) > 0 and business_city == '':
                                                                try:
                                                                    business_city = re.findall('City:.*?:|Business city:.*?:|Business Location Street Address:.*?Stata',extracted_text)[0].replace('City:','').replace('Business city:','').replace('—', '').replace('city','').replace('Business Location Street Address:','').replace('Stata','').replace(business_address,'')
                                                                    if(len(re.findall('[a-zA-Z]+?:',business_city))>0):
                                                                        business_city = business_city.replace(re.findall('[a-zA-Z]+?:',business_city)[0],'')
                                                                    record['business_city'] = business_city
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('city error'+str(e))
                                                                    
                                                            if len(re.findall('State:.*?:|Business state:.*?:',extracted_text)) > 0 and business_state == '':
                                                                try:
                                                                    business_state = re.findall('State:.*?:|Business state:.*?:',extracted_text)[0].replace('State:','').replace('Business state:','').replace('—', '')
                                                                    if(len(re.findall('[a-zA-Z]+?:',business_state))>0):
                                                                        business_state = business_state.replace(re.findall('[a-zA-Z]+?:',business_state)[0],'')
                                                                    record['business_state'] = business_state
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('business state error'+str(e))
                                                                    
                                                            if len(re.findall('Zip:.*?:|Business zip:.*',extracted_text)) > 0 and business_zip == '':
                                                                try:
                                                                    business_zip = re.findall('Zip:.*?:|Business zip:.*',extracted_text)[0].replace('Zip:','').replace('Business zip:','').replace('—', '')
                                                                    if(len(re.findall('[a-zA-Z]+?:',business_zip))>0):
                                                                        business_zip = business_zip.replace(re.findall('[a-zA-Z]+?:',business_zip)[0],'')
                                                                    record['business_zip'] = business_zip
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('business zip error'+str(e))
                                                                
                                                            if(',' not in business_address):
                                                                business_address = business_address + ', ' + business_city + ', ' + business_state + ' '+ business_zip
                                                            
                                                            
                                                            if len(re.findall('Contact Address:.*?:|Contact street address:.*',extracted_text)) > 0 and contact_address == '':
                                                                try:
                                                                    contact_address = re.findall('Contact Address:.*?:|Contact street address:.*',extracted_text)[0].replace('Contact Address:','').replace('Contact street address:','').replace('—', '')
                                                                    if(len(re.findall('[a-zA-Z]+?:',contact_address))>0):
                                                                        contact_address = contact_address.replace(re.findall('[a-zA-Z]+?:',contact_address)[0],'')
                                                                    record['contact_address'] = contact_address
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('contact address error'+str(e))
                                                                
                                                            if len(re.findall('City:.*?:|Contact city:.*?:',extracted_text)) > 0 and contact_city == '':
                                                                try:
                                                                    contact_city = re.findall('City:.*?:|Contact city:.*?:',extracted_text)[0].replace('City:','').replace('Contact city:','').replace('—', '')
                                                                    if(len(re.findall('[a-zA-Z]+?:',contact_city))>0):
                                                                        contact_city = contact_city.replace(re.findall('[a-zA-Z]+?:',contact_city)[0],'')
                                                                    record['contact_city'] = contact_city
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('contact city error'+str(e))
                                                                    
                                                            if len(re.findall('State:.*?:|Contact state:.*?:',extracted_text)) > 0 and contact_state == '':
                                                                try:
                                                                    contact_state = re.findall('State:.*?:|Contact state:.*?:',extracted_text)[0].replace('State:','').replace('Contact state:','').replace('—', '')
                                                                    if(len(re.findall('[a-zA-Z]+?:',contact_state))>0):
                                                                        contact_state = contact_state.replace(re.findall('[a-zA-Z]+?:',contact_state)[0],'')
                                                                    record['contact_state'] = contact_state
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('contact state error'+str(e))
                                                                    
                                                            if len(re.findall('Zip:.*?:|Contact zip:.*?',extracted_text)) > 0 and contact_zip == '':
                                                                try:
                                                                    contact_zip = re.findall('Zip:.*?:|Contact zip:.*?',extracted_text)[0].replace('Zip:','').replace('Contact zip:','').replace('—', '')
                                                                    if(len(re.findall('[a-zA-Z]+?:',contact_zip))>0):
                                                                        contact_zip = contact_zip.replace(re.findall('[a-zA-Z]+?:',contact_zip)[0],'')
                                                                    record['contact_zip'] = contact_zip
                                                                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                                                except Exception as e:
                                                                    print('contact zip error'+str(e))
                                                                    
                                                            if(',' not in contact_address):
                                                                contact_address = contact_address + ', ' + contact_city + ', ' + contact_state + ' '+ contact_zip
                                                            else:
                                                                pass
                                                                
                                                    if i ==0:            
                                                        cv2.imwrite("text_info0.jpg", result)
                                                    if i ==1:            
                                                        cv2.imwrite("text_info1.jpg", result)
                                                except Exception as e:
                                                    print(e)
                                                    
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
                                        print(e)
                                                
                                        
                                if 'complaint' in pdf_file.lower():
                                    numbers = []
                                    try:
                                        for i, image in enumerate([images[0],images[1],images[2]]):
                                            text = pytesseract.image_to_string(image, lang='eng')
                                            for info in re.findall('.*\\n' ,text):
                                                for number in re.findall('\$\d+,\d+\.\d+|\$\d+,\d+|\$\d+',info):
                                                    number = number.replace('$','').replace(',','')
                                                    numbers.append(float(number))
                                        price = max(numbers)
                                        record['price'] = price
                                    except Exception as e:
                                        print('complaint error'+str(e))
                            except Exception as e:
                                print(e)
                            
                    records.append(record)
                            

                for record in records:
                    print('-'*50)
                    try:
                        at = airtable.Airtable('appho2OWyOBvn6PPU', 'patwsQ3w8O4VGC05S.01759369d41db17822bcf0074f5daf046cc68ef136677dd68a15550f0e843bef')
                        print(record['email'] if 'email' in record else None)
                        at.create('Scrape Leads', {
                            'First Name': record['first_name'] if 'first_name' in record else None,
                            'Last Name': record['last_name'] if 'last_name' in record else None,
                            'phone': record['tel'] if 'tel' in record else None,
                            'email': record['email'] if 'email' in record else None,
                            'BUSINESS NAME': record['business_name'] if 'business_name' in record else None,
                            'CREDITOR NAME': record['creadetor_name'] if 'creadetor_name' in record else None,
                            'COMPANY SUID': record['company_suid'] if 'company_suid' in record else None,
                            'OFFICERS COMANY': record['company_suid'] if 'company_suid' in record else None,
                            'BALANCE': record["price"] if 'price' in record else 0,
                            'BUSINESS ADDRESS': record['business_address'] if 'business_address' in record else None,
                            'CONTACT ADDRESS': record['contact_address'] if 'contact_address' in record else None
                        })
                    except Exception as e:
                        print(e)

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