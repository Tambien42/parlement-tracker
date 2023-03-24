import re
from sqlalchemy import create_engine, Column, String, DATE, Integer, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from soup import make_request
import locale, time

# Set the locale to French
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# create a database connection
engine = create_engine('sqlite:///votes.db')
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Deputes(Base):
    __tablename__ = 'deputes'

    id_ = Column("id", String, primary_key=True, autoincrement=False)
    name = Column("name", String)
    photo = Column("photo", String)
    group = Column("group", String)
    mandat_fin = Column("mandat_fin", DATE)
    raison = Column("raison", String)
    birthdate = Column("birthdate", DATE)
    profession = Column("profession", String)
    commission = Column("commission", String)
    suppleant = Column("suppleant", String)
    rattachement_finance = Column("rattachement_finance", String)
    circonscription_adress = Column("circonscription_adress", String)
    circonscription = Column("circonscription", String)
    siege_number = Column("siege_number", Integer)
    mail = Column("mail", String)
    twitter = Column("twitter", String)
    facebook = Column("facebook", String)
    instagram = Column("instagram", String)
    linkedin = Column("linkedin", String)
    lien_interet = Column("line_interet", String)
    collaborateurs = Column("collaborateurs", String)
    date_election = Column("date_election", DATE)
    date_debut_mandat = Column("date_debut_mandat", DATE)
    position_vote = Column("position_vote", Text)
    questions = Column("questions", Text)
    rapports = Column("rapports", Text)
    law_author = Column("law_author", Text)
    law_cosigner = Column("law_cosigner", Text)
    commission_presence = Column("commission_presence", Text)

    def __init__(self, deputes):
        self.id_ = deputes["id"]
        self.name = deputes["name"]
        self.photo = deputes["photo"]
        self.group = deputes["group"]
        self.mandat_fin = deputes["mandat_fin"]
        self.raison = deputes["raison"]
        self.birthdate = deputes["birthdate"]
        self.profession = deputes["profession"]
        self.commission = deputes["current_commission"]
        self.suppleant = deputes["suppleant"]
        self.rattachement_finance = deputes["rattachement_finance"]
        self.circonscription_adress = deputes["circonscription_adress"]
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
        self.position_vote = deputes['vote_depute']
        self.questions = deputes['questions_depute']
        self.rapports = deputes['rapports_depute']
        self.law_author = deputes['author_depute']
        self.law_cosigner = deputes['cosigner_depute']
        self.commission_presence = deputes['commission_depute']
    
    def __repr__(self):
        return f'(Depute {self.name})'

#Create the table in the database
Base.metadata.create_all(engine)
def update_example(name, value):
    session = Session()

    # Check if the data is in the database
    data = session.query(Example).filter(Example.name == name).first()
    if data:
        # If the data is in the database and the value has changed, modify it
        if data.value != value:
            data.value = value
            session.commit()
            print("Data modified successfully")
        else:
            print("Data already exists and has not changed")
    else:
        # If the data is not in the database, add it
        data = Example(name=name, value=value)
        session.add(data)
        session.commit()
        print("Data added successfully")
        
def save_to_database(data: dict, Model):
    """
    Save data to a database using the provided session and model.
    :param data: dictionary containing data to be saved
    :param model: SQLAlchemy model class
    :return: None
    """
    # open a new database session
    session = Session()
    # retrieve the row you want to check by its id and sort it by date
    depute = session.query(Model).filter_by(ids=data["ids"]).first()
    if depute:
        return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

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
#TODO replace full questions title by id ?
def depute_questions(url):
    table = []
    while True:
        soup = make_request(url)
        list = soup.find('div', class_='embed-search-result').find('ul').find_all('li', recursive=False)
        for li in list:
            table.append(li.find("a").text.strip())
            print(li.find("a").text.strip())
            print(li.find("a")['href'].split('/')[-1].split('.')[0])

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
        name = soup.find("h1").text.strip()
        list = soup.find_all('section')[-1].find('ul').find_all('li', recursive=False)
        for li in list:
            url_cr = 'https://www2.assemblee-nationale.fr' + li.find("a")['href']
            cr = make_request(url_cr)
            iframe = cr.find('iframe')
            table = []
            if iframe:
                url_iframe = 'https://www.assemblee-nationale.fr' + iframe['src']
                page = make_request(url_iframe)
                presence = page.find_all('p')
                for x in presence:
                    if x.text.strip().startswith("Présent"):
                        tmp = x.text.strip().replace('\xa0', ' ').split(', ')
                        if name in tmp or name in tmp[0]:
                            table.append(li.find("a").text.strip())
            else:
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
        list = soup.find('div', class_='embed-search-result').find('ul').find_all('li', recursive=False)
        for li in list:
            numero = li.find('a')['href'].split('/')[-1]
            position = li.find("span", class_="h6").text.strip()
            if len(li.find_all("span", class_="h6")) == 3:
                position = li.find_all("span", class_="h6")[-1].text.strip()
            vote = numero + '-' + position
            table.append(vote)

        # Get next page
        url = next_page_an(soup)
        if url is None:
            break 
    return ', '.join(table)

