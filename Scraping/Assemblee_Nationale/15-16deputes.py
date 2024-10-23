import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
import re
import time
from urllib.parse import unquote
from votes import Votes
import os
import subprocess
from pprint import pprint
import requests

# Global Variable
legislature = 16

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

# Dictionary mapping French department names to their numbers
department_numbers = {
    "Ain": "01",
    "Aisne": "02",
    "Allier": "03",
    "Alpes-de-Haute-Provence": "04",
    "Hautes-Alpes": "05",
    "Alpes-Maritimes": "06",
    "Ardèche": "07",
    "Ardennes": "08",
    "Ariège": "09",
    "Aube": "10",
    "Aude": "11",
    "Aveyron": "12",
    "Bouches-du-Rhône": "13",
    "Calvados": "14",
    "Cantal": "15",
    "Charente": "16",
    "Charente-Maritime": "17",
    "Cher": "18",
    "Corrèze": "19",
    "Corse-du-Sud": "2A",
    "Haute-Corse": "2B",
    "Côte-d'Or": "21",
    "Côtes-d'Armor": "22",
    "Creuse": "23",
    "Dordogne": "24",
    "Doubs": "25",
    "Drôme": "26",
    "Eure": "27",
    "Eure-et-Loir": "28",
    "Finistère": "29",
    "Gard": "30",
    "Haute-Garonne": "31",
    "Gers": "32",
    "Gironde": "33",
    "Hérault": "34",
    "Ille-et-Vilaine": "35",
    "Indre": "36",
    "Indre-et-Loire": "37",
    "Isère": "38",
    "Jura": "39",
    "Landes": "40",
    "Loir-et-Cher": "41",
    "Loire": "42",
    "Haute-Loire": "43",
    "Loire-Atlantique": "44",
    "Loiret": "45",
    "Lot": "46",
    "Lot-et-Garonne": "47",
    "Lozère": "48",
    "Maine-et-Loire": "49",
    "Manche": "50",
    "Marne": "51",
    "Haute-Marne": "52",
    "Mayenne": "53",
    "Meurthe-et-Moselle": "54",
    "Meuse": "55",
    "Morbihan": "56",
    "Moselle": "57",
    "Nièvre": "58",
    "Nord": "59",
    "Oise": "60",
    "Orne": "61",
    "Pas-de-Calais": "62",
    "Puy-de-Dôme": "63",
    "Pyrénées-Atlantiques": "64",
    "Hautes-Pyrénées": "65",
    "Pyrénées-Orientales": "66",
    "Bas-Rhin": "67",
    "Haut-Rhin": "68",
    "Rhône": "69",
    "Haute-Saône": "70",
    "Saône-et-Loire": "71",
    "Sarthe": "72",
    "Savoie": "73",
    "Haute-Savoie": "74",
    "Paris": "75",
    "Seine-Maritime": "76",
    "Seine-et-Marne": "77",
    "Yvelines": "78",
    "Deux-Sèvres": "79",
    "Somme": "80",
    "Tarn": "81",
    "Tarn-et-Garonne": "82",
    "Var": "83",
    "Vaucluse": "84",
    "Vendée": "85",
    "Vienne": "86",
    "Haute-Vienne": "87",
    "Vosges": "88",
    "Yonne": "89",
    "Territoire de Belfort": "90",
    "Essonne": "91",
    "Hauts-de-Seine": "92",
    "Seine-Saint-Denis": "93",
    "Val-de-Marne": "94",
    "Val-d'Oise": "95",
    "Guadeloupe": "971",
    "Martinique": "972",
    "Guyane": "973",
    "Réunion": "974",
    "Mayotte": "976",
    "Français établis hors de France": "999"
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
    numero_siege: Mapped[int] = mapped_column(nullable=True)
    groupe: Mapped[str]
    mail: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

class FonctionsAN(Base):
    __tablename__ = 'fonctions_an'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    president: Mapped[str]
    vice_presidents: Mapped[str]
    questeurs: Mapped[str]
    secretaires: Mapped[str]
    date: Mapped[datetime]

    def __repr__(self):
        return f"<FonctionsAN(id={self.id}, legislature={self.legislature}, president={self.president})>"

def parse(url):
    list = get_all_deputes_from_votes(legislature)
    deputes = merge_and_remove_duplicates(list)
    print(len(deputes))

    # for depute in deputes:
    #     # vote en congrès skip les sénateurs
    #     if re.match(r"^PA\d+", depute) == None:
    #         continue
    #     if check_db(legislature, depute):
    #         print("already on db")
    #         continue
    #     pprint(depute)
    #     url = "https://www.assemblee-nationale.fr/dyn/deputes/" + depute
    #     parse_depute(url)
        

def parse_depute(url):
    response = fetch_url(url)
    if response == None:
            return
    soup = BeautifulSoup(response, "html.parser")
    
    name = soup.find("h1").text.split()
    # Remove the first word
    remaining_words = name[1:]
    nom = ' '.join(remaining_words)
    depute_id = url.split("/")[-1]
    groupe = soup.find("a", {"class": "h4"}).text.strip()
    pprint(nom)

    bio = soup.find("span", text=re.compile("Biographie")).parent.find("p")
    profession = bio.text.split(")")[-1].replace("-", "").strip()
    date_pattern = r'(?:\d{1,3}|1er) [a-zA-Zéû]+ \d{4}'
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
    ext = photo_url.split("/")[-1].split(".")
    photo = "PA"  + ext[0] +  "-" + str(legislature) + '.' + ext[-1]
    photo_path = os.path.abspath(folder) + photo
    download_image(photo_url, folder, photo)

    url_archive = "https://www.assemblee-nationale.fr/dyn/deputes/" + depute_id + "/fonctions?archive=oui"
    archive = fetch_url(url_archive)
    soupe = BeautifulSoup(archive, "html.parser")
    
    circos = soup.find("span", {"class": "_big"}).text.split("|")[0].strip()
    departement = circos.split("(")[0].strip()
    # Sort the dictionary by the length of the keys (department names) in descending order
    sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
    for department, number in sorted_departments:
        departement = departement.replace(department, number)
    pattern = r'\d{1,2}'
    number = re.findall(pattern, circos)
    circo = number[0]
    circonscription = departement + "-" + str(circo)
    numero_siege = ""

    all_dates = soupe.find("li", {"class": "togglable-box"}).find("ul").find_all("sup")
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    for date in all_dates:
        if re.match(fr"^{legislature}", date.parent.text):
            dates = re.findall(date_pattern, date.parent.text)
            # Replace French names with English names
            for french, english in french_to_english.items():
                dates[0] = dates[0].replace(french, english)
                dates[1] = dates[1].replace(french, english)
                dates[2] = dates[2].replace(french, english)
            # Define the date format with English names
            date_format = "%d %B %Y"
            # Convert the date string to a datetime object
            date_object = datetime.strptime(dates[0], date_format)
            date_election = date_object
            date_object = datetime.strptime(dates[1], date_format)
            date_debut_mandat = date_object
            date_object = datetime.strptime(dates[2], date_format)
            date_fin_mandat = date_object
            pattern = r'\((.*?)\)'
            # Find all matches
            data_within_parentheses = re.findall(pattern, date.parent.text)
            raison = data_within_parentheses[-1]

    # open a new database session
    session = Session()
    depute = Deputes(
        depute_id=depute_id,
        nom=nom,
        legislature=legislature,
        photo=photo_path,
        profession=profession,
        date_naissance=date_naissance,
        date_election=date_election,
        date_debut_mandat=date_debut_mandat,
        date_fin_mandat=date_fin_mandat,
        raison_fin=raison,
        circonscription=circonscription,
        numero_siege=0,
        groupe=groupe,
        mail=""

    )
    session.add(depute)
    session.commit()
    session.close()

def parse_fonctions(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
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
    depute = FonctionsAN(
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

def check_fonctions(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(FonctionsAN.president, FonctionsAN.vice_presidents, FonctionsAN.questeurs, FonctionsAN.secretaires)
        .where(FonctionsAN.legislature == legislature)
        .order_by(FonctionsAN.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).fetchall()

    if len(results) != 0:
        last = results[0]
        return last
    return None

def merge_and_remove_duplicates(list_of_str):
    # Split each string by commas and flatten the list
    flat_list = [item.strip() for sublist in list_of_str for item in sublist.split(',')]
    # Convert to a set to remove duplicates
    unique_items = set(flat_list)
    # Convert back to a list and sort it (optional)
    return sorted(unique_items)

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

def get_all_deputes_from_votes(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Votes.pour, Votes.contre, Votes.abstention, Votes.non_votants)
        .where(Votes.legislature == legislature)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    return results

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = "https://www2.assemblee-nationale.fr/deputes/liste/alphabetique"
    parse(url)
    # get fonctions du bureau de l'an
    match legislature:
        case 15:
            url = "https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/42363undefined"
        case 16:
            url = "https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/119106undefined"
        case 17:
            url = "https://www2.assemblee-nationale.fr/layout/set/ajax/content/view/embed/189123undefined"
    
    url  = "https://www2.assemblee-nationale.fr/" + str(legislature) + "/le-bureau-de-l-assemblee-nationale"
    parse_fonctions(url)

if __name__ == "__main__":
    main()