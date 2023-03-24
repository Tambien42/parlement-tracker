import re
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from soup import make_request, next_page
from datetime import datetime

# create a database connection
engine = create_engine('sqlite:///votes.db')
Session = sessionmaker(bind=engine)

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
    asked_date = Column("asked_date", Date)
    answered_date = Column("answered_date", Date)

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

#Create the table in the database
Base.metadata.create_all(engine)

def save_to_database(data: dict, Model):
    """
    Save data to a database using the provided session and model.
    :param data: dictionary containing data to be saved
    :param model: SQLAlchemy model class
    :return: None
    """
    # open a new database session
    session = Session()
    # retrieve the row you want to check by its id and sort it by date
    question = session.query(Questions).filter_by(ids=data["id"]).first()
    if question:
        if question.answered_date != data['answered_date']:
            question.answered_date = data['answered_date']

        return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

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
            questions["id"] = column[0].find('a')['href'].split('/')[-1].split('.')[0]
            questions["legislature"]= questions["id"].split('-')[0]
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
                questions["answered_date"] = None
            else:
                answered_date = column[2].find_all('strong')[-1].text
                questions["answered_date"] = datetime.strptime(answered_date, "%d/%m/%Y")

            save_to_database(questions, Questions)
        # Get next page
        url = next_page(soup)
        # Check if there is a next page
        if url is None:
            break

