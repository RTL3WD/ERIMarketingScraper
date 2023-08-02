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
import asyncio
import requests
from PIL import Image
import io
import cv2
import numpy as np
import random


net = cv2.dnn.readNet("yolov2.weights", "yolov2.cfg")
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
foundObjects = []
def detect_objects(image, i, detect):
    global foundObjects
    # Get the image's height and width
    height, width = image.shape[:2]

    # Preprocess the image for YOLO
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)

    # Set the input to the YOLO network
    net.setInput(blob)

    # Get the output layer names
    output_layer_names = net.getUnconnectedOutLayersNames()

    # Run the forward pass to get the detections
    detections = net.forward(output_layer_names)

    # Process the detections
    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # You can adjust the confidence threshold as needed
                # Object detected, do something with the result
                class_name = classes[class_id]
                if(str(class_name).lower() in str(detect).lower() or str(detect).lower() in str(class_name).lower()):
                    foundObjects.append(i)
                    print(f"Detected {class_name} with confidence {confidence} at {i}")
                    
def detect_big_objects(image, detect):
    # Get the image's height and width
    height, width = image.shape[:2]
    # Preprocess the image for YOLO
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    # Set the input to the YOLO network
    net.setInput(blob)
    # Get the output layer names
    output_layer_names = net.getUnconnectedOutLayersNames()
    # Run the forward pass to get the detections
    detections = net.forward(output_layer_names)
    # Process the detections
    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # You can adjust the confidence threshold as needed
                # Object detected, do something with the result
                class_name = classes[class_id]
                if (str(class_name).lower() in str(detect).lower() or str(detect).lower() in str(class_name).lower()):
                    print(f"Detected {class_name} with confidence {confidence} in the image")
                    box = obj[0:4] * np.array([width, height, width, height])
                    (centerX, centerY, box_width, box_height) = box.astype("int")
                    rectangle_width = int(box_width * 0.5)
                    rectangle_height = int(box_height * 0.5)
                    x = int(centerX - (rectangle_width / 2))
                    y = int(centerY - (rectangle_height / 2))
                    x2 = x + rectangle_width
                    y2 = y + rectangle_height
                    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    gray_image_bgr = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
                    image_with_rect = cv2.rectangle(gray_image_bgr.copy(), (x, y), (x2, y2), (0, 255, 0), cv2.FILLED)
    
                    return image_with_rect

def split_image_from_url_to_4x4(url,type):
    # Download the image from the URL
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download the image from the URL. Status code: {response.status_code}")

    # Open the image using PIL
    image = Image.open(io.BytesIO(response.content))

    # Get the dimensions of the original image
    width, height = image.size

    # Calculate the width and height of each sub-image (tile)
    
    tile_width = width // type
    tile_height = height // type

    # Create a list to store the cropped tiles
    tiles = []

    # Split the image into a 4x4 grid and crop each tile
    for row in range(type):
        for col in range(type):
            left = col * tile_width
            upper = row * tile_height
            right = left + tile_width
            lower = upper + tile_height

            # Crop the tile
            tile = image.crop((left, upper, right, lower))
            tiles.append(tile)

    return tiles

def split_image_from_image_to_4x4(image, type):
    print(image)
    # Get the dimensions of the original image
    width, height = image.size
    # Calculate the width and height of each sub-image (tile)
    
    tile_width = width // type
    tile_height = height // type
    # Create a list to store the cropped tiles
    tiles = []
    # Split the image into a 4x4 grid and crop each tile
    for row in range(type):
        for col in range(type):
            left = col * tile_width
            upper = row * tile_height
            right = left + tile_width
            lower = upper + tile_height
            # Crop the tile
            tile = image.crop((left, upper, right, lower))
            tiles.append(tile)

    return tiles


def has_green_color(image):
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for the green color in HSV
    lower_green = (40, 40, 40)
    upper_green = (80, 255, 255)

    # Create a mask using inRange to detect green color in the image
    mask = cv2.inRange(hsv_image, lower_green, upper_green)

    # Count the number of non-zero pixels in the mask (green pixels)
    green_pixels = cv2.countNonZero(mask)

    # If there are green pixels, return True, otherwise return False
    return green_pixels > 0



