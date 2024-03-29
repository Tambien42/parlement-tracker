import requests, re
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from dateutil import parser
import json
import locale

# set the locale to French
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

Base = declarative_base()

class Deputes(Base):
    __tablename__ = 'deputes'

    ids = Column("id", String, primary_key=True, autoincrement=False)
    name = Column("name", String)
    date_election = Column("date_election", DATE)
    date_start = Column("date_start", DATE)
    circonscription = Column("circonscription", String)
    mandat = Column("mandat", String)
    photo = Column("photo", String)
    party = Column("party", String)
    facebook = Column("facebook", String)
    twitter = Column("twitter", String)
    instagram = Column("instagram", String)
    current_commission = Column("current_commission", String)
    birthdate = Column("birthdate", DATE)
    profession = Column("profession", String)
    suppleant = Column("suppleant", String)
    mail = Column("mail", String)
    rattachement_financement = Column("rattachement_financement", String)
    numero_siege = Column("numero_siege", Integer)
    collaborateur = Column("collaborateur", JSON)
    question = Column("question", TEXT)
    rapport = Column("rapport", TEXT)
    proposition_loi_author = Column("proposition_loi_author", TEXT)
    proposition_loi_cosign = Column("proposition_loi_cosign", TEXT)
    commission_participation = Column("commission_participation", TEXT)
    position_vote = Column("position_vote", TEXT)

    def __init__(self, deputes):
        self.ids = deputes["id"]
        self.name = deputes["name"]
        self.date_election = deputes["date_election"]
        self.date_start = deputes["date_start"]
        self.circonscription = deputes["circonscription"]
        self.mandat = deputes["mandat"]
        self.photo = deputes["photo"]
        self.party = deputes["party"]
        self.facebook = deputes["facebook"]
        self.twitter = deputes["twitter"]
        self.instagram = deputes["instagram"]
        self.current_commission = deputes["current_commission"]
        self.birthdate = deputes["birthdate"]
        self.profession = deputes["profession"]
        self.suppleant = deputes["suppleant"]
        self.mail = deputes["mail"]
        self.rattachement_financement = deputes["rattachement_financement"]
        self.numero_siege = int(deputes["numero_siege"])
        self.collaborateur = json.dumps(deputes["collaborateur"])

    
    def __repr__(self):
        return f'(Depute {self.name})'

