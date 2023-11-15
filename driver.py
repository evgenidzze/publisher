import asyncio
import undetected_chromedriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium_stealth import stealth
from selenium.webdriver.support import expected_conditions as EC

uc_options = undetected_chromedriver.ChromeOptions()
uc_options.headless = True
driver = undetected_chromedriver.Chrome(options=uc_options)

stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win64",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

wait = WebDriverWait(driver, 30)
driver.maximize_window()
driver.get('https://viks.com/uz#sign-in')
email_button = wait.until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-tab="email"].item.smooth-toggle_item')))
ActionChains(driver).move_to_element(email_button).click(email_button).perform()
email = wait.until(EC.visibility_of_element_located((By.ID, 'i-40324f4a-login')))
email.clear()
email.send_keys('predict3@tuta.io')

password = wait.until(EC.visibility_of_element_located((By.ID, 'i-40324f4a-password')))
password.clear()
password.send_keys('Predict3')
password.send_keys(Keys.ENTER)

sign_in_btn = (
    "xpath", "//button[@type='submit' and @class='button primary big shadow fluid']/span[text()='Kirish']")
wait.until(EC.invisibility_of_element_located(sign_in_btn))
driver.get('https://viks.com/uz/game/spribe/aviator3/real')

game_iframe = wait.until(EC.visibility_of_element_located((By.ID, 'game-iframe')))
driver.switch_to.frame(game_iframe)

# Find and switch to the second iframe within the first iframe
second_iframe = wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'iframe')))
driver.switch_to.frame(second_iframe)

# Find and switch to the third iframe within the second iframe
third_iframe = wait.until(EC.visibility_of_element_located((By.NAME, 'game')))
driver.switch_to.frame(third_iframe)


async def wait_for_new_coef():
    try:
        div_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'payouts-block')))
        div_content = div_element.text.split('\n')
        if float(div_content[0].split('x')[0]) > 1.5:
            last_coefs = div_content
            while last_coefs[:4] == div_content[:4]:
                div_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'payouts-block')))
                div_content = div_element.text.split('\n')
            else:
                return div_content[0].split('x')[0]
        else:
            await asyncio.sleep(2)
            await wait_for_new_coef()



    except:
        pass
