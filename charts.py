# anarchism and gender
# charts.py

# standard imports
import argparse
import logging
from datetime import datetime

# data
import pandas as pd
import numpy as np

# plotting
import matplotlib.pyplot as plt

# db
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# project specific
from db import Base, Journal, Issue, Page

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("--dump-db", help="don't run chrome headless", action="store_true")

# logging
FORMAT = "%(asctime)-15s %(levelname)s %(message)s"
logging.basicConfig(
    filename=f"log/{datetime.now()}_charts.log", format=FORMAT, level=20
)
logger = logging.getLogger("anarchism")

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(FORMAT)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# search parameters
JOURNAL_TYPE = "journal"
SEARCH_TEXT = "Anarchis*"
DATE_FROM = "01.01.1898"
DATE_TO = "31.12.1898"


def get_db_session(echo=False):
    engine = create_engine(
        f"sqlite:///{SEARCH_TEXT.replace('*','')}_{DATE_FROM}-{DATE_TO}.db",
        encoding="utf-8",
        echo=echo,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate(
            "{}".format(height),
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, 3),  # 3 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
        )


if __name__ == "__main__":
    t1 = datetime.now()
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(10)
    session = get_db_session(args.verbose)
    # issue stats
    issue_query = session.query(
        Issue.issue_id, Issue.journal_id, Issue.issue_date, Issue.text
    )
    issue_stats = [(i[0], i[1], i[2], i[3]) for i in issue_query]
    issue_df = pd.DataFrame(
        issue_stats,
        columns=["id", "journal_id", "date", "text"],
    )

    """
    plt.figure()
    ax = (issue_df["date"].groupby(issue_df["date"].dt.month).count().plot(
        kind="bar"))
    ax.bar()
    ax.set_facecolor('#eeeeee')
    ax.set_xlabel("1898")
    ax.set_ylabel("Zeitungsausgaben")
    ax.set_title(f"Begriff: {SEARCH_TEXT}")
    ax.set_xticks(x)
    ax.set_xticklabels(issue_df["date"].groupby(issue_df["date"].dt.month).count())
    plt.show()
    """
    labels = [
        "Jänner",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]
    men_means = issue_df["date"].groupby(issue_df["date"].dt.month).count()

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(x - width / 2, men_means, width, label="Zeitungsausgaben")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel("Anzahl")
    ax.set_title(f"Begriff: {SEARCH_TEXT}")
    ax.set_xlabel("1898")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    autolabel(rects)

    fig.tight_layout()
    plt.xticks(rotation=45)
    plt.show()

    session.close()
    logger.info(f"Completed. Processing took {(datetime.now() - t1).seconds}s.")
