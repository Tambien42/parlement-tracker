import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
import re
import os
import time
from urllib.parse import unquote
from pprint import pprint
from urllib.parse import urlparse, parse_qs
import requests
from playwright.sync_api import sync_playwright, TimeoutError, Error

legislature = 17
# Global variable
# legislature = 11
# url_fonctions = "https://www.assemblee-nationale.fr/11/tribun/xml/bureau_assemblee.asp"
# legislature = 12
# url_fonctions = "https://www.assemblee-nationale.fr/12/tribun/xml/bureau_assemblee.asp"
# legislature = 13
# url_fonctions = "https://www.assemblee-nationale.fr/13/tribun/xml/bureau_assemblee.asp"
# legislature = 14
# url_fonctions ="https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/25145"
# legislature = 15
# url_fonctions = "https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/42363"
# legislature = 16
# url_fonctions = "https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/119106"
# legislature = 17
# url_fonctions = "https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/189123"


# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class AN_Fonctions(Base):
    __tablename__ = 'AN_fonctions'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    president: Mapped[str]
    vice_presidents: Mapped[str]
    questeurs: Mapped[str]
    secretaires: Mapped[str]
    date: Mapped[datetime]

    def __repr__(self):
        return f"<AN_Fonctions(id={self.id}, legislature={self.legislature}, president={self.president})>"

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

def format_date(str):
    # Replace French names with English names
    for french, english in french_to_english.items():
        str = str.replace(french, english)
    # Define the date format with English names
    date_format = "%d %B %Y"
    # Convert the date string to a datetime object
    date_object = datetime.strptime(str, date_format)
    return date_object

def check_fonctions(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(AN_Fonctions.president, AN_Fonctions.vice_presidents, AN_Fonctions.questeurs, AN_Fonctions.secretaires)
        .where(AN_Fonctions.legislature == legislature)
        .order_by(AN_Fonctions.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).fetchall()

    if len(results) != 0:
        last = results[0]
        return last
    return None

def parse_fonctions(url):
    # Initialize Playwright
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch()
        # Create a new page
        page = browser.new_page()
        page.goto(url)
        # Wait for the AJAX content to load
        page.wait_for_selector('#composition')
        # Get the page content
        page_content = page.content()
        soup = BeautifulSoup(page_content, 'html.parser')

        fonctions = soup.find("div", {"id": "composition"}).find_all("h3")
    
        president = []
        vicep = []
        questeurs = []
        secretaires = []
        for f in fonctions:
            if re.match(r"^Président", f.text):
                president.append(f.parent.find("a")["href"].split("_")[-1])
            if re.match(r"^Vice", f.text):
                vps = f.parent.find_all("a")
                for vp in vps:
                    vicep.append(vp["href"].split("_")[-1])
            if re.match(r"^Quest", f.text):
                qs = f.parent.find_all("a")
                for q in qs:
                    questeurs.append(q["href"].split("_")[-1])
            if re.match(r"^Secrétaires", f.text):
                secs = f.parent.find_all("a")
                for sec in secs:
                    secretaires.append(sec["href"].split("_")[-1])

        results = check_fonctions(legislature)
        if (results and
            results[0] == ','.join(map(str, president))  and 
            results[1] == ','.join(map(str, vicep)) and 
            results[2] == ','.join(map(str, questeurs)) and 
            results[3] == ','.join(map(str, secretaires))):
            print("no changes in Bureau")
            return

        # # open a new database session
        session = Session()
        depute = AN_Fonctions(
            legislature=legislature,
            president=','.join(map(str, president)),
            vice_presidents=','.join(map(str, vicep)),
            questeurs =  ','.join(map(str, questeurs)),
            secretaires = ','.join(map(str, secretaires)),
            date = date.today()
        )
        session.add(depute)
        session.commit()
        session.close() 
        
        
        browser.close()

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    # get fonctions du bureau de l'an
    url  = "https://www2.assemblee-nationale.fr/" + str(legislature) + "/le-bureau-de-l-assemblee-nationale"
    parse_fonctions(url)
    #parse_fonctions(url_fonctions)

if __name__ == "__main__":
    main()