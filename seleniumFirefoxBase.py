from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By # Searching elements (e.g. By.ID)
from selenium.webdriver.common.keys import Keys # For sending key strokes
from selenium.webdriver.common.action_chains import ActionChains # Send keys to page
from selenium.webdriver.support.ui import WebDriverWait # Wait
from webdriver_manager.firefox import GeckoDriverManager # Install/Update webdriver
from selenium.webdriver.support import expected_conditions as EC

def launch_firefox_driver() -> webdriver.Firefox:
    '''Launch firefox webdriver, 
        with extensions: adblocker-ultimate'''
    browser = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
    # Addons
    adblock_path = '.\\firefox-extensions\\adblocker_ultimate-3.7.21.xpi'
    browser.install_addon(adblock_path, temporary=True)
    # Close all tabs opened by extensions
    # print(browser.window_handles)
    if len(browser.window_handles) > 1:
        # print('len(browser.window_handles) > 1')
        # print(f'{len(browser.window_handles)=}')
        for i, window in enumerate(browser.window_handles):
            if i != 0:
                browser.switch_to.window(window)
                browser.close()
    browser.switch_to.window(browser.window_handles[0]) # Switch focus to first tab (the one we're working with)
    browser.maximize_window() # Maximize window
    return browser

if __name__ == "__main__":
    browser = launch_firefox_driver()
    browser.get('https://google.com')