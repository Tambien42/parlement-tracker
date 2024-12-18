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

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class S_Fonctions(Base):
    __tablename__ = 'S_fonctions'

    id: Mapped[int] = mapped_column(primary_key=True)
    session: Mapped[str]
    president: Mapped[str]
    vice_presidents: Mapped[str]
    questeurs: Mapped[str]
    secretaires: Mapped[str]
    date: Mapped[datetime]

    def __repr__(self):
        return f"<S_Fonctions(id={self.id}, session={self.session}, president={self.president})>"

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

def format_date(str):
    date_format = "%d %B %Y"
    # Convert the date string to a datetime object
    date_object = datetime.strptime(str, date_format)
    return date_object

def check_fonctions(sessionp):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(S_Fonctions.president, S_Fonctions.vice_presidents, S_Fonctions.questeurs, S_Fonctions.secretaires)
        .where(S_Fonctions.session == sessionp)
        .order_by(S_Fonctions.date.desc())
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

    h2 = soup.find_all("h2")
    today = date.today()
    # 04 octobre 2024 

    sessionp = "2024-2025"
    president = []
    vps = []
    questeurs = []
    secretaires = []
    for fonction in h2:
        if fonction.text.strip() == "Président du Sénat":
            a = fonction.find_next_sibling("ul").find_all("a")
            for m in a:
                president.append(extract_id(m["href"]))
        if fonction.text == "Vice-présidents du Sénat":
            a = fonction.find_next_sibling("ul").find_all("a")
            for m in a:
                vps.append(extract_id(m["href"]))
        if fonction.text == "Questeurs du Sénat":
            a = fonction.find_next_sibling("ul").find_all("a")
            for m in a:
                questeurs.append(extract_id(m["href"]))
        if fonction.text == "Secrétaires du Sénat":
            a = fonction.find_next_sibling("ul").find_all("a")
            for m in a:
                secretaires.append(extract_id(m["href"]))
    
    results = check_fonctions(sessionp)
    if (results and
        results[0] == ','.join(map(str, president))  and 
        results[1] == ','.join(map(str, vps)) and 
        results[2] == ','.join(map(str, questeurs)) and 
        results[3] == ','.join(map(str, secretaires))):
        print("no changes in Bureau")
        return

    # open a new database session
    depute = S_Fonctions(
        session=sessionp,
        president=','.join(map(str, president)),
        vice_presidents=','.join(map(str, vps)),
        questeurs =  ','.join(map(str, questeurs)),
        secretaires = ','.join(map(str, secretaires)),
        date = date.today()
        #date = format_date("4 october 2024")
    )
    session.add(depute)
    session.commit()
    session.close() 
    
def parse_vote(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    
def main():
    # Start URL
    url = "https://www.senat.fr/senateurs/bureau.html"
    parse(url)

if __name__ == "__main__":
    main()