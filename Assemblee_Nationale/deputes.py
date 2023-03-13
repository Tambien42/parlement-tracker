import re
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from soup import make_request, next_page
import locale

# Set the locale to French
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

Base = declarative_base()

class Deputes(Base):
    __tablename__ = 'deputes'

    ids = Column("id", String, primary_key=True, autoincrement=False)
    name = Column("name", String)
    photo = Column("photo", String)
    group = Column("group", String)
    mandat = Column("mandat", String)
    birthdate = Column("birthdate", DATE)
    profession = Column("profession", String)
    commission = Column("commission", String)
    suppleant = Column("suppleant", String)
    rattachement_finance = Column("rattachement_finance", String)
    an_adress = Column("an_adress", String)
    circonscription = Column("circonscription", String)
    siege_number = Column("siege_number", INTEGER)
    mail = Column("mail", String)
    twitter = Column("twitter", String)
    facebook = Column("facebook", String)
    instagram = Column("instagram", String)
    linkedin = Column("linkedin", String)
    lien_interet = Column("line_interet", String)
    collaborateurs = Column("collaborateurs", String)
    date_election = Column("date_election", DATE)
    date_debut_mandat = Column("date_debut_mandat", DATE)
    #TODO Store Travaux Parlementaire

    def __init__(self, deputes):
        self.ids = deputes["ids"]
        self.name = deputes["name"]
        self.photo = deputes["photo"]
        self.group = deputes["group"]
        self.mandat = deputes["mandat"]
        self.birthdate = deputes["birthdate"]
        self.profession = deputes["profession"]
        self.commission = deputes["commission"]
        self.suppleant = deputes["suppleant"]
        self.rattachement_finance = deputes["rattachement_finance"]
        self.an_adress = deputes["an_adress"]
        self.circonscription = deputes["circonscription"]
        self.siege_number = deputes["siege_number"]
        self.mail = deputes["mail"]
        self.twitter = deputes["twitter"]
        self.facebook = deputes["facebook"]
        self.instagram = deputes["instagram"]
        self.linkedin = deputes["linkedin"]
        self.lien_interet = deputes["lien_interet"]
        self.collaborateurs = deputes["collaborateurs"]
        self.date_election = deputes["date_election"]
        self.date_debut_mandat = deputes["date_debut_mandat"]
    
    def __repr__(self):
        return f'(Depute {self.name})'

# modified version because different class name
def next_page_an(page):
    try:
        pagination = page.find('div', class_='an-pagination')
        return (
            'https://www2.assemblee-nationale.fr' + pagination.find_all('div')[-1].find('a')['href']
        )
    except:
        return None

