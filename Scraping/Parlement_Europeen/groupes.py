import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date
import time
import re
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# Global Variable
legislature = 10

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class GroupesEuro(Base):
    __tablename__ = 'groupes_europeens'

    id: Mapped[int] = mapped_column(primary_key=True)
    groupe_id: Mapped[str]
    nom: Mapped[str]
    abbreviation: Mapped[str]
    date: Mapped[datetime]
    membres: Mapped[str]
    legislature: Mapped[int]

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

def parse(url):
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')

    list = soup.find("select", {"id": "politicalGroupSelect"}).find_all("option")
    for groupe in list:
        if groupe["value"] == "":
            continue
        url = "https://www.europarl.europa.eu/meps/en/search/advanced?euPoliticalGroupBodyRefNum=" + groupe["value"] + "&bodyType=ALL"
        parse_groupe(url)

def parse_groupe(url):
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')

    # Parse the URL
    parsed_url = urlparse(url)
    # Extract the query parameters
    query_params = parse_qs(parsed_url.query)
    groupe_id = query_params.get('euPoliticalGroupBodyRefNum', [None])[0]
    nom = soup.find("select", {"id": "politicalGroupSelect"}).find("option", {"value": groupe_id}).text.strip()
    abbreviation = ""
    list = soup.find("div", {"class": "erpl_member-list"}).find_all("a")
    members = []
    for mep in list:
        members.append(mep["href"].split("/")[-1])

    url = "https://www.europarl.europa.eu/meps/en/search/table"
    content = fetch_url(url)
    soup = BeautifulSoup(content, 'html.parser')
    row = soup.find("div", {"class": "table-responsive"}).find("tbody").find_all("tr")[-1].find_all("td")
    for r in row:
        if r.find("a"):
            # Parse the URL
            parsed_url = urlparse(r.find("a")["href"])
            # Extract the query parameters
            query_params = parse_qs(parsed_url.query)
            id_num= query_params.get('euPoliticalGroupBodyRefNum', [None])[0]
            if id_num == groupe_id:
                abbreviation = r["data-th"].split(":")[0].strip()

    groupe_euro = session.query(GroupesEuro).filter(GroupesEuro.groupe_id == groupe_id, GroupesEuro.legislature == legislature).first()
    if groupe_euro:
        print(f"No changes in {nom}.")
        return
    
    print("-------------------------------------------")
    print(f"{groupe_id} {nom} {abbreviation} {members}")
    
    groupe = GroupesEuro(
        nom=nom,
        groupe_id=groupe_id,
        abbreviation=abbreviation,
        legislature=legislature,
        date=date.today(),
        membres = ','.join(map(str, members)),
    )
    session.add(groupe)
    session.commit()
    session.close()
        
# TODO split the members betwenn president, vp, bureau...
fonctions = []
fonctions = ['Membre',
 'Membre du bureau',
 'Vice-président',
 '', #Non-inscrits
 'Trésorier',
 'Coprésidente',
 'Coprésident',
 'Président',
 'Vice-présidente',
 'Première vice-présidente/Membre du bureau',
 'Présidente',
 'Cotrésorier',
 'Trésorière']
# def parse(url):
#     content = fetch_url(url)
#     soup = BeautifulSoup(content, 'html.parser')

#     list = soup.find("div", {"class": "erpl_member-list"}).find_all("a")
#     for mep in list:
#         url = mep["href"]
#         parse_groupe(url)

# def parse_groupe(url):
#     content = fetch_url(url)
#     soup = BeautifulSoup(content, 'html.parser')

#     legislature = 0
#     nom = soup.find("span", {"class": "sln-member-name"}).text.strip()
#     #pprint(nom)
#     groupe = soup.find("h3", {"class": "sln-political-group-name"}).text.strip()
    
#     political_group_role = "" #= "Non-inscrits"
#     if soup.find("p", {"class": "sln-political-group-role"}):
#         political_group_role = soup.find("p", {"class": "sln-political-group-role"}).text
#     print(f"{nom} - {groupe}: {political_group_role}")
#     # if political_group_role not in fonctions:
#     #     fonctions.append(political_group_role)
#     # pprint(fonctions)
    
def main():
    # Example URL (replace with target URL)
    #url = "https://www.europarl.europa.eu/meps/fr/full-list/all"
    url = "https://www.europarl.europa.eu/meps/en/search/advanced"
    parse(url)

if __name__ == "__main__":
    main()