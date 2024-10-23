import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date
import time
import re
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class DeputesEuro(Base):
    __tablename__ = 'deputes_europeens'

    id: Mapped[int] = mapped_column(primary_key=True)
    depute_id: Mapped[str]
    en_cours: Mapped[int]
    legislature: Mapped[int]
    nom: Mapped[str]
    prenom: Mapped[str]
    fullname: Mapped[str]
    photo: Mapped[str] = mapped_column(nullable=True)
    date_naissance: Mapped[datetime] = mapped_column(nullable=True)
    lieu_naissance: Mapped[str] = mapped_column(nullable=True)
    date_election: Mapped[datetime] = mapped_column(nullable=True)
    date_fin_mandat: Mapped[datetime] = mapped_column(nullable=True)
    raison_fin: Mapped[str] = mapped_column(nullable=True)
    pays: Mapped[str]
    groupe_pays: Mapped[str] = mapped_column(nullable=True)
    groupe: Mapped[str] = mapped_column(nullable=True)
    mail: Mapped[str] = mapped_column(nullable=True)
    twitter: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<Deputes(id={self.id}, nom={self.nom})>"

Base.metadata.create_all(engine)

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
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
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

def entrants_sortants(legislature):
    url_entrants = "https://www.europarl.europa.eu/meps/fr/incoming-outgoing/incoming"
    content = fetch_url(url_entrants)
    soup = BeautifulSoup(content, 'html.parser')
    list = soup.find("div", {"class": "erpl_member-list"}).find_all("a")
    print("-----------------------entrants-----------------------------")
    for mep in list:
        url = mep["href"]
        depute_id = mep["href"].split("/")[-1]
        date_debut = mep.find("span", {"class": "sln-additional-info"}).text
        print(f"{depute_id} {date_debut}")
        parse_depute(url, legislature)
        depute_euro = session.query(DeputesEuro).filter(DeputesEuro.depute_id == depute_id, DeputesEuro.legislature == legislature).first()
        if depute_euro:
            if depute_euro.en_cours != 1:
                depute_euro.en_cours = 1
            if depute_euro.date_election != datetime.strptime(date_debut, "%d-%m-%Y"):
                depute_euro.date_election = datetime.strptime(date_debut, "%d-%m-%Y")
            session.commit()
            print("Depute data updated successfully.")
    
    url_sortants = "https://www.europarl.europa.eu/meps/fr/incoming-outgoing/outgoing"
    content = fetch_url(url_sortants)
    soup = BeautifulSoup(content, 'html.parser')
    list = soup.find("div", {"class": "erpl_member-list"}).find_all("a")
    print("-----------------------sortants-----------------------------")
    for mep in list:
        url = mep["href"]
        depute_id = mep["href"].split("/")[-1]
        date_fin = mep.find("span", {"class": "sln-additional-info"}).text.split("- ")[-1].strip()
        print(f"{depute_id} {date_fin}")
        parse_depute(url, legislature)
        depute_euro = session.query(DeputesEuro).filter(DeputesEuro.depute_id == depute_id, DeputesEuro.legislature == legislature).first()
        if depute_euro:
            if depute_euro.en_cours != 0:
                depute_euro.en_cours = 0
            if depute_euro.date_fin_mandat != datetime.strptime(date_fin, "%d-%m-%Y"):
                depute_euro.date_fin_mandat = datetime.strptime(date_fin, "%d-%m-%Y")
            depute_euro.mail = ""
            session.commit()
            print("Depute data updated successfully.")



def parse(url, legislature):
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')

    list = soup.find("div", {"class": "erpl_member-list"}).find_all("a")
    for mep in list:
        url = mep["href"]
        parse_depute(url, legislature)

