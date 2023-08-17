#! python
'''
This script scrapes a Google Maps URL with a query for places, and their details if found (email, phone number, opening hours,...)
'''
from seleniumFirefoxBase import launch_firefox_driver, webdriver, By, Keys, WebDriverWait, EC
import code
import re
import json
from datetime import datetime

# TODO: Calculate distance between the places and your home and sort the places accordingly (TIP: Use geopy.distance.distance(...) function)
# TODO: Add more user prompts (Ask if to take the query URL from 'constants.json' or to enter it as a prompt, or to search a place in a specific address)

def main():

    # Constants
    with open('constants.json') as f:
        constants_dict = json.load(f)

    GOMAPS_URL = constants_dict["GOMAPS_URL_QUERY"]
    PLACE_URL = constants_dict["PLACE_URL"]
    try:
        NUM_OF_PLACES = constants_dict["NUM_OF_PLACES"]
    except:
        NUM_OF_PLACES = 10
        print('NUM_OF_PLACES not found in constants.json. It is set to 10 by default.');
    # TEST = constants_dict["TEST"]
    # print(TEST)

    # sidecard_xpath = r'//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]/div[3]/div/a'

    driver: webdriver.Firefox = launch_firefox_driver()

    # Scrape all places and their details
    # places_data_lst = scrape_places(driver, GOMAPS_URL)
    places_data_lst = scrape_places(driver, GOMAPS_URL, NUM_OF_PLACES)
    print(places_data_lst)

    # Write to JSON file
    # ct stores current time
    ct = datetime.now()
    time_str = ct.strftime('%Y-%m-%d_%H-%M') +  str(ct.timestamp()).replace('.','')
    result_file = 'result_' + time_str + '.json'
    with open(result_file, mode='w', encoding='utf-8') as json_f:
        json.dump(places_data_lst, json_f, ensure_ascii=False)

    # TEST: Scrape place
    # driver.get(PLACE_URL)
    # scrape_place(driver)

    # TEST" get_coords_from_gomaps_url
    # coords = get_coords_from_gomaps_url(PLACE_URL)
    # print(f'{coords=}')

    input('Scraping ended! Press any key to quit...')
    driver.quit()


def scrape_places(driver: webdriver.Firefox, gomaps_url: str, max_num_of_places: int = 10):
    # Launch site
    driver.get(gomaps_url)

    # Wait for the page to load
    # Waiting time to find element, before raising an exception
    timeout = float(30)
    # Wait for zoom in button to be visible, as an indicator that the page is loaded
    zoomin_css = '#widget-zoom-in'
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, zoomin_css)))
    except:
        print('Zoom-in button not found!')
        print('Quitting...')
        return 1

    i = 1
    count = 0  # Number of places scraped
    places_feed_css = 'div[role="feed"]'
    places_data_lst: list[dict[str, str]] = []
    places_feed = driver.find_element(By.CSS_SELECTOR, places_feed_css)
    while (count < max_num_of_places):
        # Make next place_card's CSS selector
        place_card_css = r'div[role="feed"] > div:not([class]):nth-of-type(' + str(i*2+1) + ') > div:nth-child(1) > a'
        #
        place_card_a_lst = driver.find_elements(By.CSS_SELECTOR, place_card_css)
        # code.interact(local={**locals(), **globals()})
        if place_card_a_lst == []:
            # Scroll down the feed to load more places
            driver.execute_script('''feed = document.querySelector("div[role='feed']"); feed.scrollTo(0, feed.scrollHeight);''')
            # places_feed.send_keys(Keys.PAGE_DOWN)
            # places_feed.send_keys(Keys.PAGE_DOWN)
            try:
                WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, place_card_css)))
                continue
            except:
                print('place_card_a element not found or loading!')
                print(f'{place_card_css}')
                print('Quitting...')
                return 1
        elif len(place_card_a_lst) > 1:
            print('WEIRD... Found more than one place card with the same selector')
        place_url = place_card_a_lst[0].get_attribute('href')
        i += 1
        count += 1

        # Open URL in new tab and pass the driver to scrape_place function
        print(f'Opening place URL no. {count} ...')
        original_window = driver.current_window_handle
        driver.switch_to.new_window('tab')
        driver.get(place_url)
        # Call a function that scrapes the data (phone number, address,...) from the place_urls
        place_data = scrape_place(driver)
        driver.close()
        driver.switch_to.window(original_window)
        places_data_lst.append(place_data)
    return places_data_lst


def scrape_place(driver: webdriver.Firefox):
    '''Gets a driver with a Google Maps place in focus, return details in a python dictionary
    Dictionary keys: name, address, website, phone, coordinates '''
    # CSS Selectors
    css_slct_dict = {
        'name': {'slct': 'div[role="main"] h1',
                 'attr': 'text'},  # Get text
        'address': {'slct': 'button[data-item-id="address"] div.fontBodyMedium',
                    'attr': 'text'},  # Get text
        'website': {'slct': 'a[data-item-id="authority"]',
                    'attr': 'href'},  # Get href
        'phone': {'slct': 'button[data-item-id*="phone"], button[data-item-id*="tel"]',
                  'attr': 'text'},  # Get text
        # 'email': ''
    }
    # TODO: More CSS selectors: Opening hours selector ...

    # Scrape details
    data_dict = {}
    # Wait for page to load by waiting for the place name
    timeout = float(10)
    WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_slct_dict['name']['slct'])))
    for detail, selector in css_slct_dict.items():
        print(f'Scraping {detail} ...')
        el_lst = driver.find_elements(By.CSS_SELECTOR, selector['slct'])
        num_of_els_found = len(el_lst)
        if num_of_els_found >= 1:
            if num_of_els_found > 1:
                print(f'Weird... found more than one "{detail}". Scraping the first one found')
            if selector['attr'] == 'text':
                detail_data = el_lst[0].text
            else:
                detail_data = el_lst[0].get_attribute(selector['attr'])
            data_dict[detail] = detail_data
            print(f'V. {detail}: {detail_data}')

        else:  # el_lst is empty
            print(f'X . {detail} does not exist!')

    # Get the exact coordiantes of the place from URL
    data_dict['coordinates'] = get_coords_from_gomaps_url(driver.current_url)
    return data_dict


def get_coords_from_gomaps_url(url: str):
    '''Returns the coords (in a tuple) found in a Google Maps place URL.
    If it's not found, returns None.
    Example URL: https://www.google.com/maps/place/%D7 ... %80%AD/@32.8287764,35.0804737,17z/data= ... 
     => returns ('32.8287764', '35.0804737')
    '''
    regex_pattern = r'@([(0-9.]+),([0-9.]+)'
    match_lst = re.findall(regex_pattern, url)
    if match_lst:
        return match_lst[0]

    return None


if __name__ == "__main__":
    main()