#TODO return data
# Extract all travaux parlementaires
def travaux(id_):
    url  = 'https://www2.assemblee-nationale.fr/dyn/deputes/' + id_ + '/travaux-parlementaires'
    soup = make_request(url)

    section = soup.find('section', id='actualite_parlementaire').find('div', class_='ha-grid').find_all('div', class_='ha-grid-item')
    questions_depute = ''
    rapports_depute = ''
    author_depute = ''
    cosigner_depute = ''
    for type in section:
        title = type.find("div", class_="bloc-title").text.strip()
        url = 'https://www2.assemblee-nationale.fr' + type.find('a')['href']

        if title == 'Questions':
            questions_depute = depute_questions(url)
        
        # if title == 'Rapports':
        #     rapports_depute = depute_rapports(url)
       
        # if title == 'Propositions (auteur)':
        #     author_depute = depute_author(url)

        # if title == 'Propositions (cosignataire)':
        #     cosigner_depute = depute_cosigner(url)

    section = soup.find('main').find_all('section')[-1].find('div', class_='ha-grid').find_all('div', class_='ha-grid-item')
    commission_depute = ''
    votes_depute = ''
    for type in section:
        title = type.find("div", class_="bloc-title").text.strip()
        url = 'https://www2.assemblee-nationale.fr' + type.find('a')['href']
        
        # Seance Publique not extracted not relevent for my work
        # if title == 'Séance Publique':
        #     seance = 'Not Done'
        
        # if title == 'Commission':
        #     commission_depute = depute_commission(url)
        
        # if title == 'Positions de vote':
        #     votes_depute = depute_votes(url)

    return questions_depute, rapports_depute, author_depute, cosigner_depute, commission_depute, votes_depute

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

#TODO save old deputes in db
# get info on deputes that have resigned before launching the project
# find the name https://www.nosdeputes.fr/deputes
def old_deputes():
    url = 'https://www.nosdeputes.fr/deputes'
    soup = make_request(url)
    old = soup.find_all('div', class_='anciens')
    list = []
    for i in old:
        url = 'https://www.nosdeputes.fr' + i.parent['href']
        name = i.parent.find_all("span")[1].text.strip()
        soup = make_request(url)
        href = soup.find('div', class_='contenu_depute').find('div', id='b1').find('ul').find('ul').find('li').find('a')['href']
        list.append(href)
    return list

