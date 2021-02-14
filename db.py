from sqlalchemy import (
    Column,
    Boolean,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Journal(Base):
    __tablename__ = "journals"

    journal_id = Column(Integer, primary_key=True)
    title = Column(String(1024), nullable=False)
    url = Column(String(512), nullable=True)
    language = Column(String(255), nullable=True)
    publication_place = Column(String(1024), nullable=True)

    def __init__(self, title, url, language=None, publication_place=None):
        self.title = title
        self.url = url
        self.language = language
        self.publication_place = publication_place

    def __repr__(self):
        return f"<Journal {self.title}>"


class Issue(Base):
    __tablename__ = "issues"

    issue_id = Column(Integer, primary_key=True)
    journal_id = Column(Integer, ForeignKey(Journal.journal_id), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    url = Column(String(512), unique=True)
    text = Column(Text, nullable=False)

    def __init__(self, journal_id, issue_date, url, text):
        self.journal_id = journal_id
        self.issue_date = issue_date
        self.url = url
        self.text = text

    def __repr__(self):
        return f"<Issue {self.issue_id}>"


class Page(Base):
    __tablename__ = "pages"

    page_id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey(Issue.issue_id), nullable=False)
    number = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    hit = Column(Boolean, default=False, nullable=False)
    url = Column(String(512), unique=True)

    def __init__(self, issue_id, number, text, hit, url):
        self.issue_id = issue_id
        self.number = number
        self.text = text
        self.hit = hit
        self.url = url

    def __repr__(self):
        return f"<Page {self.page_id}>"
