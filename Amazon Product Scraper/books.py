import logging

# logger configuration
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)


def _get_product_title(soup, dic):
    logging.info('Getting the product title...')
    try:
        title = soup.find("span", id="productTitle").text
        dic.update({"Title": title.strip()})

    except:
        logging.info("Failed to fetch title.")
        return

    logging.info("Finished fetching title!")


def _get_author(soup, dic):
    global author
    logging.info('Getting the product author name...')
    try:
        author = soup.find('a', {"class": "a-link-normal contributorNameID"})
        dic.update({"Author": author.text.strip()})

    except:
        logging.info("Failed to fetch author.")
        return

    logging.info("Finished fetching author!")


def _get_price(soup, dic):
    logging.info('Getting the product price...')
    price = soup.find("div", id="soldByThirdParty")
    try:

        dic.update({"Price (in rupees)": price.text.strip().replace("\u20b9\u00a0", "")})

    except:

        try:
            dic.update({"Price (in rupees)": price.text.strip()})

        except:

            logging.info("Failed to fetch price.")
            return

    logging.info("Finished fetching price!")


def _get_product_details(soup, dic):
    logging.info("Getting the product details...")
    details = soup.find('div', {"id": "detailBulletsWrapper_feature_div"})
    list_elements = details.find_all("li")

    for elements in list_elements:
        detail_row_list = [i.strip() for i in elements.text.rstrip().split(":")]

        try:
            if detail_row_list[1]:
                if len(detail_row_list) == 2:
                    dic.update({detail_row_list[0]: detail_row_list[1]})
                else:
                    dic.update({detail_row_list[0]: ", ".join(detail_row_list[1:])})

        except:

            logging.info("Failed to fetch product details.")
            return

    logging.info("Finished fetching product details!")
