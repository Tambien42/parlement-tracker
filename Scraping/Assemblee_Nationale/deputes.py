import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import time
import re
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column
from pprint import pprint

# Global variable
legislature = 17

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class AN_Deputes(Base):
    __tablename__ = 'AN_deputes'

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
        return f"<AN_Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

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

def get_all_current_deputes():
    """
    Get a list of all depute IDs from the database.
    
    Returns:
        list: A list of all depute IDs.
    """
    with Session() as session:
        stmt = select(AN_Deputes.depute_id).where(AN_Deputes.legislature == legislature).where(AN_Deputes.date_fin_mandat == None)
        results = session.scalars(stmt).all()
        return results

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

def fetch_url_content(url, retries=10, delay=30):
    """
    Fetch the content of a URL using Playwright, with retries in case of failure.
    
    Args:
        url (str): The URL to fetch.
        retries (int): Number of times to retry in case of an error (default: 3).
        delay (int): Delay in seconds between retries (default: 5).
    
    Returns:
        str: The content of the page.
    """
    for attempt in range(retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True) 
                page = browser.new_page()  # Create a new page
                page.goto(url, timeout=30000)  # Set a 30-second timeout
                content = page.content()
                browser.close()
                return content
        except PlaywrightTimeoutError:
            print(f"Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        except Exception as e:
            if "503" in str(e):
                print(f"HTTP 503 error encountered. Attempt {attempt + 1} of {retries}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
    raise Exception(f"Failed to fetch the URL: {url} after {retries} retries")

def group_change():
    with Session() as session:
        stmt = select(AN_Deputes).where(AN_Deputes.legislature == legislature).where(AN_Deputes.date_fin_mandat == None)
        results = session.scalars(stmt).all()
        for depute in results:
            print(depute.nom)
            url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + depute.depute_id
            content = fetch_url(url)
            soup = BeautifulSoup(content, 'html.parser')

            groupe = soup.find("a", {"class": "h4"})["href"].split("/")[-1]
            if depute.groupe != groupe:
                depute.groupe = groupe
                print("Modifying Groupe")
                session.commit()
        

def parse(url):
    """
    Fetch the URL content and start scraping the data.
    
    Args:
        url (str): The URL to fetch and parse.
    
    Returns:
        BeautifulSoup: Parsed HTML content of the page.
    """
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')
    liste = []
    if soup.find("div", {"id": "deputes-list"}):
        liste = soup.find("div", {"id": "deputes-list"}).find_all("li")
    if soup.find("div", {"id": "DataTables_Table_0_wrapper"}):
        liste = soup.find("div", {"id": "DataTables_Table_0_wrapper"}).find_all("tr")

    db_liste = get_all_current_deputes()

    site_liste = []
    for depute in liste:
        site_liste.append(depute.find("a")["href"].split("_")[-1])

    if len(db_liste) == 0:
        print("No data in db. retrieving data from website")
        for depute in site_liste:
            depute_url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + depute
            parse_depute(depute_url)
        return
    
    print("Checking for new deputes or deputes who resigned")
    deputes = list(set(db_liste).symmetric_difference(set(site_liste)))
    for depute in deputes:
        depute_url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + depute
        parse_depute(depute_url)

def parse_clos(url):
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')

    liste = []
    if soup.find("tbody"):
        liste = soup.find("tbody").find_all("a")
        
    for depute in liste:
        depute_url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + depute["href"].split("_")[-1]
        parse_old_mandat_clos(depute_url)

def parse_depute(url):
    """
    Fetch the content of a depute page and extract relevant data.
    
    Args:
        url (str): The URL of the depute page to fetch and parse.
    
    Returns:
        dict: Extracted data about the depute.
    """
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')
    
    depute_id = url.split("/")[-1]
    name = soup.find("h1").text.split()
    remaining_words = name[1:]
    nom = ' '.join(remaining_words)

    print(f"Name: {nom}")

    photo_url = soup.find("div", {"class": "acteur-photo-image"}).find("img")["src"]
    folder = "../images/an/"
    ext = photo_url.split("/")[-1].split(".")
    photo = "PA"  + ext[0] +  "-" + str(legislature) + '.' + ext[-1]
    if download_image(photo_url, folder, photo) == 0:
        photo = ""
    groupe = soup.find("a", {"class": "h4"})["href"].split("/")[-1]

    mandat = soup.find_all("span", {"class": "_big"})[-1].text.replace("|", "").strip()
    if re.match(r"^Mandat clos", mandat):
        print("mandat clos")
        mail = ""
        bloc = soup.find("div", {"class": "bloc-content"}).find_all("span")[-1].text.strip()
        date_pattern = r'(?:\d{1,2}|1er) \w+ \d{4}'
        dates = re.findall(date_pattern, bloc)
        date_fin_mandat = format_date(dates[0])
        raison_fin = bloc.split("(")[-1].replace(")", "").strip()
        depute = session.query(AN_Deputes).filter(AN_Deputes.depute_id == depute_id, AN_Deputes.legislature == legislature).first()
        if depute:
            depute.mail = mail
            depute.date_fin_mandat = date_fin_mandat
            depute.raison_fin = raison_fin
            session.commit()
            print("save data")
        return
    
    biographie_tag = soup.find(string="Biographie")
    date = biographie_tag.parent.parent.find("p").find("br").previous_sibling.split("à")[0].strip()
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    dates = re.findall(date_pattern, date)
    date_naissance = format_date(dates[0])
    pattern = r"à ([^()]+) \(([^)]+)\)"
    match1 = re.search(pattern, biographie_tag.parent.parent.find("p").find("br").previous_sibling)
    lieu_naissance = ""
    if match1:
        city = match1.group(1).strip()
        department1 = match1.group(2).strip()
        departement  = department1.strip()
        # Sort the dictionary by the length of the keys (department names) in descending order
        sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
        for dpt, number in sorted_departments:
            departement = departement.replace(dpt, number)
        lieu_naissance = city + "-" + departement
    profession = ""
    if biographie_tag.parent.parent.find("p").find("br").next_sibling:
        profession = biographie_tag.parent.parent.find("p").find("br").next_sibling

    # Parse the URL to obtain the query component
    url_circo = soup.find("a", href=re.compile(r'^/dyn/vos-deputes/carte-departements'))["href"]
    parsed_url = urlparse(url_circo)
    query_string = parsed_url.query
    # Parse the query string into a dictionary
    query_params = parse_qs(query_string)
    # Extract specific parameters
    departement_numero = query_params.get('departementNumero', [None])[0]
    circonscription_numero = query_params.get('circonscriptionNumero', [None])[0]

    circonscription = departement_numero + "-" + circonscription_numero
    numero_siege = 0
    if soup.find("a", href=re.compile(r'^/dyn/vos-deputes/hemicycle')):
        numero_siege = soup.find("a", href=re.compile(r'^/dyn/vos-deputes/hemicycle'))["href"].split("=")[-1]
    mail = soup.find("a", href=re.compile(r'^mailto:'))["href"].split(":")[-1]

    fonctions_url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + depute_id + "/fonctions"
    fonctions_content = fetch_url(fonctions_url)
    soup_fonctions = BeautifulSoup(fonctions_content, 'html.parser')

    date_election = None
    date_debut_mandat = None
    raison_debut = ""
    date_fin_mandat = None
    raison_fin = ""
    for span in soup_fonctions.find_all("span", {"class": "relative-block"}):
        if re.match(fr"^{legislature}", span.text):
            # Regular expression to match dates in the format: day month year (e.g., 19 juin 2022)
            date_pattern = r'(?:\d{1,2}|1er) \w+ \d{4}'
            dates = re.findall(date_pattern, span.text)
            date_election = format_date(dates[0])
            date_debut_mandat = format_date(dates[1])
            # Regular expression to match text inside parentheses
            parentheses_pattern = r'\((.*?)\)'
            parentheses_content = re.findall(parentheses_pattern, span.text)
            raison_debut = parentheses_content[0]
            
            depute = session.query(AN_Deputes).filter(AN_Deputes.depute_id == depute_id, AN_Deputes.legislature == legislature, AN_Deputes.date_debut_mandat == date_debut_mandat).first()
            if depute:
                print(f"Depute with ID {depute_id} already in database. Skipping.")
                continue
    
            # Store data in the database
            depute = AN_Deputes(
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
                numero_siege=numero_siege,
                groupe=groupe,
                mail=mail
            )
            
            session.add(depute)  # Use merge to update or insert
            session.commit()
            session.close() 

def parse_old_mandat_clos(url):
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')

    depute_id = url.split("/")[-1]
    name = soup.find("h1").text.split()
    remaining_words = name[1:]
    nom = ' '.join(remaining_words)

    # Print or store the extracted data
    print(f"Name: {nom}")
    photo_url = soup.find("div", {"class": "acteur-photo-image"}).find("img")["src"]
    folder = "../images/an/"
    ext = photo_url.split("/")[-1].split(".")
    photo = "PA"  + ext[0] +  "-" + str(legislature) + '.' + ext[-1]
    if download_image(photo_url, folder, photo) == 0:
        photo = ""
    groupe = soup.find("a", {"class": "h4"})["href"].split("/")[-1]
    if groupe.split("?"):
        groupe = groupe.split("?")[0]
    mandat = soup.find_all("span", {"class": "_big"})[-1].text.replace("|", "").strip()
    biographie_tag = soup.find(string="Biographie")
    date = biographie_tag.parent.parent.find("p").find("br").previous_sibling.split("à")[0].strip()
    date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
    dates = re.findall(date_pattern, date)
    date_naissance = format_date(dates[0])
    pattern = r"à ([^()]+) \(([^)]+)\)"
    match1 = re.search(pattern, biographie_tag.parent.parent.find("p").find("br").previous_sibling)
    lieu_naissance = ""
    if match1:
        city = match1.group(1).strip()
        department1 = match1.group(2).strip()
        departement  = department1.strip()
        # Sort the dictionary by the length of the keys (department names) in descending order
        sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
        for dpt, number in sorted_departments:
            departement = departement.replace(dpt, number)
        lieu_naissance = city + "-" + departement
    profession = ""
    if biographie_tag.parent.parent.find("p").find("br").next_sibling:
        profession = biographie_tag.parent.parent.find("p").find("br").next_sibling
    
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

    numero_siege = 0
    mail = ""

    fonctions_url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + depute_id + "/fonctions?archive=oui"
    fonctions_content = fetch_url(fonctions_url)
    soup_fonctions = BeautifulSoup(fonctions_content, 'html.parser')

    date_election = None
    date_debut_mandat = None
    raison_debut = ""
    date_fin_mandat = None
    raison_fin = ""
    for span in soup_fonctions.find_all("span", {"class": "relative-block"}):
        if re.match(fr"^{legislature}", span.text):
            # Regular expression to match dates in the format: day month year (e.g., 19 juin 2022)
            date_pattern = r'(?:\d{1,2}|1er) \w+ \d{4}'
            dates = re.findall(date_pattern, span.text)
            date_election = format_date(dates[0])
            date_debut_mandat = format_date(dates[1])
            date_fin_mandat = format_date(dates[2])
            # Regular expression to match text inside parentheses
            parentheses_pattern = r'\((.*?)\)'
            parentheses_content = re.findall(parentheses_pattern, span.text)
            raison_debut = parentheses_content[0]
            raison_fin = parentheses_content[1]

            record = session.query(AN_Deputes).filter(AN_Deputes.depute_id == depute_id, AN_Deputes.legislature == legislature, AN_Deputes.date_fin_mandat == None).first()
            if record:
                record.date_fin_mandat = date_fin_mandat
                record.raison_fin = raison_fin
                record.mail = ""
                record.numero_siege = 0
                session.commit()
                print(f"Modifying data of depute with ID {depute_id}.")
                # modify record
                continue
            if session.query(AN_Deputes).filter(AN_Deputes.depute_id == depute_id, AN_Deputes.legislature == legislature, AN_Deputes.date_fin_mandat == date_fin_mandat).first():
                print(f"Depute with ID {depute_id} already in database. Skipping.")
                continue

            # Store data in the database
            depute = AN_Deputes(
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
                numero_siege=numero_siege,
                groupe=groupe,
                mail=mail
            )
            
            session.add(depute)  # Use merge to update or insert
            session.commit()
            session.close() 

    print(parentheses_content)
    
def main():
    # Example URL (replace with target URL)
    url = "https://www2.assemblee-nationale.fr/deputes/liste/alphabetique"
    parse(url)
    # liste mandat clos
    url = "https://www2.assemblee-nationale.fr/deputes/liste/clos"
    parse_clos(url)
    # Check if depute changed group
    group_change()

if __name__ == "__main__":
    main()