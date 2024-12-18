import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from pprint import pprint
from datetime import datetime
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

class S_Scrutins(Base):
    __tablename__ = 'S_scrutins'

    id: Mapped[int] = mapped_column(primary_key=True)
    session: Mapped[str]
    numero: Mapped[str]
    titre: Mapped[str]
    date_seance: Mapped[datetime]
    lien: Mapped[str]
    votes_pour: Mapped[int]
    votes_contre: Mapped[int]
    votes_abstention: Mapped[int]
    non_votants: Mapped[int]

    def __repr__(self):
        return f"<S_Scrutins(id={self.id}, session={self.session}, numero={self.numero})>"

Base.metadata.create_all(engine)

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

def check_db(sessionp, numero):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(S_Scrutins.numero)
        .where(S_Scrutins.session == sessionp)
        .where(S_Scrutins.numero == numero)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        return True
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

def extract_number(text):
    # Regex pattern to extract digits after "n°"
    match = re.search(r'scrutin n°(\d+)', text, re.IGNORECASE)
    
    if match:
        return match.group(1)  # Return the captured number
    else:
        return None  # Return None if no match is found

def parse_old(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    session_list = soup.find("aside").find("ul", {"class": "dropdown-menu"}).find_all("a")
    for session in session_list:
        sessionp = session.text.strip()
        url_session = "https://www.senat.fr/scrutin-public/" + session["href"]
        response = fetch_url(url_session)
        soup = BeautifulSoup(response, 'html.parser')

        liste = soup.find_all("p", {"class": "my-2"})
        for scrutin in liste:
            numero = extract_number(scrutin.find("a").text.strip())
            #print(f"numero: {numero}, session: {sessionp}")
            # TODO if numero and session in db skip
            if check_db(sessionp, numero) == True:
                print("already in db")
                return
            url = "https://www.senat.fr/scrutin-public/" + scrutin.find("a")["href"]
            parse_scrutin(url)

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    session = soup.find("aside").find("ul", {"class": "dropdown-menu"}).find("a").text
    liste = soup.find_all("p", {"class": "my-2"})
    for scrutin in liste:
        numero = extract_number(scrutin.find("a").text.strip())
        # TODO if numero and session in db skip
        url = "https://www.senat.fr/scrutin-public/" + scrutin.find("a")["href"]
        parse_scrutin(url)

def parse_scrutin(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    year = int(url.split("/")[-2])
    sessionp = str(year) + "-" + str(year+1)
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    dates = re.findall(date_pattern, soup.find("h1").text.strip())
    date = format_date(dates[0])
    numero = extract_number(soup.find("h1").text.strip().split("-")[0])
    titre = soup.find("p", {"class": "page-lead"}).text.strip()
    lien = url # or just the end ?
    
    card = soup.find("div", {"class": "card-body"}).find_all("li")
    votes_pour = card[2].find("strong").text
    votes_contre = card[3].find("strong").text
    votes_abstention = card[4].find("span").text
    absents = soup.find_all("div", {"class": "accordion-body"})[-1].find_all("li")
    count = 0
    for abs in absents:
        if len(abs.text.split(",")) > 1:
            count = count + 1
    non_votants = count
    
    print(f"numero: {numero}, session: {sessionp}, date: {date}, pour:{votes_pour}, contre: {votes_contre}, abstention: {votes_abstention}, non-votants: {non_votants}")

    # open a new database session
    scrutin = S_Scrutins(
        numero=numero,
        session=sessionp,
        titre=titre,
        date_seance=date,
        lien=lien,
        votes_pour=votes_pour,
        votes_contre=votes_contre,
        votes_abstention=votes_abstention,
        non_votants=non_votants

    )
    session.add(scrutin)
    session.commit()
    session.close()

def main():
    # Start URL
    url = "https://www.senat.fr/scrutin-public/scr2024.html"
    parse_old(url)

if __name__ == "__main__":
    main()