import re
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float
from sqlalchemy.ext.declarative import declarative_base
from soup import make_request, next_page
from datetime import datetime

Base = declarative_base()

class Questions(Base):
    __tablename__ = 'questions'

    ids = Column("id", String, primary_key=True)
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
        self.ids = question["id"]
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

def questions():
    # Parse the HTML content
    url = 'https://www2.assemblee-nationale.fr/recherche/resultats_questions/'

    questions = {}
    while True:
        soup = make_request(url)
        # Find all the rows in the table
        rows = soup.find('table').find('tbody').find_all('tr')
        for row in rows:
            column = row.find_all('td')
            # ID type of quetion - number of the question - legislature
            id = column[0].find('strong').text.split('-')
            question = id[1]
            questions["legislature"]= re.findall(r'\d+', id[0])[0]
            questions["id"] = question.strip().replace(' ', '-') + '-' + questions["legislature"]
            # Extract Link
            questions["link"] = column[0].find('a')['href']
            # Extract the type of question
            questions["type"] = column[0].find('strong').text.split('-')[1].split(' ')[1]
            # Extract the number
            questions["number"] = column[0].find('strong').text.split('-')[1].split(' ')[2]
            # Extract name of person who asked the question
            questions["name"] = column[1].find('strong').text
            # Extract title
            questions["title"] = column[1].find('em').text
            # Extract concerned ministry
            questions["ministry"] = column[1].find_all('strong')[-1].text
            asked_date = column[2].find('strong').text
            questions["asked_date"] = datetime.strptime(asked_date, "%d/%m/%Y")
            # Extract answered Date
            if column[2].find('form'):
                questions["answered_date"] = 'en attente de réponse'
            else:
                answered_date = column[2].find_all('strong')[-1].text
                questions["answered_date"] = datetime.strptime(answered_date, "%d/%m/%Y")
    
        # Get next page
        url = next_page(soup)
        # Check if there is a next page
        if url is None:
            break
