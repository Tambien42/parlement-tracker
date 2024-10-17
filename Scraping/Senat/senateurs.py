import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from pprint import pprint
from datetime import datetime, date
import time
import re
import os
import itertools
import sqlalchemy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class Senateurs(Base):
    __tablename__ = 'senateurs'

    id: Mapped[int] = mapped_column(primary_key=True)
    senateur_id: Mapped[str]
    en_cours: Mapped[int]
    nom: Mapped[str]
    photo: Mapped[str] = mapped_column(nullable=True)
    profession: Mapped[str]
    date_naissance: Mapped[datetime]
    date_election: Mapped[datetime]
    raison_debut: Mapped[str]
    date_fin_mandat: Mapped[datetime] = mapped_column(nullable=True)
    raison_fin: Mapped[str] = mapped_column(nullable=True)
    circonscription: Mapped[str]
    numero_siege: Mapped[int] = mapped_column(nullable=True)
    groupe: Mapped[str]
    mail: Mapped[str] = mapped_column(nullable=True)
    twitter: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<Deputes(id={self.id}, nom={self.nom})>"

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
    "Alpes de Haute-Provence": "04",
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
    "La Réunion": "974",
    "Mayotte": "976",
    "Saint-Barthélemy": "977",
    "Polynésie française": "987",
    "Saint-Martin": "978",
    "Nouvelle-Calédonie": "988",
    "Iles Wallis et Futuna": "986",
    "Wallis-et-Futuna": "986",
    "Français établis hors de France": "999"
}

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

def get_all_current_senateurs():
    with Session() as session:
        stmt = select(Senateurs.photo).where(Senateurs.date_fin_mandat == None)
        results = session.scalars(stmt).all()
        return results

def group_change():
    with Session() as session:
        stmt = select(Senateurs).where(Senateurs.en_cours == 1)
        results = session.scalars(stmt).all()
        for senateur in results:
            print(senateur.nom)
            url = "https://www2.assemblee-nationale.fr/dyn/deputes/" + senateur.depute_id
            content = fetch_url(url)
            soup = BeautifulSoup(content, 'html.parser')

            groupe_id = soup.find("div", {"class": "page-content"}).find("dl").find_all("a", href=re.compile(r"^/senateurs/"))[-1]["href"].split(".")[0].split("/")[-1]
            if senateur.groupe != groupe_id:
                senateur.groupe = groupe_id
                print("Modifying Groupe")
                session.commit()

