import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime
import re
import time
from urllib.parse import unquote
from pprint import pprint

# Mapping French day and month names to English
french_to_english = {
    # Days of the week
    "lundi": "Monday",
    "mardi": "Tuesday",
    "mercredi": "Wednesday",
    "jeudi": "Thursday",
    "vendredi": "Friday",
    "samedi": "Saturday",
    "dimanche": "Sunday",
    
    # Months of the year
    "janvier": "January",
    "février": "February",
    "mars": "March",
    "avril": "April",
    "mai": "May",
    "juin": "June",
    "juillet": "July",
    "août": "August",
    "septembre": "September",
    "octobre": "October",
    "novembre": "November",
    "décembre": "December",

    # Day
    "1er": "1"
}

# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Scrutins(Base):
    __tablename__ = 'scrutins'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    numero: Mapped[int]
    titre: Mapped[str]
    date_seance: Mapped[datetime]
    lien: Mapped[str]
    votes_pour: Mapped[int]
    votes_contre: Mapped[int]
    votes_abstention: Mapped[int]
    non_votants: Mapped[int]

    def __repr__(self):
        return f"<Scrutins(id={self.id}, legislature={self.legislature}, numero={self.numero})>"

def parse(url):
    while True:
        client = httpx.Client()
        response = httpx.get(url)
        soup = BeautifulSoup(response, 'html.parser')
        list = soup.find("section", {"class": "an-section"}).find("ul", {"class": "_centered"}).find_all("a", {"class": "h6"})
        
        for item in list:
            if check_db(item['href'].split("/")[-3], item['href'].split("/")[-1]) == True:
                print("already in db")
                return
        
            url_scrutin = "https://www.assemblee-nationale.fr" + item["href"]
            parse_scrutins(unquote(url_scrutin))

        # Loop through all pages
        pagination = soup.find('div', class_='an-pagination')
        next_page_link = pagination.find_all('div')[-1].find('a')

        if next_page_link:
            url = 'https://www2.assemblee-nationale.fr' + next_page_link['href']
        else:
            break

def parse_scrutins(url):
    response = httpx.get(url, timeout=30.0)
    time.sleep(1)
    s = BeautifulSoup(response, 'html.parser')

    numero = url.split("/")[-1]
    legislature = url.split("/")[-3]
    titre = s.find("p", {"class": "h6"}).text
    pprint(numero)
    if s.find("div", {"class": "_centered-text"}).find("h2", {"class": "h4"}).text  != "":
        date = s.find("div", {"class": "_centered-text"}).find("h2", {"class": "h4"}).text.split("du")[-1].strip()
         # Replace French names with English names
        for french, english in french_to_english.items():
            date = date.replace(french, english)
        # Define the date format with English names
        date_format = "%A %d %B %Y"
        # Convert the date string to a datetime object
        date_object = datetime.strptime(date, date_format)
    else:
        date_object = get_date(int(numero) + 1)   
    vote_pour = 0
    vote_contre = 0
    abstention = 0
    if s.find("ul", {"class": "votes-list"}):
        vote_pour = int(s.find("ul", {"class": "votes-list"}).find("li").find('b').text)
        vote_contre = int(s.find("ul", {"class": "votes-list"}).find_all("li")[1].find('b').text)
        abstention = int(s.find("ul", {"class": "votes-list"}).find_all("li")[-1].find('b').text)
    elif s.find("span", text=lambda x: x and "Pour l’adoption :" in x):
        vote_pour = int(s.find("span", text=lambda x: x and "Pour l’adoption :" in x).find("b").text)
    nvs = s.find("section", {"class": "an-section"}).find("div", {"class": "_size-1"}).find_all("span", text=re.compile('Non votant')) 
    non_votant = 0
    for nv in nvs:
        non_votant = non_votant + int(nv.text.split(":")[-1])
    
    # open a new database session
    session = Session()
    scrutin = Scrutins(
        numero=numero,
        legislature=legislature,
        titre=titre,
        date_seance=date_object,
        lien=url,
        votes_pour=vote_pour,
        votes_contre=vote_contre,
        votes_abstention=abstention,
        non_votants=non_votant

    )
    session.add(scrutin)
    session.commit()
    session.close()


def check_db(legislature, numero):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Scrutins.numero)
        .where(Scrutins.legislature == legislature)
        .where(Scrutins.numero == numero)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        return True
    return False


def get_date(numero):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Scrutins.date_seance)
        .where(Scrutins.numero == numero)
    )

    last = 0
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        last = results[0]
    session.close()
    pprint(last)
    return last

def get_last_scrutin(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Scrutins.numero)
        .where(Scrutins.legislature == legislature)
        .order_by(Scrutins.numero.desc())
    )

    last = 0
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        last = results[0]
    session.close()
    pprint(last)
    return last

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)

    #Start URL
    url = "https://www.assemblee-nationale.fr/dyn/16/scrutins"
    parse(url)

if __name__ == "__main__":
    main()
