import re
from sqlalchemy import create_engine, Column, Integer, DATE, TEXT, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from soup import make_request, next_page

# create a database connection
engine = create_engine('sqlite:///votes.db')
Session = sessionmaker(bind=engine)

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
    scrutin = session.query(Model).filter_by(number=data["number"]).first()
    if scrutin:
        return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

# Scrape Scrutins Data
#TODO function do put non votant status in fiche depute
def scrutins(url = ''):
    try:
        # Start with the first page
        if url == '':
            url = 'https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/16'
        
        data = {}
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
                data['number'] = re.sub("[^0-9]", "", cells[0].text)
                data['date'] = datetime.strptime(cells[1].text, "%d/%m/%Y")
                data['object'] = re.sub(r'\[.*?\]', '', cells[2].text).strip()
                data['votes_for'] = cells[3].text
                data['votes_against'] = cells[4].text
                data['votes_abstention'] = cells[5].text

                # Extract scrutin data from analysis url
                analyse_url = 'https://www2.assemblee-nationale.fr' + cells[2].find_all('a')[-1]['href']
                analyse = make_request(analyse_url)
                # Extract Number and name of present deputes but Non Votant
                nv = analyse.find_all('div', class_='Non-votant')
                list_non_votant = ""
                data['non_votants'] = 0
                for i in nv:
                    data['non_votants'] = data['non_votants'] + int(i.find('p').find('b').text)
                    list_non_votant = list_non_votant + ', ' + i.find('ul').text.strip().split('(')[0].replace('\xa0', ' ').strip()
                
                # Extract votes by group
                data['group_vote'] = ""
                groups = analyse.find('ul', {"id": "index-groupe"}).find_all('li')
                for g in groups:
                    gr = g.find_all('span')
                    group = gr[0].text
                    nb_votes = 0
                    if len(gr) != 1:
                        for n in gr[1:]:
                            nb_votes = nb_votes + int(n.find('b').text)
                    data['group_vote'] = data['group_vote'] + ' ,' + group + ':' + str(nb_votes)
                tmp = data['group_vote'].split(';')
                tmp.pop(0)
                data['group_vote'] = ';'.join(tmp)

                # Calculations
                data['total_votes'] = int(data['votes_for']) + int(data['votes_against']) + int(data['votes_abstention']) + int(data['non_votants'])
                pourcentage_participation = float((data['total_votes'] / 577) * 100)
                data['pourcentage_abstention'] = round(100 - pourcentage_participation, 2)
                save_to_database(data, Scrutins)

            # Get next page
            url = next_page(soup)
            # Check if there is a next page
            if url is None:
                break
    
    except Exception as e:
        print(f'An error occurred, restarting scrutins scraping...')
        scrutins(url)

scrutins()