def main():
    global foundObjects
    optionsUC = webdriver.ChromeOptions()
    optionsUC.add_argument('--window-size=360,640')
    optionsUC.add_argument('--no-sandbox')
    try:
        driver =  webdriver.Chrome(options=optionsUC)
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
            driver.get('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange')
            iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[title*="reCAPTCHA"]')
            driver.switch_to.frame(iframe)
            driver.find_element(By.CSS_SELECTOR, 'span.recaptcha-checkbox').click()
            sleep(5)
            undetected = True
            while(undetected):
                print('start')
                driver.switch_to.default_content()
                imageIframe = driver.find_element(By.CSS_SELECTOR, 'iframe[title*="recaptcha challenge expires in two minutes"]')
                driver.switch_to.frame(imageIframe)
                sleep(3)
                imageSize = driver.find_elements(By.CSS_SELECTOR, 'table > tbody > tr:nth-child(1) > td.rc-imageselect-tile')
                sleep(2)
                images = driver.find_elements(By.CSS_SELECTOR, 'table > tbody > tr > td.rc-imageselect-tile')
                detect = driver.find_element(By.CSS_SELECTOR, 'strong').text
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="rc-imageselect-desc"] > span')))
                typeOfRecaptcha = driver.find_element(By.CSS_SELECTOR, 'div[class*="rc-imageselect-desc"] > span').text
                image_url = images[0].find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                found = False
                for clas in classes:
                    if (str(clas).lower() in str(detect).lower() or str(detect).lower() in str(clas).lower()):
                        found = True 
                if(len(imageSize) == 3 and found):
                    tiles = split_image_from_url_to_4x4(image_url, len(imageSize))
                    for i, tile in enumerate(tiles):
                        image_np = np.array(tile)
                        tile.save(f"recaptcha_images/tile_{i}.png")
                        detect_objects(image_np, i, detect)
                    for index in foundObjects:
                        print(index)
                        images[index].click()
                        sleep(random.randint(1, 4))
                    
                    if('none left' not in typeOfRecaptcha):
                        driver.find_element(By.CSS_SELECTOR, 'button#recaptcha-verify-button').click()
                    else:
                        if(len(tiles)==0):
                            driver.find_element(By.CSS_SELECTOR, 'button#recaptcha-verify-button').click()
                    sleep(10)
                    tiles = []
                    foundObjects = []
                    mainPage = driver.find_elements(By.XPATH,'//*[@id="selCountyCourt"]/option[text()="Albany County Supreme Court"]')
                    if(len(mainPage)>0):
                        undetected = False
                elif(len(imageSize) == 4 and found):
                    response = requests.get(image_url)
                    if response.status_code != 200:
                        raise Exception(f"Failed to download the image from the URL. Status code: {response.status_code}")
                    # Open the image using PIL
                    image = Image.open(io.BytesIO(response.content))
                    image_np = np.array(image)
                    image_with_rect_local = detect_big_objects(image_np, detect)
                    cv2.imwrite(f"colored_image.png", image_with_rect_local)
                    colored_image = Image.open("colored_image.png")
                    tiles = split_image_from_image_to_4x4(colored_image, len(imageSize))
                    tiles_with_green_color = []
                    for i, tile in enumerate(tiles):
                        if has_green_color(np.array(tile)):
                            images[i].click()
                            tiles_with_green_color.append(i)
                            sleep(random.randint(1, 4))
                        tile.save(f"recaptcha_images/tile_{i}.png")
                    driver.find_element(By.CSS_SELECTOR, 'button#recaptcha-verify-button').click()
                    sleep(10)
                    mainPage = driver.find_elements(By.XPATH,'//*[@id="selCountyCourt"]/option[text()="Albany County Supreme Court"]')
                    if(len(mainPage)>0):
                        undetected = False
                    print("Tiles with green color:", tiles_with_green_color)

                else:
                    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.rc-button-reload'))).click()
                    sleep(5)
            # image = 
            


            

        except Exception as e:
            print(e)
    except Exception as e:
            print(e)
            
            
main()