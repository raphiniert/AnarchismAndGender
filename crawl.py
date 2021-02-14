# anarchism and gender

# standard imports
import argparse
from datetime import datetime
import logging
import locale
import math
import time

# crawling
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# db
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from db import Base, Journal, Issue, Page

# set german locale for accurate datetime parsing
locale.setlocale(locale.LC_TIME, "de_AT")

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
parser.add_argument(
    "--no-headless", help="don't run chrome headless", action="store_false"
)
parser.add_argument(
    "--skip-issue-crawling",
    help="don't crawl issues and use link list instead",
    action="store_true",
)
parser.add_argument("--update", help="update db entry if exists", action="store_true")
parser.add_argument(
    "--skip-db-issues",
    help="skip issue crawling if issue is already in db",
    action="store_true",
)
# TODO: add search args text, date


# logging
FORMAT = "%(asctime)-15s %(levelname)s %(message)s"
logging.basicConfig(
    filename=f"log/{datetime.now()}_anarchism_crawl.log",
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
SEARCH_TEXT = "Anarchis*"
DATE_FROM = "01.01.1898"
DATE_TO = "31.12.1898"


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


def get_db_session(echo=False):
    engine = create_engine(
        f"sqlite:///{SEARCH_TEXT.replace('*','')}_{DATE_FROM}-{DATE_TO}.db",
        encoding="utf-8",
        echo=echo,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


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


def get_issue_links():
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

    # extract links to journals containt search text
    issue_list = []
    for p in range(1, pages + 1):
        # iterate through links
        for journal_link in driver.find_elements_by_css_selector("div.entry_title a"):
            issue_list.append(journal_link.get_attribute("href"))
        logger.debug(f"Crawled page: {p}/{pages}.")
        driver.get(
            f"{BASE_URL}#{get_url_param_string(SEARCH_TEXT, DATE_FROM, DATE_TO, 1 + (p * RESULTS_PER_PAGE), JOURNAL_TYPE)}"
        )
        time.sleep(NAP_TIME)
    logger.info(f"Extracted {len(issue_list)} issue links.")
    return issue_list


def get_issue_text(issue_abbr, issue_date):
    r = requests.get(
        "https://anno.onb.ac.at/cgi-content/annoshow",
        params={"text": f"{issue_abbr}|{datetime.strftime(issue_date, '%Y%m%d')}|x"},
    )
    logger.debug(f"Getting issue full text from: {r.url}")
    return r.content


def get_page_text(journal_title, issue_date, issue_text, page):
    start_tag = f"[ {journal_title} - {datetime.strftime(issue_date, '%Y%m%d')} - Seite {page} ]"
    end_tag = f"[ {journal_title} - {datetime.strftime(issue_date, '%Y%m%d')} - Seite {page + 1} ]"
    issue_text = issue_text.decode("utf-8")
    if start_tag not in issue_text:
        logger.warning(f"Start tag: '{start_tag}' not found in issue full text.")
        return None
    page_text = issue_text.split(start_tag)[1]
    if end_tag in issue_text:
        page_text = page_text.split(end_tag)[0]
    else:
        logger.debug(
            f"End tag: '{end_tag}' not found in issue full text, assuming it's the last page."
        )
    return page_text


if __name__ == "__main__":
    t1 = datetime.now()
    args = parser.parse_args()
    if args.update and args.skip_db_issues:
        pass  # TODO: add warning

    if args.verbose:
        logger.setLevel(10)

    session = get_db_session(args.verbose)
    logger.info("Established database connection.")
    driver = setup_webdriver(args.no_headless)
    logger.info("Setup webdriver.")

    issue_list_filename = (
        f"issues/{SEARCH_TEXT.replace('*','')}_{DATE_FROM}-{DATE_TO}.txt"
    )

    if not args.skip_issue_crawling:
        issue_list = get_issue_links()
        # save links to file
        with open(issue_list_filename, "w") as f:
            f.write("\n".join(issue_list))
        logger.info(f"Saved issue list to: '{issue_list_filename}'")
    else:
        with open(issue_list_filename, "r") as f:
            issue_list = f.readlines()
        logger.info(
            f"Read issue list from: '{issue_list_filename}' with {len(issue_list)} items."
        )

    for issue_url in issue_list:
        issue_url = issue_url.strip()
        issue = session.query(Issue).filter(Issue.url == issue_url).first()
        if args.skip_db_issues:
            logger.debug(f"Checking if issue with url: {issue_url} is in db.")
            if issue:
                logger.debug(f"Skipping issue with urL: {issue_url}. Is already in db.")
                continue
        driver.get(issue_url)
        logger.debug(f"Crawling issue from: {issue_url}")
        # journal info
        journal_title = driver.find_element_by_css_selector(
            "div#tools-media h2.title"
        ).text
        journal_url = driver.find_element_by_css_selector(
            "div#tools-media-page div.content span.xoom a[title='info']"
        ).get_attribute("href")
        journal_url = f"{journal_url}"
        journal_abbr = issue_url.split("/ANNO/")[1][0:3]

        journal = session.query(Journal).filter(Journal.url == journal_url).first()
        if journal:
            if args.update:
                journal.title = journal_title
                # TODO: update further journal data
        else:
            journal = Journal(journal_title, journal_url)
        logger.debug(
            f"Journal info extracted. Title: {journal_title} with abbreviation: {journal_abbr}."
        )
        session.add(journal)
        session.commit()

        # issue info
        issue_date = driver.find_element_by_css_selector(
            "div#tools-main div.content ul li:nth-child(3)"
        ).text.strip()
        issue_date = datetime.strptime(
            issue_date.replace("Januar", "Jänner"), "%d. %B %Y"
        )
        issue_text = get_issue_text(journal_abbr, issue_date)
        logger.debug(
            f"Issue info extracted. Issue date: {issue_date} and issue text: {issue_text[:10]}"
        )

        if issue:
            if args.update:
                issue.text = issue_text
        else:
            issue = Issue(journal.journal_id, issue_date, issue_url, issue_text)
        session.add(issue)
        session.commit()

        # page info
        page_number = 1
        for page_link in driver.find_elements_by_css_selector(
            "div#content div.prevws a"
        ):
            page_url = page_link.get_attribute("href")
            page = session.query(Page).filter(Page.url == page_url).first()
            page_text = get_page_text(
                journal_title, issue_date, issue_text, page_number
            )
            try:
                page_link.find_element_by_class_name("treffer")
                hit = True
            except NoSuchElementException:
                hit = False
            if page:
                if args.update:
                    page.text = page_text
            else:
                page = Page(issue.issue_id, page_number, page_text, hit, page_url)
            session.add(page)
            logger.debug(
                f"Page info extracted. Number: {page_number}, page url: {page_url} and page text: {page_text[:10] if page_text else None}"
            )
            page_number += 1
        session.commit()

    session.close()
    driver.quit()
    logger.info(f"Completed. Processing took {(datetime.now() - t1).seconds}s.")