def parse_depute(url, legislature):
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')
    depute_id = url.split("/")[-1]


    en_cours = 0
    if legislature == 10:
        en_cours = 1
    date_debut = None
    if legislature == 10:
        date_debut = datetime.strptime("16-07-2024", "%d-%m-%Y")

    
    # Regular expression pattern to match first name and last name
    pattern = r"^(.+?)\s+([\wÀ-ÖØ-öø-ÿ\-\/\'\s]+)$"
    name = soup.find("div", {"id": "presentationmep"}).find("span", {"class": "sln-member-name"}).text.strip()
    match = re.match(pattern, name, re.UNICODE)
    if match:
        prenom = match.group(1).strip()
        nom = match.group(2).strip()
    if name == "Sir Christopher J. PROUT (Lord Kingsland)":
        nom = "PROUT"
        prenom = "Christopher J."
    print(f"{prenom} {nom}")

    photo_url = soup.find("div", {"id": "presentationmep"}).find("div", {"class": "erpl_image-frame"}).find("span").find("img")["src"]
    folder = "../images/parlement_euro/"
    photo = photo_url.split("/")[-1]
    if download_image(photo_url, folder, photo) == 0:
        photo = ""
    groupe = ""
    if soup.find("div", {"id": "presentationmep"}).find("h3", {"class": "sln-political-group-name"}):
        groupe = soup.find("div", {"id": "presentationmep"}).find("h3", {"class": "sln-political-group-name"}).text.strip()
    pays = re.sub(r'[\t\r\n]', '', soup.find("div", {"id": "presentationmep"}).find("div", {"class": "erpl_title-h3"}).text.strip()).split("- ")[0].strip()
    parti_pays = ""
    if len(re.sub(r'[\t\r\n]', '', soup.find("div", {"id": "presentationmep"}).find("div", {"class": "erpl_title-h3"}).text.strip()).split("- ")) == 2:
        parti_pays = re.sub(r'[\t\r\n]', '', soup.find("div", {"id": "presentationmep"}).find("div", {"class": "erpl_title-h3"}).text.strip()).split("- ")[1].split("(")[0].strip()
    date_naissance = None
    lieu_naissance = ""
    if soup.find("div", {"id": "presentationmep"}).find("time"):
        date = soup.find("div", {"id": "presentationmep"}).find("time", {"class": "sln-birth-date"}).text.strip()
        date_naissance = datetime.strptime(date, "%d-%m-%Y")
        if soup.find("div", {"id": "presentationmep"}).find("span", {"class": "sln-birth-place"}):
            lieu_naissance = soup.find("div", {"id": "presentationmep"}).find("span", {"class": "sln-birth-place"}).text.strip()
    mail = ""
    if soup.find("div", {"id": "presentationmep"}).find("a", {"class": "link_email"}):
        mail = soup.find("div", {"id": "presentationmep"}).find("a", {"class": "link_email"})["href"].split(":")[-1].replace("[dot]", ".").replace("[at]", "@")
    twitter = ""
    if soup.find("div", {"id": "presentationmep"}).find("a", {"class": "link_twitt"}):
        twitter = soup.find("div", {"id": "presentationmep"}).find("a", {"class": "link_twitt"})["href"].split("?")[0]
    
    political_group_role = "" #= "Non-inscrits"
    if soup.find("div", {"id": "presentationmep"}).find("p", {"class": "sln-political-group-role"}):
        political_group_role = soup.find("div", {"id": "presentationmep"}).find("p", {"class": "sln-political-group-role"}).text
    
    depute_euro = session.query(DeputesEuro).filter(DeputesEuro.depute_id == depute_id, DeputesEuro.legislature == legislature).first()
    if depute_euro:
        if depute_euro.groupe != groupe:
            depute_euro.groupe = groupe
        session.commit()
        print("Depute data updated successfully.")
        return

    # Store data in the database
    depute = DeputesEuro(
        depute_id=depute_id,
        en_cours=en_cours,
        legislature=legislature,
        nom=nom,
        prenom=prenom,
        fullname=name,
        photo=photo,
        date_naissance=date_naissance,
        lieu_naissance=lieu_naissance,
        date_election=date_debut,
        date_fin_mandat=None,
        raison_fin="",
        pays=pays,
        groupe_pays=parti_pays,
        groupe=groupe,
        mail=mail,
        twitter=twitter
    )
    
    session.add(depute)  # Use merge to update or insert
    session.commit()
    session.close() 

def main():
    # Example URL (replace with target URL)
    legislature = 10
    url = "https://www.europarl.europa.eu/meps/fr/full-list/all"
    # for i in range(1, 10):
    #     url = "https://www.europarl.europa.eu/meps/fr/directory/" + str(i)
    #     print(f"--------------------------legislature: {i}-------------------------")
    #     parse(url, i)
    #url = "https://www.europarl.europa.eu/meps/fr/directory/1"
    parse(url, legislature)
    entrants_sortants(legislature)

if __name__ == "__main__":
    main()