#TODO function to check if id in database skip info gathering except travaux parlemantaire
#TODO and check if depute hasn't resigned or changed commission add db column date_end_mandat
# Extract all deputes informations
def deputes():
    # Start with the first page
    url = 'https://www2.assemblee-nationale.fr/deputes/liste/alphabetique'

    # Parse the HTML content
    soup = make_request(url)
     # Find the table containing the data
    table = soup.find('div', id='deputes-list').find_all('li')
    #list = old_deputes()
    #TODO get list from url + get old depute from database
    #TODO get all ids from database and compare with list merge the two removing doublon
    list = []
    for li in table:
       list.append(li.find('a')['href'].split('/')[-1])
    
    #list = ['OMC_PA605036', 'OMC_PA722190']
    depute = {}
    for fiche in list:
        url = 'https://www2.assemblee-nationale.fr/deputes/fiche/' + fiche
        soup = make_request(url)

        # Extract depute info
        depute['name'] = soup.find("h1").text.strip()
        print(f'{depute["name"]}')
        depute['id'] = soup.find("h1").parent['href'].split('/')[-1]
        #TODO download photo and store path
        depute['photo'] = soup.find('div', class_='acteur-photo-image').find('img')['src']
        depute['group'] = soup.find("a", class_='h4').text.strip()
        mandat = soup.find('section').find_all('div')[-1].find_all('span')[-1].text.replace('|', '').strip()
        if mandat == 'Mandat en cours':
            depute['mandat_fin'] = ''
            depute['raison'] = ''

            section2 = soup.find_all('section')[1]
            info = section2.find('div', class_='ha-grid-item').find('div', class_='bloc-content').find_all('span', class_='h5')
            depute['birthdate'] = ''
            depute['current_commission'] = ''
            depute['suppleant'] = ''
            depute['rattachement_finance'] = ''
            depute['circonscription_adress'] = ''
            for i in info:
                if i.text.strip().startswith("Biographie"):
                    date = i.parent.find('p').text.replace(')', ')$').split('$')[0].strip()
                    match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', date)
                    if match:
                        birth = match.group()
                        depute['birthdate'] = datetime.strptime(birth, "%d %B %Y")
                    depute['profession'] = i.parent.find('p').text.replace(')', ')$').split('$')[1].strip()
                
                #TODO get old commissions and dates
                if i.text.strip().startswith("Commission"):
                    depute['current_commission'] = i.parent.find('a').text.strip()
                
                if i.text.strip().startswith("Suppléant"):
                    depute['suppleant'] = i.parent.find_all('span')[-1].text.strip()
                
                if i.text.strip().startswith("Rattachement"):
                    depute['rattachement_finance'] = i.parent.find_all('span')[-1].text.strip()
                
                if i.text.strip().startswith("Adresse"):
                    adresses = i.parent.find('ul').find_all('li')
                    for a in adresses:
                        if a.find('span') and a.find('span').text.strip().startswith("En circonscription"):
                            depute["circonscription_adress"] = a.find_all('span')[-1].text.strip()
                
                departement = section2.find_all('div', class_='ha-grid-item')[1].find_all('a')[-1]['href'].split('/')[-1].split('?')[0].strip()
                circonscription_number = section2.find_all('div', class_='ha-grid-item')[1].find_all('a')[-1]['href'].split('/')[-1].split('=')[-1].strip()
                depute['circonscription'] = departement + '-' + circonscription_number
                depute['siege_number'] = ''
                if soup.find('a', href=re.compile("/dyn/hemicycle")):
                    depute['siege_number'] = soup.find('a', href=re.compile("/dyn/hemicycle"))['href'].split('=')[-1].strip()
                depute['mail'] = ''
                if soup.find('a', href=re.compile("mailto")):
                    depute['mail'] = soup.find('a', href=re.compile("mailto"))['href'].split(':')[-1]

                depute['twitter'] = ''
                depute['facebook'] = ''
                depute['instagram'] = ''
                depute['linkedin'] = ''
                if soup.find('div', class_='right-menu'):
                    for i in soup.find("div", class_="right-menu").find_all("li"):
                        if i.find("i")["class"][-1].split("-")[-1] == 'twitter':
                            depute['twitter'] = i.find('a')['href'].strip() 
                        if i.find("i")["class"][-1].split("-")[-1] == 'facebook':
                            depute['facebook'] = i.find('a')['href'].strip()
                        if i.find("i")["class"][-1].split("-")[-1] == 'instagram':
                            depute['instagram'] = i.find('a')['href'].strip() 
                        if i.find("i")["class"][-1].split("-")[-1] == 'linkedin':
                            depute['linkedin'] = i.find('a')['href'].strip()
                
                depute['lien_interet'] = soup.find('div', text=re.compile("Consulter la déclaration")).parent.parent.find('a')['href'].strip()
                collabo = soup.find('span', text=re.compile("Collaborateurs")).parent.find_all('li')
                depute['collaborateurs'] = collabo[0].text.strip()
                for c in collabo[1:]:
                    depute['collaborateurs'] = depute['collaborateurs'] + ', ' + c.text.strip()
        else:
            item = soup.find('span', text=re.compile("Date de fin de mandat"))
            date = item.parent.find_all('span')[-1].text.replace('(', '|').replace(')', '').strip().split('|')[0]
            # Define regular expression pattern to match the date
            pattern = r"(\d{1,2}\s\w+\s\d{4})"
            # Find the date in the string
            match = re.search(pattern, date)
            if match:
                str = match.group(1)
                date = datetime.strptime(str, "%d %B %Y")
            else:
                # handle the case where the regex didn't match
                date = None
                depute['mandat_fin'] = date
                depute['raison'] = item.parent.find_all('span')[-1].text.replace('(', '|').replace(')', '').strip().split('|')[1]
            
            section2 = soup.find_all('section')[1]
            info = section2.find('div', class_='ha-grid-item').find('div', class_='bloc-content').find_all('span', class_='h5')
            depute['birthdate'] = ''
            depute['current_commission'] = ''
            depute['suppleant'] = ''
            depute['rattachement_finance'] = ''
            depute['circonscription_adress'] = ''
            for i in info:
                if i.text.strip().startswith("Biographie"):
                    date = i.parent.find('p').text.replace(')', ')$').split('$')[0].strip()
                    match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', date)
                    if match:
                        birth = match.group()
                        depute['birthdate'] = datetime.strptime(birth, "%d %B %Y")
                    depute['profession'] = i.parent.find('p').text.replace(')', ')$').split('$')[1].strip()
            
            depute['circonscription'] = ''
            depute['siege_number'] = ''
            depute['mail'] = ''
            depute['twitter'] = ''
            depute['facebook'] = ''
            depute['instagram'] = ''
            depute['linkedin'] = ''
            depute['lien_interet'] = ''
            depute['collaborateurs'] = ''

        # Extract Election Date
        #depute['date_election'], depute['date_debut_mandat'] = dmandat(depute['id'])

        # Extract Travaux Parlementaires
        depute['questions_depute'], depute['rapports_depute'], depute['author_depute'], depute['cosigner_depute'], depute['commission_depute'],depute['vote_depute'] = travaux(depute['id'])
        #save_to_database(depute, Deputes)

        
deputes()