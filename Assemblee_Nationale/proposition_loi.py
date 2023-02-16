import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from dateutil import parser
import json
import locale

# set the locale to French
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

Base = declarative_base()

class Law_proposals(Base):
    __tablename__ = 'law_proposals'

    ids = Column("id", Integer, primary_key=True)
    number = Column("number", Integer)
    title = Column("title", String)
    link = Column("link", String)
    date = Column("date", DATE)
    author = Column("author", TEXT)
    cosigner = Column("cosigner", TEXT)

    def __init__(self, law):
        self.number = law["number"]
        self.title = law["title"]
        self.link = law["link"]
        #self.date = law["date"]

    
    def __repr__(self):
        return f'(Commission n {self.name})'

# SQLAlchemy
engine = create_engine('sqlite:///votes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

URL = 'https://www2.assemblee-nationale.fr/documents/liste/(type)/propositions-loi'
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

law = {}
while True:
    # Find all the rows in the table
    lis = soup.find('ul', class_='liens-liste').find_all('li', recursive=False)
    # Iterate over the rows
    for p in lis:
        # Extract the number of the proposal
        law['number'] = p.find('h3').text.split('-')[-1].replace(u'\xa0', ' ').split(' ')[-1]
        # Extract title
        law['title'] = p.find('h3').text
        # Extract link
        law['link'] = p.find('ul').find_all('li')[-1].find('a')['href']
        # Extract date
        law['date'] = p.find('ul').find_all('li')
        # TODO Extract author and cosigners or take from deputes info ?
        # Extract author
        url_redirect = 'https://www.assemblee-nationale.fr/dyn/16/textes/l16b' + law['number'].zfill(4) + '_proposition-loi#'
        page_law = requests.get(url_redirect)
        tmp = BeautifulSoup(page_law.content, 'html.parser')
        iframe = tmp.find('iframe')
        if iframe:
            iframe_url = iframe['src']
            url_iframe = 'https://www.assemblee-nationale.fr' + iframe['src']
            print(url_iframe)
            response = urlopen(url_iframe)
            signers = BeautifulSoup(response, 'html.parser')
            author = signers.find('div', class_='assnatSection1').find_all('span', class_='assnatLnom')
            print(author)
        # Extract cosigner
        #print(f'author: {signers}')
        # Store in DB
        law_proposal = Law_proposals(law)
        session.add(law_proposal)
        session.commit() 

    # Iterate over all pages    
    pagination = soup.find('div', class_='pagination-bootstrap')
    if pagination:
        next = pagination.find_all('li')[-1].find('a')
        if next:
            url_next = 'https://www2.assemblee-nationale.fr' + next['href']
            next = requests.get(url_next)
            soup = BeautifulSoup(next.content, 'html.parser')
        else:
            break
    else:
        break
        