import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime
import re
import os
import time
from urllib.parse import unquote
from pprint import pprint
from urllib.parse import urlparse, parse_qs

# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

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

class Deputes(Base):
    __tablename__ = 'deputes'

    id: Mapped[int] = mapped_column(primary_key=True)
    depute_id: Mapped[str]
    legislature: Mapped[int]
    nom: Mapped[str]
    photo: Mapped[str]
    profession: Mapped[str]
    date_naissance: Mapped[datetime]
    date_election: Mapped[datetime]
    date_debut_mandat: Mapped[datetime]
    date_fin_mandat: Mapped[datetime] = mapped_column(nullable=True)
    raison_fin: Mapped[str] = mapped_column(nullable=True)
    circonscription: Mapped[str]
    numero_siege: Mapped[int]
    groupe: Mapped[str]
    mail: Mapped[str]

    def __repr__(self):
        return f"<Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')
    list = soup.find("div", {"id": "deputes-list"}).find_all("li")

    # get deputes from db
    db = get_all_deputes(17)

    # get deputes from website
    for depute in list:
        db.append(depute.find("a")["href"].split("/")[-1].split("_")[-1])

    # Convert to a set to remove duplicates
    results = set(db)
    #pprint(results)
    for depute in results:
        pprint(depute)
        url_depute = "https://www.assemblee-nationale.fr/dyn/deputes/" + depute
        parse_depute(url_depute)
#TODO get last legislature of global variable
def parse_depute(url):
    # open a new database session
    session = Session()

    response = fetch_url(url)
    if response == None:
            return
    soup = BeautifulSoup(response, 'html.parser')
    mandat = soup.find("span", {"class": "_colored _bold _big"}).text.split("|")[-1].strip()
    depute_id = url.split("/")[-1]
    legislature = 17

    if re.match(r"^Mandat clos", mandat) and check_db(legislature, depute_id):
        fin = soup.find("span", text=re.compile("Date de fin de mandat")).parent.find_all("span")[-1].text
        date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
        dates = re.findall(date_pattern, fin)
        # Replace French names with English names
        for french, english in french_to_english.items():
            date = dates[0].replace(french, english)
        # Define the date format with English names
        date_format = "%e %B %Y"
        # Convert the date string to a datetime object
        date_object = datetime.strptime(date, date_format)
        date_fin_mandat = date_object
        pattern = r'\((.*?)\)'
        # Find all matches
        data_within_parentheses = re.findall(pattern, fin)
        raison = data_within_parentheses[0]
        mail = ""

        # Query for the user you want to update
        depute = session.query(Deputes).filter_by(depute_id=depute_id, legislature=legislature).first()
        if depute:
            depute.date_fin_mandat = date_fin_mandat
            depute.raison_fin = raison
            depute.mail = mail
            # Commit the changes
            session.commit()

        return
    
    elif check_db(legislature, depute_id):
        print('stop')
        return

    nom = soup.find("h1").text
    bio = soup.find("span", text=re.compile("Biographie")).parent.find("p")
    profession = bio.text.split(")")[-1].replace("-", "").strip()
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    dates = re.findall(date_pattern, bio.text)
    # Replace French names with English names
    for french, english in french_to_english.items():
        dates[0] = dates[0].replace(french, english)
    # Define the date format with English names
    date_format = "%d %B %Y"
    # Convert the date string to a datetime object
    date_object = datetime.strptime(dates[0], date_format)
    date_naissance = date_object

    photo_url = soup.find("div", {"class": "acteur-photo-image"}).find("img")["src"]
    folder = "../images/"
    photo = "PA"  + photo_url.split("/")[-1] + "-" + str(legislature)
    photo_path = os.path.abspath(folder) + photo
    download_image(photo_url, folder, photo)

    # Parse the URL to obtain the query component
    url_circo = soup.find("a",  href=re.compile(r'^/dyn/vos-deputes/carte-departements'))["href"]
    parsed_url = urlparse(url_circo)
    query_string = parsed_url.query
    # Parse the query string into a dictionary
    query_params = parse_qs(query_string)
    # Extract specific parameters
    departement_numero = query_params.get('departementNumero', [None])[0]
    circonscription_numero = query_params.get('circonscriptionNumero', [None])[0]

    circonscription = departement_numero + "-" + circonscription_numero
    numero_siege = ""
    if soup.find("a",  href=re.compile(r'^/dyn/vos-deputes/hemicycle?')):
        numero_siege = soup.find("a",  href=re.compile(r'^/dyn/vos-deputes/hemicycle?'))["href"].split("=")[-1]
    groupe = soup.find("a", {"class": "h4"}).text.strip()
    mail = soup.find("a",  href=re.compile(r'^mailto:'))["href"].split(":")[-1]

    url_archive = "https://www.assemblee-nationale.fr/dyn/deputes/" + depute_id + "/fonctions"
    archive = fetch_url(url_archive)
    soupe = BeautifulSoup(archive, "html.parser")

    date = soupe.find("li", {"class": "togglable-box"}).find("ul").find("sup").parent.text
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    dates = re.findall(date_pattern, date)
    # Replace French names with English names
    for french, english in french_to_english.items():
        dates[0] = dates[0].replace(french, english)
        dates[1] = dates[1].replace(french, english)
    # Define the date format with English names
    date_format = "%d %B %Y"
    # Convert the date string to a datetime object
    date_object = datetime.strptime(dates[0], date_format)
    date_election = date_object
    date_object = datetime.strptime(dates[1], date_format)
    date_debut_mandat = date_object

    depute = Deputes(
        depute_id=depute_id,
        nom=nom,
        legislature=legislature,
        photo=photo_path,
        profession=profession,
        date_naissance=date_naissance,
        date_election=date_election,
        date_debut_mandat=date_debut_mandat,
        date_fin_mandat=None,
        raison_fin=None,
        circonscription=circonscription,
        numero_siege=numero_siege,
        groupe=groupe,
        mail=mail

    )
    session.add(depute)
    session.commit()
    session.close()

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

def download_image(url, folder, filename):
    # Create the directory if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Combine the folder path with the filename
    file_path = os.path.join(folder, filename)

    try:
        response = httpx.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Write the image content to a file
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Image successfully downloaded: {file_path}")
    except httpx.RequestError as err:
        print(f"An error occurred while requesting {err.request.url!r}: {err}")
    except httpx.HTTPStatusError as err:
        print(f"HTTP error occurred: {err.response.status_code} - {err.response.reason_phrase}")

def check_db(legislature, depute_id):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Deputes.depute_id)
        .where(Deputes.legislature == legislature)
        .where(Deputes.depute_id == depute_id)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        return True
    return False

def get_all_deputes(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Deputes.depute_id)
        .where(Deputes.legislature == legislature)
    )
    # Execute the query
    results = session.execute(stmt).fetchall()
    list = [r[0] for r in results]
    return list

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = "https://www2.assemblee-nationale.fr/deputes/liste/alphabetique"
    parse(url)

if __name__ == "__main__":
    main()