def parse(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    liste = soup.find("div", {"class": "page-content"}).find("div", {"class": "col-md-8"}).find_all("a", href=True)

    db_list = get_all_current_senateurs()
    senateurs_db = []
    if len(db_list):
        # Remove "_carre.jpg" from every item in the list
        senateurs_db = [filename.replace("_carre.jpg", "") for filename in db_list]

    site_liste = []
    for a in liste:
        site_liste.append(a['href'].split("/")[-1].split(".")[0])

    senateurs = list(set(senateurs_db).symmetric_difference(set(site_liste)))
    for senateur in senateurs:
        url = "https://www.senat.fr/senateur/" + senateur + ".html"
        parse_senateur(url)

def parse_senateur(url):
    response = fetch_url(url)
    soup = BeautifulSoup(response, 'html.parser')

    pattern = r'(\d+[a-zA-Z]?)'
    matches = re.findall(pattern, url)
    senateur_id = matches[0]
    name = soup.find("h1").text.split()
    if name[0] == "Mme" or name[0] == "M.":
        remaining_words = name[1:]
    else:
        remaining_words = name[0:]
    nom = ' '.join(remaining_words)
    print(f"Name: {nom}, id: {senateur_id}")

    photo_url = "https://www.senat.fr" + soup.find("header", {"class": "page-header"}).find("img")["src"]
    folder = "../images/senat/"
    photo = photo_url.split("/")[-1]
    if download_image(photo_url, folder, photo) == 0:
        photo = ""

    profession = ""
    if soup.find("dt", text=re.compile("Profession :")):
        profession = soup.find("dt", text=re.compile("Profession :")).find_next_sibling().text
    
    date_naissance = None
    if soup.find("dt", text=re.compile(r"^État civil")):
        date = soup.find("dt", text=re.compile(r"^État civil")).find_next_sibling().text
        date_pattern = r'(?:\d{1,2}|1er) [a-zA-Zéû]+ \d{4}'
        dates = re.findall(date_pattern, date)
        date_naissance = format_date(dates[0])
        if len(dates) == 2:
            date_mort = format_date(dates[1])

    en_cours = 1
    # check si senateur mandat clos
    if soup.find("div", {"class": "picto"}):
        # Anciens Sénateurs
        en_cours = 0
        circonscription = ""
        numero_siege = 0
        mail = ""
        group = ""
        remaining_words = group[3:]
        groupe = ' '.join(remaining_words)
        twitter = ""
        if soup.find("div", {"class": "page-content"}).find("dl").find("a", href=re.compile(r"^https://twitter.com/")):
            twitter = soup.find("div", {"class": "page-content"}).find("dl").find("a", href=re.compile(r"^https://twitter.com/"))["href"]
            if twitter.split("?"):
                twitter = twitter.split("?")[0]
        elections = soup.find("div", {"id": "accordion-collapse-2"}).find("p").decode_contents().split('<br/>')
    else:
        # Mandat en cours
        circonscription = soup.find("a", href=re.compile(r'^/senateurs/sencir')).find("img")["alt"]
        # Sort the dictionary by the length of the keys (department names) in descending order
        sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
        for dpt, number in sorted_departments:
            circonscription = circonscription.strip().replace(dpt, number)
        numero_siege = soup.find("hemicycle-seat")["seat"]
        #groupe = soup.find("img", src=re.compile(r'^/assets/images/partagees/groupes/'))["alt"]
        # TODO groupe id or groupe name ?
        # group = soup.find("div", {"class": "page-content"}).find("dl").find_all("a", href=re.compile(r"^/senateurs/"))[-1].text.split()
        # if group[0] == "groupe":
        #     remaining_words = group[1:]
        # if group[1] == "du":
        #     remaining_words = group[2:]
        # groupe = ' '.join(remaining_words)
        groupe_id = soup.find("div", {"class": "page-content"}).find("dl").find_all("a", href=re.compile(r"^/senateurs/"))[-1]["href"].split(".")[0].split("/")[-1]
        mail = ""
        if soup.find("div", {"class": "page-content"}).find("dl").find("a", href=re.compile(r"^mailto:")):
            mail = soup.find("div", {"class": "page-content"}).find("dl").find("a", href=re.compile(r"^mailto:"))["href"].split(":")[-1]
        twitter = ""
        if soup.find("div", {"class": "page-content"}).find("dl").find("a", href=re.compile(r"^https://twitter.com/")):
            twitter = soup.find("div", {"class": "page-content"}).find("dl").find("a", href=re.compile(r"^https://twitter.com/"))["href"]
            if twitter.split("?"):
                twitter = twitter.split("?")[0]
    

        elections = soup.find("div", {"id": "accordion-collapse-1"}).find("p").decode_contents().split('<br/>')
    
    for current_item, next_item in itertools.zip_longest(elections, elections[1:]):
        en_cours = 1
        if re.match(r"^Fin", current_item.replace("\n", "")) or current_item.replace("\n", "") == "":
            break

        date_election = None
        raison_debut = ""
        date_fin = None
        raison_fin = ""
        # Regular expression pattern to match the dates and parenthesis
        pattern = r'(\d{1,2}(?:er)?\s+\w+\s+\d{4})(?:\s*\((.*?)\))?'
        #pattern = r'(\d{1,2}(?:er)?\s+\w+\s+\d{4})(?![^\(]*\))'
        pattern = r'(\d{1,2}(?:er)?\s+\w+\s+\d{4})(?:\s*\(([^()]*?)\))?'
        # Find all matches
        matches = re.findall(pattern, current_item)
        print(matches)
        date_election = format_date(matches[0][0])
        raison_debut = matches[0][1].strip()
        if raison_debut == "":
            raison_debut = "Election générale"
        if raison_debut in department_numbers:
            # Sort the dictionary by the length of the keys (department names) in descending order
            sorted_departments = sorted(department_numbers.items(), key=lambda x: len(x[0]), reverse=True)
            for dpt, number in sorted_departments:
                raison_debut = raison_debut.strip().replace(dpt, number)
            circonscription = raison_debut
            raison_debut = ""
        if len(matches) == 2:
            date_fin = format_date(matches[1][0])
            raison_fin = matches[1][1].strip()

        if (next_item is not None and next_item.replace("\n", "") != "") and len(matches) == 1:
            # Find all matches
            matches = re.findall(pattern, next_item.strip())
            date_fin = format_date(matches[0][0])
            raison_fin = matches[0][1].strip()

        if next_item.strip() is not None and re.match(r"^Fin", next_item.strip()):
            # Find all matches
            matches = re.findall(pattern, next_item.strip())
            date_fin = format_date(matches[0][0])
            raison_fin = matches[0][1].strip()
        
        if date_fin is not None:
            en_cours = 0
        
        #print(f"en cours: {en_cours} - date election: {date_election}, raison debut: {raison_debut} - date fin: {date_fin}, raison fin: {raison_fin}")

        senateur = session.query(Senateurs).filter(Senateurs.senateur_id == senateur_id, Senateurs.date_election == date_election).first()
        if senateur:
            if senateur.date_fin_mandat != date_fin:
                senateur.date_fin_mandat = date_fin
            if senateur.groupe != groupe:
                senateur.groupe = groupe
            if senateur.en_cours != en_cours:
                senateur.en_cours = en_cours
            session.commit()
            print("Senateur data updated successfully.")
            return

        # Store data in the database
        senateur = Senateurs(
            senateur_id=senateur_id,
            en_cours=en_cours,
            nom=nom,
            photo=photo,
            profession=profession,
            date_naissance=date_naissance,
            date_election=date_election,
            raison_debut=raison_debut,
            date_fin_mandat=date_fin,
            raison_fin=raison_fin,
            circonscription=circonscription,
            numero_siege=numero_siege,
            groupe=groupe_id,
            mail=mail,
            twitter=twitter
        )
        
        session.add(senateur)  # Use merge to update or insert
        session.commit()
        session.close() 

def main():
    # Start URL
    # senateurs actuels
    url = "https://www.senat.fr/senateurs/senatl.html"
    # tous les anciens sénateurs
    #url = "https://www.senat.fr/anciens-senateurs-5eme-republique/senatl.html"
    parse(url)
    # Check if senateur change groupe
    group_change()

if __name__ == "__main__":
    main()
