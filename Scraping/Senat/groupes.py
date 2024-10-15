import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from pprint import pprint
from datetime import datetime, date
import time
import re
import sqlalchemy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# Global Variable
sessionp = "2024-2025"

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class Groupes_Senat(Base):
    __tablename__ = 'groupes_senat'

    id: Mapped[int] = mapped_column(primary_key=True)
    session: Mapped[str]
    nom: Mapped[str]
    groupe_id: Mapped[str]
    date: Mapped[datetime]
    membres: Mapped[str]

    def __repr__(self):
        return f"<Groupes(id={self.id}, session={self.session}, nom={self.nom})>"

Base.metadata.create_all(engine)

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

def check_db(sessionp, groupe_id):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes_Senat.membres)
        .where(Groupes_Senat.session == sessionp)
        .where(Groupes_Senat.groupe_id == groupe_id)
        .order_by(Groupes_Senat.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).fetchall()

    if len(results) != 0:
        last = results[0]
        return last
    return None

def extract_id(text):
    # Regex pattern to extract digits after "n°"
    match = re.search(r'(\d+[a-zA-Z])', text, re.IGNORECASE)
    
    if match:
        return match.group(1)  # Return the captured number
    else:
        return None  # Return None if no match is found

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    groupes = soup.find("div", {"class": "table-responsive"}).find_all("a")
    for groupe in groupes:
        url_g = "https://www.senat.fr/senateurs/" + groupe["href"]
        parse_groupe(url_g)

def parse_groupe(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    name = soup.find("h1").text.strip().split()
    remaining_words = name[0:]
    if name[0] == "Groupe":
        remaining_words = name[1:]
        if name[1] == "du":
            remaining_words = name[2:]
    nom = ' '.join(remaining_words)
    today = date.today()
    groupe_id = url.split("/")[-1].split(".")[0]
    lien = url
    a_list = soup.find("div", {"class": "page-content"}).find("ul", {"class": "list-links"}).find_all("a")
    list = []
    for a in a_list:
        list.append(extract_id(a["href"]))
    
    results = check_db(sessionp, groupe_id)

    if results and results[1] == ','.join(map(str, list)):
        return

    session = Session()
    groupe = Groupes_Senat(
        nom=nom,
        groupe_id=groupe_id,
        session=sessionp,
        date=today,
        membres = ','.join(map(str, list)),
    )
    session.add(groupe)
    session.commit()
    session.close()

    
def main():
    # Start URL
    url = "https://www.senat.fr/senateurs/grp.html"
    parse(url)

if __name__ == "__main__":
    main()