import csv
import logging
import os
import shutil
import sys
import urllib.request
from os import listdir
from urllib.request import urlretrieve

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

pd.set_option('mode.chained_assignment', None)

options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

# Default arguments
_DEFAULT_URL = "https://hr.iherb.com/c/categories"
_DEFAULT_BEAUTIFULSOUP_PARSER = "html.parser"
_DEFAULT_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/39.0.2171.95 Safari/537.36'}

# logger configuration
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)

final_list = []


def _get(url, headers):
    """ GET request with the proper headers """

    logging.info("Sending request to base URL...")
    ret = requests.get(url, headers=headers)
    if ret.status_code != 200:
        logging.error('Status code {status} for url {url}\n{content}'.format(
            status=ret.status_code, url=url, content=ret.text))

    logging.info(f"Website returned status code : {ret.status_code}")
    return ret


def _get_page_html(url):
    res = _get(url, _DEFAULT_HEADER)
    soup = BeautifulSoup(res.content, _DEFAULT_BEAUTIFULSOUP_PARSER)
    return soup


def _get_url_list():
    logging.info("Fetching the URL list...")

    try:
        for i in range(6, 140):
            logging.info("Sending request to the next product page")
            url = _DEFAULT_URL + "?noi=192&p=" + str(i)
            soup = _get_page_html(url)
            divs = soup.find_all("div", {"class": "absolute-link-wrapper"})
            for div in divs[1:]:
                final_list.append(div.find('a')['href'])

            if len(final_list) >= _RECORDS_TO_FETCH:
                break

    except:
        logging.info("No more product pages")

    logging.info("URL list Fetched!")
    return final_list[0:_RECORDS_TO_FETCH]


def _check_duplicates_early(product_specs, filename):
    logging.info("Checking for early duplicates..")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
        if product_specs['product_name'] + "\n" in lines:
            return True

        return False


def _check_updates_early(filename, product_id):
    logging.info("Checking for early duplicates..")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
        if product_id + "\n" in lines:
            return True

        return False


def _fetch_data():
    for url in _get_url_list():
        print(url)

        try:
            logging.info("Sending Request to a new Product Page")
            r = requests.get(url=url, headers=_DEFAULT_HEADER)
            soup = BeautifulSoup(r.content, features="html.parser")

            productspecs = {}
            logging.info(f"Started scraping : {url}")

            _get_product_code(soup, productspecs)
            _get_product_name(soup, productspecs)

            if not _check_duplicates_early(productspecs, 'completed.txt'):
                _get_product_description(soup, productspecs)

                productspecs['product_description_type'] = "html"

                _get_product_manufacture_id(soup, productspecs)

                productspecs.update({"product_quantity": _get_product_status(soup)})

                _get_price(url, productspecs)
                _get_product_category(soup, productspecs)

                productspecs['currency_id'] = "kn"

                _download_product_image(soup, productspecs, driver)

                yield productspecs

        except:
            with open("error_urls.txt", "a+", encoding='utf-8') as file1:
                file1.write(f"{url}\n")

    logging.info("Record already exists | Skipping..")


def _get_product_code(soup, productspecs):
    product_code = "N/A"
    try:
        check_list = soup.find("ul", id="product-specs-list").find_all("li")[2].text.split(":")
        if check_list[0] != "Product Code":
            product_code = soup.find("ul", id="product-specs-list").find_all("li")[1].text.split(":")[-1].strip()
        else:
            product_code = check_list[-1].strip()
    except:
        logging.info("Product Code not Found!")

    productspecs.update({"product_code": product_code})


def _get_product_name(soup, productspecs):
    product_name = "N/A"
    try:
        product_name = soup.find("h1", itemprop="name").text.strip()
    except:
        logging.info("Product Name not Found!")

    productspecs.update({"product_name": product_name})


def _get_product_manufacture_id(soup, productspecs):
    brand_name = "N/A"
    try:
        brand_name = soup.find("span", itemprop="name").text.strip()

    except:
        logging.info("Brand Name not Found!")

    productspecs.update({"product_manufacturer_id": brand_name})


def _get_price(url, productspecs):
    logging.info("Getting the Product Price...")
    product_price = "N/A"
    driver.get(url)
    try:
        product_price = driver.find_element_by_xpath('//*[@id="super-special-price"]/div/div[2]/div/b').text
    except:
        try:
            product_price = driver.find_element_by_xpath('//*[@id="price"]').text
        except:
            try:
                product_price = driver.find_element_by_class_name("price-container").text
            except:
                logging.info("Product Price not found!")

    productspecs.update({"price_value": product_price})


def _get_price_updated(driver):
    logging.info("Getting the Product Price...")
    product_price = "N/A"
    try:
        product_price = driver.find_element_by_xpath('//*[@id="super-special-price"]/div/div[2]/div/b').text
    except:
        try:
            product_price = driver.find_element_by_xpath('//*[@id="price"]').text
        except:
            try:
                product_price = driver.find_element_by_class_name("price-container").text
            except:
                logging.info("Product Price not found!")

    return product_price


def _get_product_status(soup):
    logging.info("Checking Product availability")

    try:
        product_status = soup.find("div", id="stock-status").text.strip()

        if product_status.startswith("In Stock"):
            price_quantity = -1
        else:
            price_quantity = 0

        return price_quantity

    except:
        logging.info("Product Status Not Found")
        return "N/A"


