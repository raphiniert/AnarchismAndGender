# anarchism and gender

import argparse
import logging
import datetime
import spacy

# useful stuff
from collections import Counter


# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", help="increase output verbosity", action="store_true")


# logging
FORMAT = "%(asctime)-15s %(levelname)s %(message)s"
logging.basicConfig(
    filename=f"log/{datetime.datetime.now()}_anarchism.log", format=FORMAT, level=20
)
logger = logging.getLogger("sentiment")

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(FORMAT)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# spacy
spacy_model = "de_core_news_lg"


def preprocess_text(text):
    # TODO: replace word breaks
    # TODO: replace old grammar with new equivalents e. g.
    # That -> Tat, thatsächlich -> tatsächlich
    logger.debug(f"Preprocessinng text.")
    # TODO: log changes
    text = text.replace(" ­\n", "")  # replace
    return text


def get_texts():
    # TODO: implement
    file_path = "text/bukowiner_nachrichten_18920408.txt"
    logger.debug(f"Extracting text from: {file_path}")
    with open(file_path) as f:
        text = preprocess_text(f.read())
    return text

# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    t1 = datetime.datetime.now()
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(10)
    nlp = spacy.load(spacy_model)
    logger.debug(f"Loaded spacy model {spacy_model}")
    doc = nlp(get_texts())
    # TODO: store preprocessed texts in db
    entities = [ent.text.lower() for ent in [ents for ents in doc.ents]]
    entitiy_frequency = Counter(entities)
    logger.info(entitiy_frequency)
    logger.info(
        f"Completed. Processing took {(datetime.datetime.now() - t1).seconds}s."
    )

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
