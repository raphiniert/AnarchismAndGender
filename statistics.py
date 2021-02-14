# anarchism and gender
# statistics.py

# standard imports
import argparse
import logging
from datetime import datetime
import spacy

# useful stuff
from collections import Counter
from string import punctuation
import numpy as np
import pandas as pd

from spacy.matcher import Matcher
from tqdm import tqdm

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
    filename=f"log/{datetime.now()}_statistics.log", format=FORMAT, level=20
)
logger = logging.getLogger("anarchism")

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(FORMAT)

# add formatter to ch
ch.setFormatter(formatter)


class TqdmHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)


th = TqdmHandler()
th.setFormatter(formatter)

# add ch to logger
# logger.addHandler(ch)
logger.addHandler(th)


# search parameters
JOURNAL_TYPE = "journal"
SEARCH_TEXT = "Anarchis*"
DATE_FROM = "01.01.1898"
DATE_TO = "31.12.1898"

relevant_journals_ids = (
    # 25,  # Agramer Zeitung
    12,  # Arbeiter Zeitung
    57,  # Arbeiterwille
    # 36,  # Bregenzer Tagblatt
    # 30,  # Bukowiner Rundschau
    23,  # Das Vaterland
    1,  # Deutsches Volksblatt
    #  3,  # Grazer Tagblatt
    # 31,  # Grazer Volksblatt
    # 32,  # Innsbrucker Nachrichtenn
    # 33,  # Kuryer Lwowski
    # 22,  # Kärtner Zeitungn
    # 48,  # Leitmeritzer Zeitung
    # 16,  # Linzer Volksblatt
    #  4,  # Mährisch-Schlesische Presse
    # 34,  # Mährisches Tagblatt
    54,  # Mödlinger Zeitung
    11,  # Neue Freie Presse
    #  7,  # Neues Wiener Journal
    #  5,  # Neues Wiener Tagblatt
    24,  # Pester Lloyd
    # 26,  # Prager Abendblatt
    27,  # Prager Tagblatt
    # 17,  # Reichspost
    # 18,  # Salzburger Chronik
    # 28,  # Salzburger Volksblatt
    # 13,  # Linzer Tages-Post
    #  8,  # Teplotz-Schönnauer Anzeiger
    38,  # Volksblatt für Stadt und Land
    # 46,  # Vorarlberger Landes-Zeitung
    # 14,  # Vorarlberger Volksblatt
    43,  # Wiener Neueste Nachrichten
    # 29,  # Wiener Zeitung
    # 35,  # (Neuigkeits) Welt Blatt
    # 72,  # Znaimer Tagblatt
    # 19,  # Znaimer Wochenblatt
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


def dump_relevant_text(search_pattern, dump_file):
    matcher = Matcher(nlp.vocab)
    # pattern

    for search_text in search_pattern:
        pattern = [
            # {"POS": "ADJ", "OP": "*"},
            # {"POS": "DET", "OP": "*"},
            # {"IS_PUNCT": True, "OP": "*"},
            {"LOWER": search_text.lower()},
            # {"IS_PUNCT": True},
        ]
        matcher.add(f"{search_text}_pattern".upper(), None, pattern)

    # get every sentence including the search text
    nlp_dict = {
        "issue_id": [],
        "journal_id": [],
        "issue_date": [],
        "match_id": [],
        "sentence": [],
        "window": [],
        # 'subtree': [],
    }
    for (issue_id, journal_id, issue_date, issue_text) in issue_query:
        text = issue_text.decode("utf-8")
        if len(text) > nlp.max_length:
            logger.warning(
                f"Skipping issue {issue_id} w/ jounral id: {journal_id}, because text length {len(text)} > {nlp.max_length}."
            )
            continue
        doc = nlp(text)  # load text
        matches = matcher(doc)
        window_length = 100
        for match_id, start, end in matches:
            search_text_token = doc[start]
            sentence = search_text_token.sent
            subtree_list = []
            start_pos = start - window_length
            if start < 0:
                start_pos = 0
            window_text = doc[start_pos : end + window_length].text
            logger.debug(f"Match found: '{window_text}' {issue_date}.")
            # for token in search_text_token.subtree:
            #     subtree_list.append(token.text)
            nlp_dict["issue_id"].append(issue_id)
            nlp_dict["journal_id"].append(journal_id)
            nlp_dict["issue_date"].append(issue_date)
            nlp_dict["match_id"].append(match_id)
            nlp_dict["sentence"].append(sentence)
            nlp_dict["window"].append(window_text)

    df = pd.DataFrame(data=nlp_dict)
    df.to_csv(dump_file)


def allow_token(t):
    if t.text.lower().startswith("anarchis"):
        return False
    if t.like_num:
        return False
    if t.is_punct:
        return False
    if t.text.lower() in nlp.Defaults.stop_words:
        return False
    return True


def get_most_common_token_pos(dataframe, token_pos="NOUN", counter_limit=20):
    token_pos_list = []
    for index, row in dataframe.iterrows():
        # get noun chunks per sentence
        doc = nlp(row["sentence"])
        # noun_list += [nc for nc in doc.noun_chunks]
        token_pos_list += [
            token.text.lower()
            for token in doc
            if token.pos_ == token_pos and allow_token(token)
        ]
    return Counter(token_pos_list).most_common(counter_limit)


def get_most_common_entities(dataframe, counter_limit=20):
    entity_list = []
    for index, row in dataframe.iterrows():
        # get noun chunks per sentence
        doc = nlp(row["window"])
        # noun_list += [nc for nc in doc.noun_chunks]
        entity_list += [
            ent.text.lower()
            for ent in [ents for ents in doc.ents]
            if ent.text.lower() not in nlp.Defaults.stop_words
        ]
    return Counter(entity_list).most_common(counter_limit)


def get_most_common_lists(
    dataframe, issue_date_start, issue_date_inter, issue_date_stop, counter_limit=20
):
    first_df = dataframe[
        (dataframe["issue_date"] >= issue_date_start)
        & (dataframe["issue_date"] < issue_date_inter)
    ]
    second_df = dataframe[
        (dataframe["issue_date"] >= issue_date_inter)
        & (dataframe["issue_date"] < issue_date_stop)
    ]
    first_most_common_noun = get_most_common_token_pos(first_df, "NOUN", counter_limit)
    second_most_common_noun = get_most_common_token_pos(
        second_df, "NOUN", counter_limit
    )
    first_most_common_adj = get_most_common_token_pos(first_df, "ADJ", counter_limit)
    second_most_common_adj = get_most_common_token_pos(second_df, "ADJ", counter_limit)
    first_most_common_entities = get_most_common_entities(first_df, counter_limit)
    second_most_common_entities = get_most_common_entities(second_df, counter_limit)
    return (
        first_most_common_noun,
        second_most_common_noun,
        first_most_common_adj,
        second_most_common_adj,
        first_most_common_entities,
        second_most_common_entities,
    )


def print_latex_table(journal_word_frequency, word_type, caption, label_prefix):
    for journal_title in journal_word_frequency:
        print("\\begin{table}[h!]")
        print("\\centering")
        print("\\begin{tabular}{ | l | l | l | l | }")
        print("\\hline")
        print(
            "\\multicolumn{2}{|l|}{Vor September} & \\multicolumn{2}{|l|}{Ab September} \\tabularnewline"
        )
        print("\\hline")
        print(f"{word_type} & Anzahl & {word_type} & Anzahl\\\\")
        print("\\hline")
        rows_1 = []
        rows_2 = []
        for word, frequency in sorted(
            journal_word_frequency[journal_title]["prior"].items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            rows_1.append(f"{word} & {frequency} &")
        for word, frequency in sorted(
            journal_word_frequency[journal_title]["post"].items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            rows_2.append(f"{word} & {frequency} \\\\")
        for i, row in enumerate(rows_1):
            if i < len(rows_2):
                print(row, rows_2[i])
            else:
                print(row, "- & - \\\\")
        print("\\hline")
        print("\\end{tabular}")
        print("\\caption{" + caption + " in: \\textit{" + str(journal_title) + "}}")
        print(
            "\\label{tbl:"
            + label_prefix
            + "_"
            + str(journal_title).lower().replace(" ", "_")
            + "}"
        )
        print("\\end{table}")
        print("")


if __name__ == "__main__":
    t1 = datetime.now()
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(10)
    session = get_db_session(args.verbose)

    # journal stats
    journal_query = session.query(
        Journal.journal_id, Journal.title, Journal.language, Journal.publication_place
    )
    journal_stats = [(j[0], j[1], j[2], j[3]) for j in journal_query]
    journals_df = pd.DataFrame(
        journal_stats,
        columns=["id", "title", "language", "pub place"],
    )
    logger.debug(journals_df.describe(include="all"))

    # issue stats
    issue_query = session.query(
        Issue.issue_id, Issue.journal_id, Issue.issue_date, Issue.text
    )
    issue_stats = [(i[0], i[1], i[2], i[3]) for i in issue_query]
    issue_df = pd.DataFrame(
        issue_stats,
        columns=["id", "journal_id", "date", "text"],
    )
    logger.info(issue_df.describe(include="all"))

    # nlp stuff
    nlp = spacy.load("de_core_news_lg")
    with open("stop_words.txt", "r") as f:
        nlp.Defaults.stop_words |= {word for word in f.read().split("\n")}
    dump_file = f"tmp/{SEARCH_TEXT.replace('*', '')}_{DATE_FROM}-{DATE_TO}.csv"
    search_pattern = [
        "anarchismus",
        "anarchist",
        "anarchistin",
        "anarchisten",
        "anarchistinnen",
    ]
    if args.dump_db:
        dump_relevant_text(search_pattern, dump_file)

    # load dataframe from csv
    df = pd.DataFrame()
    try:
        df = pd.read_csv(dump_file, delimiter=";", parse_dates=["issue_date"])
    except FileNotFoundError:
        logger.error(f"File: '{dump_file}' not found.")

    issue_date_start = datetime(year=1898, month=1, day=1, hour=0, minute=0, second=0)
    issue_date_inter = datetime(year=1898, month=9, day=1, hour=0, minute=0, second=0)
    issue_date_end = datetime(
        year=1898, month=12, day=31, hour=23, minute=59, second=59
    )
    counter_limit = 10

    start_inter_nouns = []
    inter_end_nouns = []
    start_inter_adjs = []
    inter_end_adjs = []
    start_inter_ents = []
    inter_end_ents = []

    journal_word_frequency_ents = {}
    journal_word_frequency_nouns = {}
    journal_word_frequency_adjs = {}
    for journal_id in tqdm(relevant_journals_ids):
        journal_df = df[(df["journal_id"] == journal_id)]
        journal_title = journals_df[(journals_df["id"] == journal_id)]["title"].values[
            0
        ]
        journal_word_frequency_nouns.update(
            {
                str(journal_title): {
                    "prior": {},
                    "post": {},
                }
            }
        )
        journal_word_frequency_adjs.update(
            {
                str(journal_title): {
                    "prior": {},
                    "post": {},
                }
            }
        )
        journal_word_frequency_ents.update(
            {
                str(journal_title): {
                    "prior": {},
                    "post": {},
                }
            }
        )
        (
            most_common_start_inter_noun,
            most_common_inter_end_noun,
            most_common_start_inter_adj,
            most_common_inter_end_adj,
            most_common_start_inter_ents,
            most_common_inter_end_ents,
        ) = get_most_common_lists(
            journal_df,
            issue_date_start,
            issue_date_inter,
            issue_date_end,
            counter_limit,
        )
        logger.debug(f"{counter_limit} most common nouns for journal: {journal_title}:")
        for (word, frequency) in most_common_start_inter_noun:
            if word not in search_pattern and frequency > 1:
                start_inter_nouns.append(word)
                logger.debug(f"{word}: {frequency}")
                journal_word_frequency_nouns[str(journal_title)]["prior"].update(
                    {word: frequency}
                )
        logger.debug(f"{counter_limit} most common nouns for journal: {journal_title}:")
        for (word, frequency) in most_common_inter_end_noun:
            if word not in search_pattern and frequency > 1:
                inter_end_nouns.append(word)
                logger.debug(f"{word}: {frequency}")
                journal_word_frequency_nouns[str(journal_title)]["post"].update(
                    {word: frequency}
                )

        logger.debug(f"{counter_limit} most common adjs for journal: {journal_title}:")
        for (word, frequency) in most_common_start_inter_adj:
            if word not in search_pattern and frequency > 1:
                start_inter_adjs.append(word)
                logger.debug(f"{word}: {frequency}")
                journal_word_frequency_adjs[str(journal_title)]["prior"].update(
                    {word: frequency}
                )
        logger.debug(f"{counter_limit} most common ajds for journal: {journal_title}:")
        for (word, frequency) in most_common_inter_end_adj:
            if word not in search_pattern and frequency > 1:
                inter_end_adjs.append(word)
                logger.debug(f"{word}: {frequency}")
                journal_word_frequency_adjs[str(journal_title)]["post"].update(
                    {word: frequency}
                )

        logger.debug(
            f"{counter_limit} most common named entities for journal: {journal_title}:"
        )
        for (word, frequency) in most_common_start_inter_ents:
            if word not in search_pattern and frequency > 1:
                start_inter_ents.append(word)
                logger.debug(f"{word}: {frequency}")
                journal_word_frequency_ents[str(journal_title)]["prior"].update(
                    {word: frequency}
                )

        logger.debug(
            f"{counter_limit} most common named entities for journal: {journal_title}:"
        )
        for (word, frequency) in most_common_inter_end_ents:
            if word not in search_pattern and frequency > 1:
                inter_end_ents.append(word)
                logger.debug(f"{word}: {frequency}")
                journal_word_frequency_ents[str(journal_title)]["post"].update(
                    {word: frequency}
                )

    logger.info("Printing entity frequencies per journal")
    print_latex_table(
        journal_word_frequency_ents,
        "Entität",
        "Entitäten im Suchintervall",
        "ent_window",
    )
    logger.info("Printing noun frequencies per journal")
    print_latex_table(
        journal_word_frequency_nouns, "Nomen", "Nomen im Suchsatz", "noun_sent"
    )
    logger.info("Printing adj frequencies per journal")
    print_latex_table(
        journal_word_frequency_adjs, "Adjektiv", "Adjektive im Suchsatz", "adj_sent"
    )
    # logger.info(f"most common prior words: {sorted(set(start_inter_words))}")
    # logger.info(f"most common post words: {sorted(set(inter_end_words))}")
    # logger.info(f"most common prior entities: {sorted(set(start_inter_ents))}")
    # logger.info(f"most common post entities: {sorted(set(inter_end_ents))}")

    session.close()
    logger.info(f"Completed. Processing took {(datetime.now() - t1).seconds}s.")
