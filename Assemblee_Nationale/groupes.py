import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
import re
import time
from urllib.parse import unquote
import os
import subprocess
from pprint import pprint

# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Groupes(Base):
    __tablename__ = 'groupes'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    nom: Mapped[str]
    groupe_id: Mapped[str]
    date: Mapped[datetime]
    president: Mapped[str]
    membres: Mapped[str]
    apparentes: Mapped[str]

    def __repr__(self):
        return f"<Groupes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')
    list = soup.find_all("div", attrs={"data-organe-id" : re.compile(r".*")})

    for groupe in list:
        nom = groupe.find("span").text
        url_groupe = "https://www2.assemblee-nationale.fr/instances/fiche/OMC_" + groupe["data-organe-id"] + "/null/ajax/1/name/Composition/legislature/17"
        parse_groupes(url_groupe, nom)

#TODO sort db data and website data?
def parse_groupes(url, nom):
    command = 'curl "' + url + '"'
    response = subprocess.check_output(command, shell=True)
    soup = BeautifulSoup(response, 'html.parser')
    list = soup.find_all("h3")
    nom = nom
    today = date.today()
    legislature = url.split("/")[-1]
    groupe_id = url.split("_")[-1].split("/")[0]
    president = []
    membres = []
    apparentes = []
    for status in list:
        poste = status.text
        if re.match(r"^Président", poste):
            deputes = status.find_next("ul").find_all("a", {"class": "instance-composition-nom"})
            for depute in deputes:
                president.append(depute["href"].split("_")[-1])
        if poste == "Membres" or poste == "Députés non-inscrits":
            deputes = status.find_next("ul").find_all("a", {"class": "instance-composition-nom"})
            for depute in deputes:
                membres.append(depute["href"].split("_")[-1])
        if re.match(r"^Apparent", poste):
            deputes = status.find_next("ul").find_all("a", {"class": "instance-composition-nom"})
            for depute in deputes:
                apparentes.append(depute["href"].split("_")[-1])
    
    results = check_db(nom, legislature, groupe_id)
    
    if results[0] == ', '.join(map(str, president)) and results[1] == ', '.join(map(str, membres)) and results[2] == ', '.join(map(str, apparentes)):
        return

    session = Session()
    groupe = Groupes(
        nom=nom,
        groupe_id=groupe_id,
        legislature=legislature,
        date=today,
        president = ','.join(map(str, president)),
        membres = ','.join(map(str, membres)),
        apparentes = ','.join(map(str, apparentes))
    )
    session.add(groupe)
    session.commit()
    session.close()

def check_db(nom, legislature, groupe_id):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.president, Groupes.membres, Groupes.apparentes)
        .where(Groupes.legislature == legislature)
        .where(Groupes.groupe_id == groupe_id)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).fetchall()

    if len(results) != 0:
        last = results[0]
        return last
    return False

def fetch_url(url, retries=10, timeout=30.0):
    attempt = 0
    while attempt < retries:
        try:
            response = httpx.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
        except (httpx.TimeoutException, httpx.HTTPStatusError) as err:
            attempt += 1
            print(f"Request to {url} timed out. Attempt {attempt} of {retries} failed: {err}. Retrying...")
            time.sleep(2)  # Wait before retrying
        except httpx.RequestError as exc:
            attempt += 1
            print(f"An error occurred while requesting {exc.request.url!r}. Attempt {attempt} of {retries}. Retrying...")
            time.sleep(2)  # Wait before retrying
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def get_president(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.president)
        .where(Groupes.nom == nom)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    president = ''
    if len(results) !=  0:
        president = results[0]
    return president

def get_membres(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.membres)
        .where(Groupes.nom == nom)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    membres = ''
    if len(results) !=  0:
        membres = results[0]
    return membres

def get_affilies(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.affilies)
        .where(Groupes.nom == nom)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    affilies = ''
    if len(results) !=  0:
        affilies = results[0]
    return affilies

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = "https://www.assemblee-nationale.fr/dyn/les-groupes-politiques"
    parse(url)

if __name__ == "__main__":
    main()