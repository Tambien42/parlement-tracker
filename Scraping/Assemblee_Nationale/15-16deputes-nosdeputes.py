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

# Global variable
# legislature = 15
# url_legislature = "https://2017-2022.nosdeputes.fr/deputes"
legislature = 16
#url_legislature = "https://2022-2024.nosdeputes.fr/deputes"
url_legislature = "https://www.nosdeputes.fr/deputes"


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

def format_date(str):
    # Replace French names with English names
    for french, english in french_to_english.items():
        str = str.replace(french, english)
    # Define the date format with English names
    date_format = "%d %B %Y"
    # Convert the date string to a datetime object
    date_object = datetime.strptime(str, date_format)
    return date_object

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
    lieu_naissance: Mapped[str]
    date_election: Mapped[datetime]
    date_debut_mandat: Mapped[datetime]
    raison_debut: Mapped[str]
    date_fin_mandat: Mapped[datetime] = mapped_column(nullable=True)
    raison_fin: Mapped[str] = mapped_column(nullable=True)
    circonscription: Mapped[str]
    numero_siege: Mapped[int] = mapped_column(nullable=True)
    groupe: Mapped[str]
    mail: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

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
        return 1
    except httpx.RequestError as err:
        print(f"An error occurred while requesting {err.request.url!r}: {err}")
        return 0
    except httpx.HTTPStatusError as err:
        print(f"HTTP error occurred: {err.response.status_code} - {err.response.reason_phrase}")
        return 0

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')
    list = soup.find_all("div", {"class": "list_table"})

    for t in list:
        link = t.find_all("a")
        for a in link:
            #url_profile = "https://2017-2022.nosdeputes.fr" + a["href"]
            url_profile = "https://www.nosdeputes.fr" + a["href"]
            res = fetch_url(url_profile)
            soup = BeautifulSoup(res, 'html.parser')
            depute = soup.find("div", {"id": "b1"}).find("ul").find("ul").find("a")["href"].split("_")[-1]
            url_depute = "https://www.assemblee-nationale.fr/dyn/deputes/" + depute
            parse_depute(url_depute)

def parse_depute(url):
    response = fetch_url(url)
    if response == None:
            return
    soup = BeautifulSoup(response, 'html.parser')

    depute_id = url.split("/")[-1]
    
    name = soup.find("h1").text.split()
    remaining_words = name[1:]
    nom = ' '.join(remaining_words)
    print(nom)
    groupe = soup.find("a", {"class": "h4"})["href"].split("/")[-1]
    if soup.find("a", {"class": "h4"})["href"].split("/")[-1].split("?"):
        groupe = soup.find("a", {"class": "h4"})["href"].split("/")[-1].split("?")[0]
    
    circo = soup.find("span", {"class": "_big"}).text
    # Regular expression to match the département (everything before the parentheses)
    departement_pattern = r'^(.*?)\s*\('
    departement = re.search(departement_pattern, circo).group(1).strip()
    # Sort the dictionary by the length of the keys (department names) in descending order
    sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
    for dpt, number in sorted_departments:
        departement = departement.replace(dpt, number)
    # Regular expression to extract only the number from "5e circonscription"
    circonscription_pattern = r'\((\d+)(?:e|er|re) circonscription\)'
    circonscription_number = re.search(circonscription_pattern, circo).group(1).strip()
    circonscription = departement + '-' + circonscription_number

    photo_url = soup.find("div", {"class": "acteur-photo-image"}).find("img")["src"]
    folder = "../images/an/"
    ext = photo_url.split("/")[-1].split(".")
    photo = "PA"  + ext[0] +  "-" + str(legislature) + '.' + ext[-1]
    if download_image(photo_url, folder, photo) == 0:
        photo = ""
    
    bio = soup.find("span", text=re.compile("Biographie")).parent.find("p")
    profession = ""
    if bio.find("br").next_sibling:
        profession = bio.find("br").next_sibling.strip()
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    dates = re.findall(date_pattern, bio.find("br").previous_sibling.strip())
    date_naissance = format_date(dates[0])
    # lieu de naissance
    pattern = r"à ([^()]+) \(([^)]+)\)"
    match1 = re.search(pattern, bio.find("br").previous_sibling.strip())
    lieu_naissance = ""
    if match1:
        city = match1.group(1).strip()
        department1 = match1.group(2).strip()
        departement  = department1
        # Sort the dictionary by the length of the keys (department names) in descending order
        sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
        for dpt, number in sorted_departments:
            departement = departement.replace(dpt, number)
        lieu_naissance = city + "-" + departement
    
    archive = "https://www.assemblee-nationale.fr/dyn/deputes/" + depute_id + "/fonctions?archive=oui"
    response = fetch_url(archive)
    if response == None:
            return
    soup = BeautifulSoup(response, 'html.parser')
    
    mandat = soup.find("div", {"class": "page-content"}).find('span', text=re.compile("Mandat")).parent
    liste = mandat.find_all("span")

    for span in liste:
        if re.match(fr"^{legislature}", span.text):
            # Regular expression to match dates in the format: day month year (e.g., 19 juin 2022)
            date_pattern = r'(?:\d{1,2}|1er) \w+ \d{4}'
            dates = re.findall(date_pattern, span.text)
            # Regular expression to match text inside parentheses
            parentheses_pattern = r'\((.*?)\)'
            parentheses_content = re.findall(parentheses_pattern, span.text)
            date_election = format_date(dates[0])
            date_debut_mandat = format_date(dates[1])
            raison_debut = parentheses_content[0]
            date_fin_mandat = format_date(dates[2])
            raison_fin = parentheses_content[1]

            # open a new database session
            session = Session()
            depute = Deputes(
                depute_id=depute_id,
                nom=nom,
                legislature=legislature,
                photo=photo,
                profession=profession,
                date_naissance=date_naissance,
                lieu_naissance=lieu_naissance,
                date_election=date_election,
                date_debut_mandat=date_debut_mandat,
                raison_debut=raison_debut,
                date_fin_mandat=date_fin_mandat,
                raison_fin=raison_fin,
                circonscription=circonscription,
                numero_siege=0,
                groupe=groupe,
                mail=""

            )
            session.add(depute)
            session.commit()
            session.close() 

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    # Start URL
    parse(url_legislature)

if __name__ == "__main__":
    main()