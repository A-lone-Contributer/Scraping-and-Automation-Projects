import logging

# logger configuration
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)


def _get_technical_details(soup, dic):
    logging.info("Fetching technical details...")
    try:
        table = soup.find('table', id="productDetails_techSpec_section_1")
        details = [i for i in table.text.strip().split("\n") if i]
        _ = [dic.update({details[i]: details[i + 1]}) for i in range(0, len(details), 2)]

    except:
        logging.info("Failed to fetched technical details.")
        return

    logging.info("Finished fetching technical details!")


def _get_additional_details(soup, dic):
    logging.info("Fetching additional details...")
    try:
        table = soup.find('table', id="productDetails_detailBullets_sections1")
        table_headings = [item.text.strip() for item in
                          table.find_all("th", {"class": "a-color-secondary a-size-base prodDetSectionEntry"})]

        table = soup.find('table', id="productDetails_detailBullets_sections1").find_all("tr")
        final = []

        for tr in table:
            temp = []
            for i in tr.find_all("td", {"class": "a-size-base"}):
                temp.append(i.text.strip())
            final.append(temp)

        data = [{table_headings[i]: final[i]} for i in range(len(table_headings)) if final[i] and table_headings[i]]
        for d in data:
            for i, j in d.items():
                dic.update({i: ", ".join(j)})

    except:
        logging.info("Failed to fetch additional details.")
        return

    logging.info("Finished fetching additional details!")