# Extract questions from a depute
def depute_questions(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            table.append(li.find("a").text.strip())

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

# Extract reports from a depute
def depute_rapports(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            table.append(li.find("a").text.replace('\n', '').strip())

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

# Extract law proposals authoe from a depute
def depute_author(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            table.append(li.find("a").text.strip())

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

# Extract law proposals cosigner from a depute
def depute_cosigner(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            table.append(li.find("a").text.strip())

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

# Extract commission presence from a depute
def depute_commission(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            table.append(li.find("a").text.strip())

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

#TODO get non votant status for some deputes
# Extract vote positions from a depuet
def depute_votes(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            numero = li.find("div", class_="flex1").find_all('span')[-1].text.split('-')[0].split('°')[-1].strip()
            position = li.find("span", class_="h6").text.strip()
            vote = numero + '-' + position
            table.append(vote)

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

#TODO return data
# Extract all travaux parlementaires
def travaux(ids):
    url  = 'https://www2.assemblee-nationale.fr/dyn/deputes/' + ids + '/travaux-parlementaires'
    soup = make_request(url)

    section = soup.find('section', id='actualite_parlementaire').find('div', class_='ha-grid').find_all('div', class_='ha-grid-item')
    for type in section:
        title = type.find("div", class_="bloc-title").text.strip()
        url = 'https://www2.assemblee-nationale.fr' + type.find('a')['href']

        questions_depute = ''
        if title == 'Questions':
            questions_depute = depute_questions(url)
        
        rapports_depute = ''
        if title == 'Rapports':
            rapports_depute = depute_rapports(url)
       
        author_depute = ''
        if title == 'Propositions (auteur)':
            author_depute = depute_author(url)
       
        if title == 'Propositions (cosignataire)':
            cosigner_depute = depute_cosigner(url)

    section = soup.find('main').find_all('section')[-1].find('div', class_='ha-grid').find_all('div', class_='ha-grid-item')
    for type in section:
        title = type.find("div", class_="bloc-title").text.strip()
        url = 'https://www2.assemblee-nationale.fr' + type.find('a')['href']
        
        # Seance Publique not extracted not relevent for my work
        # if title == 'Séance Publique':
        #     seance = 'Not Done'
        
        commission_depute = ''
        if title == 'Commission':
            commission_depute = depute_commission(url)
        
        commission_depute = ''
        if title == 'Positions de vote':
            votes_depute = depute_votes(url)
    return None

# Extract date of election and date of debut
def dmandat(ids):
    url = 'https://www2.assemblee-nationale.fr/dyn/deputes/' + ids + '/fonctions'
    soup = make_request(url)
    dates = soup.find('div', class_='page-content').find_all('ul')[1].find_all('li')[0].find_all('span')[-1].text.strip().split('-')
    election = dates[0].strip()
    match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', election)
    date_election = ''
    if match:
        d_election = match.group()
        date_election = datetime.strptime(d_election, "%d %B %Y")
    debut_mandat = dates[1].strip()
    match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', debut_mandat)
    date_debut_mandat = ''
    if match:
        date_mandat = match.group()
        date_debut_mandat = datetime.strptime(date_mandat, "%d %B %Y")
    return date_election, date_debut_mandat

#TODO return data from travaux parlementaires
# Extract all deputes informations
def deputes():
    # Start with the first page
    url = 'https://www2.assemblee-nationale.fr/deputes/liste/alphabetique'

    # Parse the HTML content
    soup = make_request(url)
    # Find the table containing the data
    list = soup.find('div', id='deputes-list').find_all('li')

    for depute in list:
        url = 'https://www2.assemblee-nationale.fr' + depute.find('a')['href']
        soup = make_request(url)

        # Extract depute info
        ids = soup.find('section', class_='an-section').find("a")['href'].split('/')[-1]
        name = soup.find("h1").text.strip()
        #TODO download photo
        photo = soup.find('div', class_='acteur-photo-image').find('img')['src']
        group = soup.find("a", class_='h4').text.strip()
        mandat = soup.find('section').find_all('div')[-1].find_all('span')[-1].text.replace('|', '').strip()
        section2 = soup.find_all('section')[1]
        info = section2.find('div', class_='ha-grid-item').find('div', class_='bloc-content').find_all('span', class_='h5')
        date = info[0].parent.find('p').text.replace(')', ')$').split('$')[0].strip()
        match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', date)
        birthdate = ''
        if match:
            birth = match.group()
            birthdate = datetime.strptime(birth, "%d %B %Y")
        profession = info[0].parent.find('p').text.replace(')', ')$').split('$')[1].strip()
        #TODO check if changed commission
        current_commission = info[1].parent.find('a').text.strip()
        if len(info) == 4:
            suppleant = ''
            rattachement_finance = info[2].parent.find_all('span')[-1].text.strip()
            adresses = info[3].parent.find_all('li')
        else:
            suppleant = info[2].parent.find_all('span')[-1].text.strip()
            rattachement_finance = info[3].parent.find_all('span')[-1].text.strip()
            adresses = info[4].parent.find_all('li')
        an_adress = adresses[0].find('span').text.strip()
        departement = section2.find_all('div', class_='ha-grid-item')[1].find_all('a')[-1]['href'].split('/')[-1].split('?')[0].strip()
        circonscription_number = section2.find_all('div', class_='ha-grid-item')[1].find_all('a')[-1]['href'].split('/')[-1].split('=')[-1].strip()
        circonscription = departement + '-' + circonscription_number
        siege_number = section2.find_all('div', class_='ha-grid-item')[2].find_all('a')[-1]['href'].split('=')[-1].strip()
        mail = section2.find('ul', class_='pipe-list').find('a')['href'].split(':')[-1].strip()
        twitter = ''
        facebook = ''
        instagram = ''
        linkedin = ''
        if soup.find('div', class_='right-menu'):
            for i in soup.find("div", class_="right-menu").find_all("li"):
                if i.find("i")["class"][-1].split("-")[-1] == 'twitter':
                    twitter = i.find('a')['href'].strip() 
                if i.find("i")["class"][-1].split("-")[-1] == 'facebook':
                    facebook = i.find('a')['href'].strip()
                if i.find("i")["class"][-1].split("-")[-1] == 'instagram':
                    instagram = i.find('a')['href'].strip() 
                if i.find("i")["class"][-1].split("-")[-1] == 'linkedin':
                    linkedin = i.find('a')['href'].strip()
        lien_interet = section2.find_all('div', class_='ha-grid-item')[4].find('a')['href'].strip()
        collabo = section2.find_all('div')[-1].find_all('li')
        collaborateurs = collabo[0].text.strip()
        for c in collabo:
            collaborateurs = collaborateurs + ', ' + c.text.strip()

        print(f'{name}')
        # Extract Election Date
        date_election, date_debut_mandat = dmandat(ids)

        # Extract Travaux Parlementaires
        data = travaux(ids)
        