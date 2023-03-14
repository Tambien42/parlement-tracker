import re
from sqlalchemy import create_engine, Column, Integer, String, DATE, TEXT
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from soup import make_request, next_page
import locale

# Set the locale to French
# Needed to translate date
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# create a database connection
engine = create_engine('sqlite:///votes.db')
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Law_proposals(Base):
    __tablename__ = 'law_proposals'

    number = Column("number", Integer, primary_key=True)
    title = Column("title", String)
    link = Column("link", String)
    date = Column("date", DATE)
    author = Column("author", TEXT)
    cosigner = Column("cosigner", TEXT)

    def __init__(self, law):
        self.number = law["number"]
        self.title = law["title"]
        self.link = law["link"]
        self.date = law["date"]
        self.author = law["author"]
        self.cosigner = law["cosigner"]

    def __repr__(self):
        return f'(Loi {self.number} {self.title})'

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
    law = session.query(Model).filter_by(number=data["number"]).first()
    if law:
        return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

def law_proposals():
    url = 'https://www2.assemblee-nationale.fr/documents/liste/(type)/propositions-loi'

    data = {}
    while True:
        soup = make_request(url)
        list = soup.find('ul', class_='liens-liste').find_all('li', recursive=False)
        for law in list:
            # Extract the number of the proposal
            data['number'] = law.find('h3').text.split('-')[-1].replace(u'\xa0', ' ').split(' ')[-1]
            # Extract title
            title = law.find('h3').text
            data['title'] = title.split('-')[0]
            if len(title.split('-')) > 2:
                title_array = title.split('-')[:-1]
                data['title'] = '-'.join(title_array)
            # Extract link
            data['link'] = law.find('ul').find_all('li')[-1].find('a')['href']
            # Extract date
            string = law.find('ul').find_all('li')[0].text.strip()
            # Define regular expression pattern to match the date
            pattern = r"(\d{1,2}\s\w+\s\d{4})"
            # Find the date in the string
            match = re.search(pattern, string)
            if match:
                date = match.group(1)
                data['date'] = datetime.strptime(date, "%d %B %Y")
            else:
                # handle the case where the regex didn't match
                data['date'] = None
            
            # Extract author and cosigner of law proposals
            url_dossier = law.find_all("li")[-2].find("a")["href"]
            signer_page = make_request(url_dossier)
            signer = signer_page.find('div', class_='carrousel-auteurs-rapporteurs')
            data['author'] = ''
            data['cosigner'] = ''
            if signer != None:
                data['author'] = signer.find_all('li')[0].text.strip()
                for author in signer.find_all('li')[1:]:
                    data['author'] = data['author'] + ', ' + author.find("p", class_="nom-personne").text.strip()
                
                if signer.find('a', {'data-toggle':'modal'}):
                    modal = signer_page.find('div', id='cosignataires').find('div', id="cosignataires-liste").find_all('a')
                    data['cosigner'] = modal[0].text.strip()
                    for cosign in modal[1:]:
                        data['cosigner'] = data['cosigner'] + ', ' + cosign.text.strip()
            
            save_to_database(data, Law_proposals)

        # Get next page
        url = next_page(soup)
        if url is None:
            break       
