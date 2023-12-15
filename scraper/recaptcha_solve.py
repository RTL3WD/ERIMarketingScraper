# Import necessary libraries
from selenium.webdriver.common.by import By
from anticaptchaofficial.recaptchav2proxyless import *

# Define a function to solve Recaptcha using AntiCaptcha service


def solve_recaptcha(driver, anticaptcha_key):
    """
    Solves Recaptcha using the AntiCaptcha service.

    :param driver: The selenium chrome driver.
    :param anticaptcha_key: Your AntiCaptcha API key.
    :return: The solution response for the Recaptcha.
    """

    # Get the Recaptcha sitekey from the web page
    sitekey = driver.find_element(
        By.CSS_SELECTOR, '#captcha_form > div').get_attribute('data-sitekey')

    try:
        # Create an instance of the recaptchaV2Proxyless solver
        solver = recaptchaV2Proxyless()

        # Configure solver settings
        solver.set_verbose(1)
        solver.set_key(anticaptcha_key)
        solver.set_website_url(driver.current_url)
        solver.set_website_key(sitekey)

        # Solve the Recaptcha and return the solution
        g_response = solver.solve_and_return_solution()

        if g_response != 0:
            recaptcha_response = g_response
        else:
            print("Task finished with error " + solver.error_code)

        # Inject the Recaptcha solution into the web page and submit the form
        driver.execute_script(
            'var element = document.getElementById("g-recaptcha-response"); element.style.display="";')
        driver.execute_script(
            'document.getElementById("g-recaptcha-response").innerHTML = "%s"' % recaptcha_response)
        driver.execute_script(
            'document.querySelector("#captcha_form").submit()')

    except:
        pass  # Handle exceptions gracefully (e.g., if Recaptcha solving fails)
