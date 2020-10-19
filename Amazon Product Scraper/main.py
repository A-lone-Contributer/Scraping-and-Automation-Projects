"""

Steps to create get a rotating proxy:

1. Go to https://proxy.webshare.io/
2. Create a free account
3. Go to Proxy -> Rotating proxy
4. Copy the respective credential when prompted on console.

"""

import csv
import logging
import os
import shutil
import time
import urllib.request
from os import listdir
from urllib.request import urlretrieve

from bs4 import BeautifulSoup

from ip_auth import fill_data, get_chromedriver

# logger configuration
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)


def get_page_soup(driver):
    logging.info("Requesting page for soup...")
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    return soup


def get_categories():
    logging.info("Getting categories list...")
    category_links = get_page_soup(driver).find_all('a', {'class': "a-link-normal aok-block a-text-normal"})
    category_url_dict = {}

    for categories in category_links:
        category_url_dict.update({categories.text.strip(): "https://www.amazon.in/" + categories['href']})

    logging.info("Categories list successfully fetched!")

    return category_url_dict


def get_product_links():
    logging.info("Getting specified category product links...")
    soup = get_page_soup(driver)

    try:

        products = soup.find_all('a', {'class': "a-link-normal a-text-normal"})

        for product in products[1:]:
            product_urls.append("https://www.amazon.in" + product['href'])

        if len(product_urls) >= _PRODUCTS_TO_FETCH:
            with open(CATEGORY + ".txt", "w") as outfile:
                outfile.write("\n".join(product_urls[:_PRODUCTS_TO_FETCH]))

            logging.info("All fetched links successfully written to a file!")
            return

        driver.get("https://www.amazon.in" + soup.find("li", {"class": "a-last"}).find('a')['href'])  # next page
        time.sleep(4)
        get_product_links()

    except Exception as e:

        logging.info(f"Following error occurred: {e}")
        pass

    logging.info("Finished fetching all the links!")


def navigate_urls():
    global price

    logging.info("Fetching links from the product URLs file...")
    with open(CATEGORY + '.txt') as infile:
        product_urls = infile.read().splitlines()

    logging.info("Got all the links!")

    logging.info("Starting main process...")
    for url in product_urls[:_PRODUCTS_TO_FETCH]:

        logging.info(f"Starting fetching operation of URL : {url}")
        driver.get(url)
        time.sleep(2)
        soup = get_page_soup(driver)
        final = {'Title': None, 'Product URL': url, 'Price (in rupees)': None, 'Stock Status': None,
                 'Product Specification': None}

        dic = {}

        if CATEGORY == 'Books':
            from books import _get_product_title, _get_author, _get_product_details, _get_price
            _get_product_title(soup, final)
            _get_author(soup, dic)
            _get_price(soup, final)
            in_stock(soup, final)
            _get_product_details(soup, dic)

        else:

            from books import _get_product_title, _get_product_details
            _get_product_title(soup, final)

            try:
                price = soup.find("span", id="priceblock_ourprice")
                final.update({"Price (in rupees)": price.text.strip().replace("\u20b9\u00a0", "")})

                in_stock(soup, final)
                _get_product_details(soup, dic)

            except:

                try:
                    price = driver.find_element_by_xpath('//*[@id="unqualified-buybox-olp"]/div/span')
                    final.update({"Price (in rupees)": price.text.strip().replace("\u20b9", "")})

                    in_stock(soup, final)
                    _get_product_details(soup, dic)
                except:
                    pass

            try:
                from books import _get_product_title, _get_product_details
                from electronics import _get_technical_details, _get_additional_details
                _get_product_title(soup, final)
                try:
                    _get_product_details(soup, dic)
                except:

                    try:
                        _get_technical_details(soup, dic)
                        _get_additional_details(soup, dic)
                    except:
                        pass

            except:
                pass

        _download_product_image(soup, final)

        try:
            dic['Customer Reviews'] = ";".join(
                set([i.strip() for i in dic['Customer Reviews'].replace("\n", " ").split("  ") if i]))

            dic['Best Sellers Rank'] = dic['Best Sellers Rank'].replace("\n", " ").split("  ")
        except:
            pass

        if dic:
            final['Product Specification'] = dic
            write_csv(final)


def in_stock(soup, dic):
    logging.info("Checking for product availability...")
    stock_status = soup.find('span', {"class": "a-size-medium a-color-success"}).text.strip()
    dic.update({"Stock Status": stock_status})
    logging.info("Finished checking for availability!")


def _download_product_image(soup, dic):
    logging.info("Downloading the Product Image...")

    imgs = str(soup.find('div', {"class": "imgTagWrapper"}))
    imgUrl = imgs.split('data-old-hires="')[-1].split('"')[0]

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    try:
        file_name = os.path.basename(imgUrl)
        time.sleep(2)
        urlretrieve(imgUrl, os.path.basename(imgUrl))
        new_name = dic['Title'] + ".jpg"
        os.rename(file_name, new_name)
        shutil.move(new_name, CATEGORY)
        time.sleep(2)
        logging.info("File Downloaded Successfully!")
    except:
        logging.info("----Not able to download the image----")


def write_csv(data):
    logging.info("Adding the data to CSV...")
    try:
        with open(CATEGORY + ".csv", 'a+', newline='', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=data.keys(), delimiter=',')

            if csvfile.tell() == 0:
                writer.writeheader()

            if csvfile.tell() != 0:
                writer.writerow(data)
                logging.info("Record added to the File")
                logging.info("-" * 40)

    except Exception as e:
        logging.error(e)


'''DRIVER CODE'''

PROXY_HOST = input("Enter the IP address: ")
PROXY_PORT = 80
PROXY_USER = input("Enter username for the proxy: ")
PROXY_PASS = input("Enter password for the proxy: ")
CATEGORY = input("Enter the product category: ")
_PRODUCTS_TO_FETCH = int(input("Enter the number of products you want to fetch: "))

manifest_json, background_js = fill_data(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
driver = get_chromedriver(manifest_json, background_js)

try:
    os.mkdir(CATEGORY)
except:
    print("")

product_urls = []

logging.info("Looking for already fetched product URL list...")
if not os.path.exists(CATEGORY + '.txt'):

    logging.info("Product URL list not found!")
    driver.get('https://www.amazon.in/b?ie=UTF8&node=6308595031')

    time.sleep(3)

    driver.get(get_categories()[CATEGORY])
    get_product_links()
else:
    logging.info("Product URL list found!")
print("Navigating to URLs...\n")
navigate_urls()

try:
    for file_name in listdir():
        if file_name.endswith(".jpg"):
            shutil.move(file_name, CATEGORY)
except:
    pass

logging.info("Cleaning up...")
logging.info("Exiting...")

print("Complete!")
driver.close()
