import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime
import re
import time
from urllib.parse import unquote
from pprint import pprint

# Global Variable
legislature = 16
# manque 3781, 3782

# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Votes(Base):
    __tablename__ = 'votes'

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str]
    legislature: Mapped[int]
    pour: Mapped[str]
    contre: Mapped[str]
    abstention: Mapped[str]
    non_votants: Mapped[str]

    def __repr__(self):
        return f"<Votes(id={self.id}, legislature={self.legislature}, numero={self.numero})>"

def parse(url):
    while True:
        response = fetch_url(url)
        soup = BeautifulSoup(response, 'html.parser')
        list = soup.find("section", {"class": "an-section"}).find("ul", {"class": "_centered"}).find_all("a", {"class": "h6"})
        
        for item in list:
            #if check_db(item['href'].split("/")[-3], item['href'].split("/")[-1]) == True:
            if check_db(legislature, item['href'].split("/")[-1]) == True:
                print("already in db")
                #return
                continue

            # if unquote(item['href'].split("/")[-1]) == "c1 - Congrès":
            #     print('test')
            #     continue

            url_scrutin = "https://www.assemblee-nationale.fr" + item["href"]
            parse_vote(unquote(url_scrutin))

        # Loop through all pages
        pagination = soup.find('div', class_='an-pagination')
        next_page_link = pagination.find_all('div')[-1].find('a')

        if next_page_link:
            url = 'https://www2.assemblee-nationale.fr' + next_page_link['href']
        else:
            break

def parse_vote(url):
    response = fetch_url(url)
    if response == None:
            return
    soup = BeautifulSoup(response, 'html.parser')
    groupes = soup.find_all('ul', id=re.compile('^groupe'))

    numero = url.split("/")[-1]
    pprint(numero)
    legislature = int(url.split("/")[-3])
    pour = []
    contre = []
    abstention = []
    non_votants = []
    for groupe in groupes:
        #pprint(groupe.find("h3").text.replace("\n", ""))
        votes = groupe.find('ul').find_all('li', {"class":"relative-flex"})

        #Pour congès / senateurs
        if groupe.find("h3").text.replace("\n", "").split(" ")[-1] == "(Sénat)":
            for vote in votes:
                if vote.find("span", {"class":"h6"}).text == "Pour":
                    for senateur in vote.find_all('li', {"class":"_no-border"}):
                        name = senateur.find('span').text.strip()
                        # Remove the first word
                        remaining_words = name[1:]
                        nom = ' '.join(remaining_words)
                        pour.append(nom)
                if vote.find("span", {"class":"h6"}).text == "Contre":
                    for senateur in vote.find_all('li', {"class":"_no-border"}):
                        name = senateur.find('span').text.strip()
                        # Remove the first word
                        remaining_words = name[1:]
                        nom = ' '.join(remaining_words)
                        contre.append(nom)
                if vote.find("span", {"class":"h6"}).text == "Abstention":
                    for senateur in vote.find_all('li', {"class":"_no-border"}):
                        if senateur.find('span'):
                            name = senateur.find('span').text.strip()
                        if senateur.find('a'):
                            name = senateur.find('a').text.strip()
                        # Remove the first word
                        remaining_words = name[1:]
                        nom = ' '.join(remaining_words)
                        abstention.append(nom)
                if vote.find("span", {"class":"h6"}).text == "Non votant" or vote.text == "Non votants":
                    for senateur in vote.find_all('li', {"class":"_no-border"}):
                        name = senateur.find('span').text.strip()
                        # Remove the first word
                        remaining_words = name[1:]
                        nom = ' '.join(remaining_words)
                        non_votants.append(nom)
            continue

        for vote in votes:
            if vote.find("span", {"class":"h6"}).text == "Pour":
                for depute in vote.find_all('li', {"class":"_no-border"}):
                    if depute.find('a') == None and depute.find('span').text.strip() == "Mme Isabelle Florennes":
                        pour.append("PA721742")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Samantha Cazebonne":
                        pour.append("PA721166")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Philippe Folliot":
                        pour.append("PA267673")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Stéphane Demilly":
                        pour.append("PA267241")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Valérie Boyer":
                        pour.append("PA330684")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Annick Girardin":
                        pour.append("PA337633")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Richard Ferrand":
                        pour.append("PA337633")
                    else:
                        pour.append(depute.find('a')['href'].split('/')[-1])
            if vote.find("span", {"class":"h6"}).text== "Contre":
                for depute in vote.find_all('li', {"class":"_no-border"}):
                    if depute.find('a') == None and depute.find('span').text.strip() == "Mme Isabelle Florennes":
                        contre.append("PA721742")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Samantha Cazebonne":
                        contre.append("PA721166")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Philippe Folliot":
                        contre.append("PA267673")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Stéphane Demilly":
                        contre.append("PA267241")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Valérie Boyer":
                        contre.append("PA330684")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Annick Girardin":
                        contre.append("PA337633")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Richard Ferrand":
                        contre.append("PA337633")
                    else:
                        contre.append(depute.find('a')['href'].split('/')[-1])
            if vote.find("span", {"class":"h6"}).text == "Abstention":
                for depute in vote.find_all('li', {"class":"_no-border"}):
                    if depute.find('a') == None and depute.find('span').text.strip() == "Mme Isabelle Florennes":
                        abstention.append("PA721742")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Samantha Cazebonne":
                        abstention.append("PA721166")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Philippe Folliot":
                        abstention.append("PA267673")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Stéphane Demilly":
                        abstention.append("PA267241")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Valérie Boyer":
                        abstention.append("PA330684")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Annick Girardin":
                        abstention.append("PA337633")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Richard Ferrand":
                        abstention.append("PA337633")
                    else:
                        abstention.append(depute.find('a')['href'].split('/')[-1])
            if vote.find("span", {"class":"h6"}).text == "Non votant" or vote.text == "Non votants":
                for depute in vote.find_all('li', {"class":"_no-border"}):
                    if depute.find('a') == None and depute.find('span').text.strip() == "Mme Yaël Braun-Pivet":
                        non_votants.append("PA721908")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "Mme Annick Girardin":
                        non_votants.append("PA337633")
                    elif depute.find('a') == None and depute.find('span').text.strip() == "M. Richard Ferrand":
                        non_votants.append("PA337633")
                    else:
                        non_votants.append(depute.find('a')['href'].split('/')[-1])

    #open a new database session
    session = Session()
    vote = Votes(
        numero=numero,
        legislature=legislature,
        pour = ','.join(map(str, pour)),
        contre = ','.join(map(str, contre)),
        abstention = ','.join(map(str, abstention)),
        non_votants = ','.join(map(str, non_votants))
    )
    session.add(vote)
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

def check_db(legislature, numero):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Votes.numero)
        .where(Votes.legislature == legislature)
        .where(Votes.numero == numero)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    if len(results) != 0:
        return True
    return False

def get_votes(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Votes.numero)
        .where(Votes.legislature == legislature)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    return results

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    #url = "https://www.assemblee-nationale.fr/dyn/16/scrutins"
    url = "https://www.assemblee-nationale.fr/dyn/" + str(legislature) + "/scrutins"
    parse(url)

if __name__ == "__main__":
    main()
