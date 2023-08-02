from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from selenium_recaptcha_solver import RecaptchaSolver
from selenium.webdriver.chrome.service import Service
import threading
from selenium.webdriver.common.proxy import Proxy, ProxyType
import undetected_chromedriver as uc

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
    


def main():
    test_ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/60.0.3112.50 Safari/537.36'
    # service = Service(executable_path='./chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=360,640')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(f'--user-agent={test_ua}')
    options.add_argument("--disable-blink-features=AutomationControlled") 
    # options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    # options.add_experimental_option("useAutomationExtension", False) 
    try:
        # chromeDriver = webdriver.Chrome(service=service, options=options)
        chromeDriver = uc.Chrome(options=options)
        chromeDriver.get('https://free-proxy-list.net/')
        proxies = []
        
        for i in chromeDriver.find_elements(By.CSS_SELECTOR, '#list tbody tr'):
            proxy_host = i.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.strip()
            proxy_port = i.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.strip()
            proxies.append(f'{proxy_host}:{proxy_port}')
        
        chromeDriver.quit()
        print(len(proxies))
        user_agent_list = [ 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36', 
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15', 
        ] 
        for proxie in proxies:
            for agent in user_agent_list:
                optionsUC = webdriver.ChromeOptions()
                service = Service(executable_path='./chromedriver.exe')
                print('+'*50)
                print(f'{proxie}')
                proxy = Proxy()
                proxy.proxy_type = ProxyType.MANUAL
                proxy.http_proxy = f'{proxie}'
                proxy.ssl_proxy = f'{proxie}'
                optionsUC.add_argument('--window-size=360,640')
                optionsUC.add_argument(f"--proxy-server={proxie}")
                optionsUC.add_argument(f'--user-agent={agent}')
                # driver = webdriver.Chrome(service=service, options=options)
                try:
                    driver = uc.Chrome(service=service, options=optionsUC)
                    try:
                        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
                        solver = RecaptchaSolver(driver=driver)
                        # driver.get('https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=courtDateRange')
                        driver.get('https://iapps.courts.state.ny.us/')
                        sleep(5)
                        recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
                        click_recaptcha_with_timeout(solver, recaptcha_iframe)
                        # driver.find_element(By.XPATH,'//#selCountyCourt/option[text()="Albany County Supreme Court"]').click()
                        # driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(Keys.BACKSPACE * 50)
                        # driver.find_element(By.CSS_SELECTOR,'#txtFilingDate').send_keys(datetime.utcnow().strftime('%m/%d/%Y'))
                        # driver.find_element(By.CSS_SELECTOR,'input[type*="submit"]').click()
                    except Exception as e:
                        print('-'*50)
                        print(e)
                    finally:
                        driver.quit()
                        continue
                except Exception as e:
                    print(e)
                    pass
        sleep(20)
    except Exception as e:
        print(e)
        pass    
    
main()