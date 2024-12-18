import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from pprint import pprint
from datetime import datetime
import time
import re
import requests
import json
import sqlalchemy
from sqlalchemy import create_engine, select, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class S_Votes(Base):
    __tablename__ = 'S_votes'

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str]
    session: Mapped[str]
    votes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f"<S_Votes(id={self.id}, session={self.session}, numero={self.numero})>"

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

def fetch_url(url, retries=10, timeout=30.0):
    attempt = 0
    while attempt < retries:
        try:
            response = httpx.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response  # Return the response if successful
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                print(f"Received 404 for {url}. Returning 404.")
                return 404  # Return 404 if the status code is 404
            else:
                attempt += 1
                print(f"Request to {url} failed with status {err.response.status_code}. Attempt {attempt} of {retries}. Retrying...")
                time.sleep(2)  # Wait before retrying
        except (httpx.TimeoutException, httpx.RequestError) as err:
            attempt += 1
            print(f"Request to {url} encountered an error: {err}. Attempt {attempt} of {retries}. Retrying...")
            time.sleep(2)  # Wait before retrying
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def check_db(sessionp, numero):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(S_Votes.numero)
        .where(S_Votes.session == sessionp)
        .where(S_Votes.numero == numero)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        return True
    return False

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
            print(f"numero: {numero}, session: {sessionp}")
            if check_db(sessionp, numero) == True:
                print("already in db")
                return
            url = "https://www.senat.fr/scrutin-public/" + scrutin.find("a")["href"]
            parse_vote(url)

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    #sessionp = session.text.strip()
    liste = soup.find_all("p", {"class": "my-2"})
    sessionp = soup.find("h1").split(" ")[-1].strip()
    for scrutin in liste:
        numero = extract_number(scrutin.find("a").text.strip())
        if check_db(sessionp, numero) == True:
                print("already in db")
                return
        url = "https://www.senat.fr/scrutin-public/" + scrutin.find("a")["href"]
        parse_vote(url)

# In json p = pour, c = contre, a = abstention, n = non_votant, q = non présent
def parse_vote(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    year = int(url.split("/")[-2])
    sessionp = str(year) + "-" + str(year+1)
    numero = extract_number(soup.find("h1").text.strip().split("-")[0])

    url_json ="https://www.senat.fr/scrutin-public/"+ str(year) + "/scr" + str(year) + "-" + numero + ".json"
    #response = fetch_url("https://www.senat.fr/scrutin-public/2023/scr2023-101.json")
    response = fetch_url(url_json)
    data = None
    if response != 404:
        data = response.json()
        #print(json.dumps(data.json(), indent=4))

        absent = []
        if soup.find("div", {"id": "accordion-collapse-4"}):
            liste = soup.find("div", {"id": "accordion-collapse-4"}).find_all("li")
            for li in liste:
                if len(li.text.split(",")) == 1:
                    pattern = r'(\d+[a-zA-Z])'
                    matches = re.findall(pattern, li.find("a")["href"])
                    senateur_id = matches[0]
                    absent.append(senateur_id)
            

            # Find and update the entry with the specific matricule
            new_vote = "q"
            for matricule_to_modify in absent:
                for entry in data['votes']:
                    #print(f"{matricule_to_modify} - {entry['matricule']}") # 04033b - 04033B
                    #if entry['matricule'] == matricule_to_modify:
                    if re.match(rf'{matricule_to_modify}', entry['matricule'], re.IGNORECASE):
                        entry['vote'] = new_vote
                        break
    
    # open a new database session
    vote = S_Votes(
        numero=numero,
        session=sessionp,
        votes=data
        #vote = ','.join(map(str, data))
    )
    session.add(vote)
    session.commit()
    session.close()
    
def main():
    # Start URL
    url = "https://www.senat.fr/scrutin-public/scr2024.html"
    parse_old(url)

if __name__ == "__main__":
    main()