def _download_product_image(soup, productspecs, driver):
    logging.info("Downloading the Product Image...")

    try:
        tags_list = soup.find("div", {"class": "thumbnail-container"}).find_all("img")

    except:
        tags_list = None

    images_link = []

    if tags_list:
        for tags in tags_list:
            try:
                images_link.append(tags["data-large-img"])
            except:
                logging.info("No Image found!")

    if not tags_list:
        try:
            image = driver.find_element_by_xpath('//*[@id="product-image"]/div[1]/a').get_attribute('href')
            images_link.append(image)
        except:
            logging.info("No image available!")

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    new_names_list = []
    try:
        for imgUrl in images_link:
            file_name = os.path.basename(imgUrl)
            urlretrieve(imgUrl, os.path.basename(imgUrl))
            new_list = imgUrl.split("/")
            new_name = new_list[4] + "-" + new_list[-1]
            os.rename(file_name, new_name)
            shutil.move(new_name, "images")
            logging.info("File Downloaded Successfully!")
            new_names_list.append(new_name)
            productspecs.update({"images": "; ".join(new_names_list)})

    except:
        logging.info("----Not able to download the image----")


def _get_product_category(soup, productspecs):
    logging.info("Getting the Product Category...")

    try:
        bread_crumps = soup.find("div", id="breadCrumbs").find_all("a")[3:]
        categories = []
        for cat in bread_crumps:
            categories.append(cat.text)
        productspecs.update({"categories": ";".join(set(categories))})
    except:
        logging.info("Not able to Extract Product Category")
        productspecs.update({"categories": "N/A"})


def _get_product_description(soup, productspecs):
    logging.info("Fetching the product description...")
    desc_html = "N/A"
    try:
        desc_html = str(soup.select("div.container.product-overview")[0]).split("\n")

    except:
        logging.info("Product Description not found!")

    productspecs.update({"product_description": " ".join(desc_html)})


print(30 * "-", "MENU", 30 * "-")
print("1. Fetch new products")
print("2. Update products")
print(67 * "-")

loop = True

while loop:
    choice = int(input("Enter your choice [1-2]: "))

    if choice == 1:

        _RECORDS_TO_FETCH = int(input("Enter the number of records you want to fetch: "))

        try:
            os.mkdir("images")
        except:
            print("")

        fetched_data = _fetch_data()
        csv_file = "product_details.csv"

        print('Fetching started!')

        for data in fetched_data:

            logging.info("Adding Fetched Data to CSV File...")
            try:
                with open(csv_file, 'a+', newline='', encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(
                        csvfile, fieldnames=data.keys(), delimiter=',')

                    if csvfile.tell() == 0:
                        writer.writeheader()

                    if csvfile.tell() != 0:
                        writer.writerow(data)
                        with open("completed.txt", "a+", encoding='utf-8') as file1:
                            file1.write(f"{data['product_name']}\n")
                        logging.info("Record added to the File")
                        logging.info("-" * 40)

            except Exception as e:
                logging.error(e)

        for file_name in listdir():
            if file_name.endswith(".jpg"):
                os.remove(file_name)

        logging.info("All the operations have been completed successfully!")
        print("Fetching Complete.")
        break

    elif choice == 2:

        print("NOTE: If you want to fetch from the start then make sure you have deleted last_index.txt "
              "file from the last run!\n")

        if not os.path.exists('product_details.csv'):
            print("CSV file not found!")
            sys.exit()

        count, temp = 0, 0

        _RECORDS_TO_FETCH = int(input("Enter the number of records you want to update: "))

        data = pd.read_csv('product_details.csv', low_memory=False)

        if os.path.exists('last_index.txt'):
            try:
                with open('last_index.txt', 'r') as f:
                    lines = f.read().splitlines()
                    temp = int(lines[-1].strip())
            except:
                print("last_index file can't be empty! Delete the file and try again!")
                sys.exit()

        else:
            temp = 0

        outfile = open("last_index.txt", "a+")

        for row in data.itertuples(index=False):

            try:

                if temp > count:
                    logging.info(f"Skipped product ID : {row.product_code} || Reason : Already updated.")
                    count += 1
                    continue

                elif count >= _RECORDS_TO_FETCH:
                    break

                else:
                    page_url = 'https://hr.iherb.com/search?kw=' + row.product_code

                    logging.info(f"Product ID being updated - {row.product_code} || Excel index : {count}")

                    driver.get(page_url)
                    updated_product_price = _get_price_updated(driver)
                    updated_product_status = _get_product_status(BeautifulSoup(driver.page_source, 'html.parser'))

                    data.loc[:, 'product_quantity'][count] = updated_product_status
                    data.loc[:, 'price_value'][count] = updated_product_price

                    count += 1

            except:

                logging.info(f"Error while updating - {row.product_code}")
                pass

        outfile.write(str(count) + "\n")

        data.to_csv('product_details_updated.csv', index=False, float_format='%.0f')
        print("Updates Complete!")
        outfile.close()
        loop = False

    else:
        print("Invalid Choice!")
        sys.exit()
