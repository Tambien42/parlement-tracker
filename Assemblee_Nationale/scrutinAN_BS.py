import requests, re
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Scrutins(Base):
    __tablename__ = 'scrutins'

    ids = Column("id", Integer, primary_key=True)
    number = Column("number", Integer)
    date = Column("date", DATE)
    object = Column("object", TEXT)
    votes_for = Column("votes_for", Integer)
    votes_against = Column("votes_against", Integer)
    votes_abstention = Column("votes_abstention", Integer)
    non_votants = Column("non_votants", Integer)
    total_votes = Column("total_votes", Integer)
    pourcentage_abstention = Column("pourcentage_abstention", Float)
    group_vote = Column("group_vote", JSON)

    def __init__(self, number, date, object, votes_for, votes_against, votes_abstention, non_votants, total_votes, pourcentage_abstention, group_vote):
        self.number = number
        self.date = date
        self.object = object
        self.votes_for = votes_for
        self.votes_against = votes_against
        self.votes_abstention = votes_abstention
        self.non_votants = non_votants
        self.total_votes = total_votes
        self.pourcentage_abstention = pourcentage_abstention
        self.group_vote = group_vote
    
    def __repr__(self):
        return f'(Scrutins n {self.number})'


def scrape_page(url):
    # Make a request to the webpage
    response = requests.get(url)
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find the table containing the data
    table = soup.find('table', class_='scrutins')
    # Find all the rows in the table
    t = table.find('tbody')
    rows = t.find_all('tr')
    
    # Iterate over the rows
    for row in rows:
        # Find the cells in the row
        cells = row.find_all('td')

        # Extract the data from the cells
        number = re.sub("[^0-9]", "", cells[0].text)
        date = datetime.strptime(cells[1].text, "%d/%m/%Y")
        obj = cells[2].text
        votes_for = cells[3].text
        votes_against = cells[4].text
        votes_abstention = cells[5].text

        # Extract url Analyse du scrutin
        url_analyse_scrutin = 'https://www2.assemblee-nationale.fr' + cells[2].find_all('a')[-1]['href']
        r = requests.get(url_analyse_scrutin)
        s = BeautifulSoup(r.content, 'html.parser')
        div = s.find_all('div', class_='Non-votant')
        list_nv = []
        # Extract Number of Non Votant
        non_votants = 0
        for d in div:
            non_votants = non_votants + int(d.find('p').find('b').text)
            list_nv.append(d.find('ul').text.strip().split('(')[0].replace('\xa0', ' ').strip())

        # Calculation
        total_votes = int(votes_for) + int(votes_against) + int(votes_abstention) + int(non_votants)
        pourcentage_participation = float((total_votes / 577) * 100)
        pourcentage_abstention = 100 - pourcentage_participation
        
        # Extract group votes
        group_vote = {}
        groups = s.find('ul', {"id": "index-groupe"}).find_all('li')
        for g in groups:
            gr = g.find_all('span')
            group = gr[0].text
            nb_votes = 0
            if len(gr) != 1:
                for n in gr[1:]:
                    nb_votes = nb_votes + int(n.find('b').text)
            group_vote[group] = nb_votes
        
        # Store in DB
        scrutins = Scrutins(int(number), date, obj, votes_for, votes_against, votes_abstention, non_votants, total_votes, pourcentage_abstention, group_vote)
        session.add(scrutins)
        session.commit() 

# SQLAlchemy
engine = create_engine('sqlite:///votes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Start with the first page
url = 'https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/16'

# Scrape the first page
scrape_page(url)

# Loop until there are no more pages
while True:
    # Make a request to the webpage
    response = requests.get(url)
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find the link to the next page
    pagination = soup.find('div', class_='pagination-bootstrap')
    next_page_link = pagination.find_all('li')[-1].find('a')

    # Check if there is a next page
    if next_page_link:
        # If there is a next page, follow the link
        url = 'https://www2.assemblee-nationale.fr' + next_page_link['href']
        # Scrape the next page
        scrape_page(url)
    else:
        # If there are no more pages, break the loop
        break
