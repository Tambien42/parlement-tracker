import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import time
import re
import os
import json
from sqlalchemy import create_engine, select, or_, func
from sqlalchemy.orm import Session, declarative_base, Mapped, mapped_column

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)

class DeputesEuro(Base):
    __tablename__ = 'deputes_europeens'

    id: Mapped[int] = mapped_column(primary_key=True)
    depute_id: Mapped[str]
    en_cours: Mapped[int]
    legislature: Mapped[int]
    nom: Mapped[str]
    prenom: Mapped[str]
    photo: Mapped[str] = mapped_column(nullable=True)
    date_naissance: Mapped[datetime] = mapped_column(nullable=True)
    lieu_naissance: Mapped[str] = mapped_column(nullable=True)
    date_election: Mapped[datetime] = mapped_column(nullable=True)
    date_fin_mandat: Mapped[datetime] = mapped_column(nullable=True)
    raison_fin: Mapped[str] = mapped_column(nullable=True)
    pays: Mapped[str]
    groupe_pays: Mapped[str] = mapped_column(nullable=True)
    groupe: Mapped[str] = mapped_column(nullable=True)
    mail: Mapped[str] = mapped_column(nullable=True)
    twitter: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<DeputesEuro(id={self.id}, nom={self.nom})>"

class Presence(Base):
    __tablename__ = 'presence_parlement_euro'

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime]
    legislature: Mapped[int]
    type: Mapped[str] = mapped_column(nullable=True)
    url: Mapped[str] = mapped_column(nullable=True)
    presents: Mapped[str] = mapped_column(nullable=True)
    excuses: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<Presence(id={self.id}, nom={self.nom})>"

Base.metadata.create_all(engine)

def fetch_url(url, retries=10, timeout=30.0):
    attempt = 0
    while attempt < retries:
        try:
            # Make the HTTP request
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)
            return response  # Return the successful response
        except httpx.HTTPStatusError as err:
            # Check if the error is a 404 Not Found
            if err.response.status_code == 404:
                print(f"Received 404 for {url}. Returning 404.")
                return 404  # Return 404 if it's a 404 error
            else:
                attempt += 1
                print(f"Request to {url} failed with status {err.response.status_code}. Attempt {attempt} of {retries}. Retrying...")
                time.sleep(2)  # Wait before retrying
        except (httpx.TimeoutException, httpx.RequestError) as err:
            # Handle other exceptions like timeouts or general request errors
            attempt += 1
            print(f"Request to {url} encountered an error: {err}. Attempt {attempt} of {retries}. Retrying...")
            time.sleep(2)  # Wait before retrying

    print(f"Failed to fetch {url} after {retries} attempts.")
    return None  # Return None after all retries are exhausted

def parse(url):
    content = fetch_url(url)

    # Parse the JSON data
    data = content.json()

    for session in data["sessionCalendar"]:
        if session["url"]:
            date = session["day"] + "-" + session["month"] + "-" + session["year"]
            date_session = datetime.strptime(date, "%d-%m-%Y")
            type = session["type"]
            url = session["url"]
            print(url)
            # Regular expression to capture the digits after 'PV-'
            pattern = r'PV-(\d+)'
            match = re.search(pattern, url)
            legislature = match.group(1)

            print(f"date: {date} type: {type} url: {url}")
            # if date and type in db modify with url if exists
            content = fetch_url(url.replace("TOC", "ATT"))
            presents = []
            excuses = []
            if content != 404:
                soup = BeautifulSoup(content, 'html.parser')
                paragraphs = soup.find_all("p", {"class", "contents"})
                if paragraphs:
                    presents = paragraphs[1].text.split(", ")
                    excuses = paragraphs[3].text.split(", ")

            with Session(engine) as session:
                date_presence = session.query(Presence).filter(Presence.date == date_session, Presence.legislature == legislature).first()
                if date_presence:
                    print("Already in DB.")
                    continue
                    #return
                
                # Store data in the database
                depute = Presence(
                    date=date_session,
                    legislature=legislature,
                    type=type,
                    url=url,
                    presents=','.join(map(str, presents)),
                    excuses=','.join(map(str, excuses)),
                )
                
                session.add(depute)  # Use merge to update or insert
                session.commit()
                session.close() 


            # TODO replace name by depute_id
            # not find in db javier moreno sánchez, cristian-silviu buşoi, jozef mihál, andrás gyürk
            # for depute in excuses:
            #     with Session(engine) as session:
            #         print("--------------------------------------------------")
            #         print(depute.lower())
            #         results = session.query(DeputesEuro).filter(
            #                     DeputesEuro.legislature == legislature,
            #                     or_(
            #                         func.lower(DeputesEuro.prenom.op('||')(' ') .op('||')(DeputesEuro.nom)) == depute.lower(),  # Full name match
            #                         func.lower(DeputesEuro.nom) == depute.lower()  # Last name match
            #                     )
            #                 ).all()
            #         if results:
            #             for r in results:
            #                 print(r)
            #         else:
            #             print("NOT FOUND")


            # for p in paragraphs:
            #     print(p.text.split(","))
            # count = 0
            # for p in paragraphs:
            #     if len(p.text.split(",")) == 1:
            #         continue
            #     count = count + len(p.text.split(","))
            # percent = (count / 720) * 100
            # print(percent)


def parse_text(url):
    pass
    

def main():
    # Example URL (replace with target URL)
    #url = "https://www.europarl.europa.eu/plenary/fr/votes.html?tab=votes"
    legislature = 10 # between 5 and 10
    url = "https://www.europarl.europa.eu/plenary/fr/ajax/getSessionCalendar.html?family=PV&termId=" + str(legislature)
    parse(url)

if __name__ == "__main__":
    main()