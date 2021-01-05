# anarchism and gender

# standard imports
import argparse
import datetime
import logging
import locale
import math
import time

# selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException


# db
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# set german locale for accurate datetime parsing
locale.setlocale(locale.LC_TIME, "de_AT")

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
parser.add_argument(
    "--no-headless", help="don't run chrome headless", action="store_false"
)
# TODO: add search args text, date


# logging
FORMAT = "%(asctime)-15s %(levelname)s %(message)s"
logging.basicConfig(
    filename=f"log/{datetime.datetime.now()}_anarchism_crawl.log",
    format=FORMAT,
    level=20,
)
logger = logging.getLogger("anarchism_crawl")

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(FORMAT)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


# settings
BASE_URL = f"https://anno.onb.ac.at/anno-suche"
NAP_TIME = 2  # seconds
RESULTS_PER_PAGE = 10

# search parameters
JOURNAL_TYPE = "journal"
SEARCH_TEXT = "Anarchismus"
DATE_FROM = "01.01.1898"
DATE_TO = "31.12.1898"


def get_url_param_string(
    search_text, date_from, date_to, page=1, journal_type="journal"
):
    return (
        f"searchMode=complex&"
        f"text={search_text}&"
        f"dateMode=date&dateFrom={date_from}&dateTo={date_to}&"
        f"from={page}&"
        f"sort=date+asc&"
        f"selectedFilters=type%3A{journal_type}"
    )


def setup_webdriver(run_headless=True):
    chrome_options = Options()
    if run_headless:
        chrome_options.add_argument("--headless")
        logger.info("Initializing Chrome with headless option.")
    else:
        logger.info("Initializing Chrome without headless option.")
    return webdriver.Chrome(
        executable_path="bin/chromedriver",
        # Optional argument, if not specified will search path.
        options=chrome_options,
    )


if __name__ == "__main__":
    t1 = datetime.datetime.now()
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(10)

    # TODO: db
    # session = get_db_session(args.verbose)
    # logger.info("Established database connection.")
    driver = setup_webdriver(args.no_headless)
    logger.info("Setup webdriver.")

    # enter search params
    driver.get(
        f"{BASE_URL}#{get_url_param_string(SEARCH_TEXT, DATE_FROM, DATE_TO, 1, JOURNAL_TYPE)}"
    )
    time.sleep(NAP_TIME)
    # calculate results and pages
    result_count = driver.find_element_by_css_selector("div#contentForm\:result h4")
    result_count = int(result_count.text.split(" ")[0].replace(".", ""))
    pages = math.ceil(result_count / RESULTS_PER_PAGE)
    logger.info(f"Expecting {result_count} results on {pages} pages.")
    journal_list = []
    for p in range(1, pages + 1):
        # iterate through links
        for journal_link in driver.find_elements_by_css_selector("div.entry_title a"):
            journal_list.append(journal_link.get_attribute("href"))
        logger.debug(f"Crawled page: {p}/{pages}.")
        driver.get(
            f"{BASE_URL}#{get_url_param_string(SEARCH_TEXT, DATE_FROM, DATE_TO, p + RESULTS_PER_PAGE, JOURNAL_TYPE)}"
        )
        time.sleep(NAP_TIME)
    logger.info(f"Extracted {len(journal_list)} {JOURNAL_TYPE} links.")
    journal_list_filename = f"journals/{SEARCH_TEXT}_{DATE_FROM}-{DATE_TO}.txt"
    with open(journal_list_filename, "w") as f:
        f.write("\n".join(journal_list))
    logger.info(f"Saved link list to: '{journal_list_filename}'")

    # session.close()
    driver.quit()
    logger.info(
        f"Completed. Processing took {(datetime.datetime.now() - t1).seconds}s."
    )