# SQLAlchemy
engine = create_engine('sqlite:///votes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

URL = 'https://www2.assemblee-nationale.fr/deputes/liste/alphabetique'
# Make a request to the webpage
page = requests.get(URL)
# Parse the HTML content
soup = BeautifulSoup(page.content, 'html.parser')
# Find the div containing the data
content = soup.find('div', {"id": "deputes-list"})

deputes = {}

for div in content.find_all('li'):
    deputes['name'] = div.find('a').text
    deputes['id'] = div.find('a')['href'].split('/')[-1]
    url_depute = 'https://www2.assemblee-nationale.fr' + div.find('a')['href'] + '?force'

    r = requests.get(url_depute)
    s = BeautifulSoup(r.content, 'html.parser')
    fiche = s.find('div', {"id": "deputes-fiche"})

    date = fiche.find('div', {"id": "fonctions-an"}).find('li').get_text().strip()
    date_pattern = r'\d{2}/\d{2}/\d{4}'
    dates = re.findall(date_pattern, date)
    deputes['date_election'] = datetime.strptime(dates[0], "%d/%m/%Y")
    deputes['date_start'] = datetime.strptime(dates[1], "%d/%m/%Y")
    deputes['circonscription'] = fiche.find_all('p', class_='deputy-healine-sub-title')[0].get_text()
    # mandat 'en cours' ou non
    deputes['mandat'] = fiche.find_all('p', class_='deputy-healine-sub-title')[1].get_text()

    deputes['photo'] = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='deputes-image').find('img')['src']

    deputes['party'] = fiche.find('div', {"id": "deputes-illustration"}).find('a').get_text()

    contact = fiche.find('div', {"id": "deputes-contact"})
    deputes['facebook'] = None
    deputes['twitter'] = None
    deputes['instagram'] = None
    if contact.find('a', class_='facebook'):
        deputes['facebook'] = contact.find('a', class_='facebook')['href']
    if contact.find('a', class_='twitter'):
        deputes['twitter'] = contact.find('a', class_='twitter')['href']
    if contact.find('a', class_='instagram'):
        deputes['instagram'] = contact.find('a', class_='instagram')['href']

    deputes['current_commission'] = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[0].find('li').get_text().replace('\xa0', ' ')
    
    date = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[1].find('li').get_text().strip()
    date_pattern = r'\d{1,2} [a-zéû]+ \d{4}'
    #birthdate = parser.parse(re.findall(date_pattern, date)[0], dayfirst=False, fuzzy=True)
    #date_format = "%Y-%m-%d %H:%M:%S"
    #dt = datetime.strptime(str(birthdate), date_format)
    #new_date_format = "%d/%m/%Y"
    #new_birthdate = dt.strftime(new_date_format)
    #deputes['birthdate'] = birthdate.strftime("%d/%m/%Y")
    print(type(deputes["id"]))
    deputes['profession'] = fiche.find('dl', class_='deputes-liste-attributs').find("dt", text="Biographie").find_next_sibling().find_all('li')[1].get_text().strip()
    if fiche.find('dl', class_='deputes-liste-attributs').find("dt", text=re.compile("Suppléant(e)?")):
        deputes['suppleant'] = fiche.find('dl', class_='deputes-liste-attributs').find("dt", text=re.compile("Suppléant(e)?")).find_next_sibling().find('li').get_text()
    else:
        deputes['suppleant'] = ""
    deputes['mail'] = fiche.find('dl', class_='deputes-liste-attributs').find("dt", text="Contact").find_next_sibling().find_all('a')[-1].get_text()
    deputes['rattachement_financement'] = fiche.find('dl', class_='deputes-liste-attributs').find("dt", text="Rattachement au titre du financement de la vie politique ").find_next_sibling().find('li').get_text().strip()
    deputes['declaration_interet'] = fiche.find('dl', class_='deputes-liste-attributs').find("dt", text="Déclaration d’intérêts et d’activités").find_next_sibling().find('a')['href']

    deputes['numero_siege'] = fiche.find('div', {"id": "hemicycle-container"})['data-place']

    collaborateur = []
    co = fiche.find(text=re.compile('Liste des collaborateurs')).parent.parent.parent.find_all('li')
    for c in co:
        collaborateur.append(c.get_text())
    #deputes['collaborateur'] = collaborateur
    
    # Extract number of question
    if fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-question'):
        url_question = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-question').find('a')['data-url']
        page_question = requests.get(url_question)
        pq = BeautifulSoup(page_question.content, 'html.parser')
        
        while True:
            question = pq.find('ul', class_='liens-liste').find_all('li', recursive=False)
            for q in question:
                numero = q.find('h4').get_text()
                link = q.find('ul', class_='liens-liste-embed').find('a')['href']
                rubrique = q.find('p', class_='vues').find('span').get_text()
                titre = q.find('p', class_='vues').find_all('span')[-1].get_text()
                corps = q.find_all('p', recursive=False)[-1].get_text()
                # reponse if reponse save reponse link else 'en attente de réponse'
                if q.find('div', class_='reponse'):
                    reponse =  q.find('div', class_='reponse').find('p').get_text()
                else:
                    reponse = 'en attente de réponse'
            
            pagination = pq.find('div', class_='pagination-bootstrap')
            if pagination:
                next = pagination.find_all('li')[-1].find('a')
                if next:
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_question = requests.get(url_next)
                    pq = BeautifulSoup(page_question.content, 'html.parser')
                else:
                    break
            else:
                break

    # Extract number of report
    # TODO Difference entre Avis et rapport
    if fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-rapport'):
        url_rapport = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-rapport').find('a')['data-url']
        page_rapport = requests.get(url_rapport)
        pr = BeautifulSoup(page_rapport.content, 'html.parser')
    
        while True:
            rapport = pr.find('ul', class_='liens-liste').find_all('li', recursive=False)
            for r in rapport:
                numero = r.find('h4').get_text()
                date = r.find_all('li')[0].get_text()
                link = r.find_all('li')[1].find('a')['href']
                titre = r.find('p').get_text()
            
            pagination = pr.find('div', class_='pagination-bootstrap')
            if pagination:
                if pagination.find_all('li')[-1].find('a'):
                    next = pagination.find_all('li')[-1].find('a')
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_rapport = requests.get(url_next)
                    pr = BeautifulSoup(page_rapport.content, 'html.parser')
                else:
                    break
            else:
                break
    
    # Extract law proposals author
    if fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-ppl'):
        url_ppl = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-ppl').find('a')['data-url']
        page_ppl = requests.get(url_ppl)
        ppl = BeautifulSoup(page_ppl.content, 'html.parser')

        while True:
            proposition = ppl.find('ul', class_='liens-liste').find_all('li', recursive=False)
            for p in proposition:
                numero = p.find('h4').get_text()
                date = p.find_all('li')[0].get_text()
                link = p.find_all('li')[1].find('a')['href']
                corps = p.find('p').get_text()
            
            pagination = ppl.find('div', class_='pagination-bootstrap')
            if pagination:
                if pagination.find_all('li')[-1].find('a'):
                    next = pagination.find_all('li')[-1].find('a')
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_ppl = requests.get(url_next)
                    pp = BeautifulSoup(page_ppl.content, 'html.parser')
                else:
                    break
            else:
                break
    
    # Extract law proposals cosigner
    if fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-pplco'):
        url_pplco = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-pplco').find('a')['data-url']
        page_pplco = requests.get(url_pplco)
        pp = BeautifulSoup(page_pplco.content, 'html.parser')

        while True:
            proposition = pp.find('ul', class_='liens-liste').find_all('li', recursive=False)
            for p in proposition:
                numero = p.find('h4').get_text()
                date = p.find_all('li')[0].get_text()
                link = p.find_all('li')[1].find('a')['href']
                corps = p.find('p').get_text()
            
            pagination = pp.find('div', class_='pagination-bootstrap')
            if pagination:
                if pagination.find_all('li')[-1].find('a'):
                    next = pagination.find_all('li')[-1].find('a')
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_rapport = requests.get(url_next)
                    pp = BeautifulSoup(page_rapport.content, 'html.parser')
                else:
                    break
            else:
                break
    
    # Extract commission involvement
    if fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-crc'):
        url_crc = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-crc').find('a')['data-url']
        page_crc = requests.get(url_crc)
        crc = BeautifulSoup(page_crc.content, 'html.parser')

        while True:
            participation_commission = crc.find('ul', class_='liens-liste').find_all('li', recursive=False)
            for pc in participation_commission:
                numero = pc.find('h4').get_text().strip()
                date = pc.find_all('li')[0].get_text()
                link = pc.find_all('li')[1].find('a')['href']
                resume = pc.find_all('ul')[-1].get_text().strip()
            
            pagination = crc.find('div', class_='pagination-bootstrap')
            if pagination:
                if pagination.find_all('li')[-1].find('a'):
                    next = pagination.find_all('li')[-1].find('a')
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_crc = requests.get(url_next)
                    crc = BeautifulSoup(page_crc.content, 'html.parser')
                else:
                    break
            else:
                break
    
    # Extract vote position
    # list non-votant in scrutinAN_BS.py files
    if fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-wrapvotes'):
        url_votes = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='fonctions-tab-selection').find('li', class_='li-wrapvotes').find('a')['data-url']
        page_votes = requests.get(url_votes)
        vote = BeautifulSoup(page_votes.content, 'html.parser')

        while True:
            votes = vote.find('ul', class_='liens-liste').find_all('li', recursive=False)
            for v in votes:
                numero = v.find_all('li')[0].find('a')['href'].split('/')[-1]
                position_vote = v.find('span', class_='position_vote').get_text()
                date = v.find('h4').find_all('span')[-1].get_text()
                link = v.find_all('li')[0].find('a')['href']
                titre = v.find('h4').get_text().strip()
            
            pagination = v.find('div', class_='pagination-bootstrap')
            if pagination:
                if pagination.find_all('li')[-1].find('a'):
                    next = pagination.find_all('li')[-1].find('a')
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_votes = requests.get(url_next)
                    votes = BeautifulSoup(page_votes.content, 'html.parser')
                else:
                    break
            else:
                break

    # Extract Contributions
    # Store in DB
        depute_info = Deputes(deputes)
        session.add(depute_info)
        session.commit() 

    
    
    
    
