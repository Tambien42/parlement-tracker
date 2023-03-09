import re
from sqlalchemy import Column, Integer, String, DATE, TEXT, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from soup import make_request, next_page

Base = declarative_base()

class Scrutins(Base):
    __tablename__ = 'scrutins'

    #ids = Column("id", Integer, primary_key=True)
    number = Column("number", Integer, primary_key=True, autoincrement=False)
    date = Column("date", DATE)
    object = Column("object", TEXT)
    votes_for = Column("votes_for", Integer)
    votes_against = Column("votes_against", Integer)
    votes_abstention = Column("votes_abstention", Integer)
    non_votants = Column("non_votants", Integer)
    total_votes = Column("total_votes", Integer)
    pourcentage_abstention = Column("pourcentage_abstention", Float)
    group_vote = Column("group_vote", TEXT)

    def __init__(self, data):
        self.number = data['number']
        self.date = data['date']
        self.object = data['object']
        self.votes_for = data['votes_for']
        self.votes_against = data['votes_against']
        self.votes_abstention = data['votes_abstention']
        self.non_votants = data['non_votants']
        self.total_votes = data['total_votes']
        self.pourcentage_abstention = data['pourcentage_abstention']
        self.group_vote = data['group_vote']
    
    def __repr__(self):
        return f'(Scrutins n {self.number} {self.object})'

# Scrape Scrutins Data
def scrutins():
    # Start with the first page
    url = 'https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/16'
    
    scrutins = {}
    while True:
        # Parse the HTML content
        soup = make_request(url)
        # Find the table containing the data
        table = soup.find('table', class_='scrutins')
        # Find all the rows in the table
        rows = table.find('tbody').find_all('tr')

        for row in rows:
            # Find all cells in a row
            cells = row.find_all('td')
            # Extract the votes data from the cells
            scrutins['number'] = re.sub("[^0-9]", "", cells[0].text)
            scrutins['date'] = datetime.strptime(cells[1].text, "%d/%m/%Y")
            print(f'date: {scrutins["date"]}')
            scrutins['object'] = re.sub(r'\[.*?\]', '', cells[2].text).strip()
            scrutins['votes_for'] = cells[3].text
            scrutins['votes_against'] = cells[4].text
            scrutins['votes_abstention'] = cells[5].text

            # Extract scrutin data from analysis url
            analyse_url = 'https://www2.assemblee-nationale.fr' + cells[2].find_all('a')[-1]['href']
            analyse = make_request(analyse_url)
            # Extract Number and name of present deputes but Non Votant
            nv = analyse.find_all('div', class_='Non-votant')
            list_non_votant = ""
            scrutins['non_votants'] = 0
            for i in nv:
                scrutins['non_votants'] = scrutins['non_votants'] + int(i.find('p').find('b').text)
                list_non_votant = list_non_votant + ', ' + i.find('ul').text.strip().split('(')[0].replace('\xa0', ' ').strip()
            
            # Extract votes by group
            scrutins['group_vote'] = ""
            groups = analyse.find('ul', {"id": "index-groupe"}).find_all('li')
            for g in groups:
                gr = g.find_all('span')
                group = gr[0].text
                nb_votes = 0
                if len(gr) != 1:
                    for n in gr[1:]:
                        nb_votes = nb_votes + int(n.find('b').text)
                scrutins['group_vote'] = scrutins['group_vote'] + ' ;' + group + ',' + str(nb_votes)

            # Calculations
            scrutins['total_votes'] = int(scrutins['votes_for']) + int(scrutins['votes_against']) + int(scrutins['votes_abstention']) + int(scrutins['non_votants'])
            pourcentage_participation = float((scrutins['total_votes'] / 577) * 100)
            scrutins['pourcentage_abstention'] = round(100 - pourcentage_participation, 2)

        # Get next page
        url = next_page(soup)
        # Check if there is a next page
        if url is None:
            break
