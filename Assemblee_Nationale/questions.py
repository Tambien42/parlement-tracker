import requests
from bs4 import BeautifulSoup
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

class Questions(Base):
    __tablename__ = 'questions'

    ids = Column("id", Integer, primary_key=True)
    link = Column("link", String)
    type = Column("type", String)
    number = Column("number", Integer)
    legislature = Column("legislature", Integer)
    name = Column("name", String)
    title = Column("title", String)
    ministry = Column("ministry", String)
    asked_date = Column("asked_date", String)
    answered_date = Column("answered_date", String)

    def __init__(self, question):
        self.link = question["link"]
        self.type = question["type"]
        self.number = question["number"]
        self.legislature = question["legislature"]
        self.name = question["name"]
        self.title = question["title"]
        self.ministry = question["ministry"]
        self.asked_date = question["asked_date"]
        self.answered_date = question["answered_date"]

    
    def __repr__(self):
        return f'(Commission n {self.name})'

# SQLAlchemy
engine = create_engine('sqlite:///votes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

URL = 'https://www2.assemblee-nationale.fr/recherche/resultats_questions/'
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

questions = {}
while True:
    # Find all the rows in the table
    rows = soup.find('table').find('tbody').find_all('tr')
    # Iterate over the rows
    for row in rows:
        column = row.find_all('td')
        # Extract Link
        questions["link"] = column[0].find('a')['href']
        # Extract the type of question
        questions["type"] = column[0].find('strong').text.split('-')[1].split(' ')[1]
        # Extract the title
        questions["number"] = column[0].find('strong').text.split('-')[1].split(' ')[2]
        # Extract legislature
        questions["legislature"] = column[0].find('strong').text.split('-')[0].split(' ')[0]
        # Extract name of person who asked the question
        questions["name"] = column[1].find('strong').text
        # Extract title
        questions["title"] = column[1].find('em').text
        # Extract concerned ministry
        questions["ministry"] = column[1].find_all('strong')[-1].text
        # Extract asked Date
        questions["asked_date"] = column[2].find('strong').text
        # Extract answered Date
        if column[2].find('form'):
            questions["answered_date"] = 'en attente de réponse'
        else:
            questions["answered_date"] = column[2].find_all('strong')[-1].text
        
        # Store in DB
        question = Questions(questions)
        session.add(question)
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
        