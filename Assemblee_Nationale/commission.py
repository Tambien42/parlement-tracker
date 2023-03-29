import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, DATE, TEXT
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta, date
from soup import make_request
import locale
import signal
import time

class TimeoutError(Exception):
    pass

def handler(signum, frame):
    raise TimeoutError()

# Set the signal handler
signal.signal(signal.SIGALRM, handler)

# Set the locale to French
# Needed to translate date
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# create a database connection
engine = create_engine('sqlite:///votes.db')
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Commission(Base):
    __tablename__ = 'commission'

    ids = Column("id", Integer, primary_key=True)
    name = Column("name", String)
    president = Column("president", TEXT)
    rapporteur = Column("rapporteur", TEXT)
    secretaires = Column("secretaires", TEXT)
    membres = Column("membres", TEXT)
    date = Column("date", DATE)

    def __init__(self, commission):
        self.name = commission["name"]
        self.president = commission["president"]
        self.rapporteur = commission["rapporteur"]
        self.secretaires = commission["secretaires"]
        self.membres = commission["membres"]
        self.date = commission["date"]

    def __repr__(self):
        return f'(Commission {self.name})'

class CommissionWork(Base):
    __tablename__ = 'commission_work'

    ids = Column("id", Integer, primary_key=True)
    commission = Column("commission", String)
    title = Column("title", String)
    date = Column("date", DATE)
    session = Column("session", String)
    corps = Column("corps", TEXT)
    link = Column("link", String)
    present = Column("present", TEXT)
    absent = Column("absent", TEXT)
    assiste = Column("assiste", TEXT)

    def __init__(self, data):
        self.commission = data["commission"]
        self.title = data["title"]
        self.date = data["date"]
        self.session = data["session"]
        self.corps = data["corps"]
        self.link = data["link"]
        self.present = data["present"]
        self.absent = data["absent"]
        self.assiste = data["assiste"]

    def __repr__(self):
        return f'(Compte rendu {self.title})'

#Create the table in the database
Base.metadata.create_all(engine)

def save_compo_to_database(data: dict, Model):
    """
    Save data to a database using the provided session and model.
    :param data: dictionary containing data to be saved
    :param model: SQLAlchemy model class
    :return: None
    """
    # open a new database session
    session = Session()
    commission = session.query(Model).filter(Model.name==data["name"], Model.date <= data["date"]).order_by(Model.date.desc()).first()

    if commission != None:
        # compare all columns except for the date column
        if (commission.name == data['name'] and
            commission.president == data['president'] and
            commission.membres == data['membres'] and
            commission.secretaires == data['secretaires'] and
            commission.rapporteur == data['rapporteur']):
            return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

def save_crc_to_database(data: dict, Model):
    """
    Save data to a database using the provided session and model.
    :param data: dictionary containing data to be saved
    :param model: SQLAlchemy model class
    :return: None
    """
    # open a new database session
    session = Session()
    commission_work = session.query(Model).filter_by(title=data["title"]).order_by(Model.date.desc()).first()
    if commission_work != None:
        # compare all columns except for the date column
        if (commission_work.title == data['title'] and
            commission_work.session == data['session']):
            return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

# def to get composition of commission
def composition(url, date):
    page = make_request(url)
    section = page.find('section', class_='an-section printable')
    div = section.find('div', class_='_gutter-ms _vertical').find_all('div', recursive=False)
    composition = {}
    composition['name'] = page.find('span', class_='h1').text.strip()
    print(composition['name'])
    today = datetime.today().strftime('%d/%m/%Y')
    if date == None:
        composition['date'] = datetime.strptime(today, "%d/%m/%Y")
    else:
        composition['date'] = date
    composition['president'] = div[0].find('span', class_='h5').text.strip()
    composition['rapporteur'] = ''
    if len(div) == 4:
        vp = div[1].find_all('span', class_='h5')
        composition['vps'] = vp[0].text.strip()
        for h in vp[1:]:
            composition['vps'] = composition['vps'] + ', ' + h.text.strip()
        secretaire = div[2].find_all('span', class_='h5')
        composition['secretaires'] = secretaire[0].text.strip()
        for h in secretaire[1:]:
            composition['secretaires'] = composition['secretaires'] + ', ' + h.text.strip()
        membre = div[3].find_all('span', class_='h5')
        composition['membres'] = membre[0].text.strip()
        for h in membre[1:]:
            composition['membres'] = composition['membres'] + ', ' + h.text.strip()
    elif len(div) == 5:
        composition['rapporteur'] = div[1].find('span', class_='h5').text.strip()
        vp = div[2].find_all('span', class_='h5')
        composition['vps'] = vp[0].text.strip()
        for h in vp[1:]:
            composition['vps'] = composition['vps'] + ', ' + h.text.strip()
        secretaire = div[3].find_all('span', class_='h5')
        composition['secretaires'] = secretaire[0].text.strip()
        for h in secretaire[1:]:
            composition['secretaires'] = composition['secretaires'] + ', ' + h.text.strip()
        membre = div[4].find_all('span', class_='h5')
        composition['membres'] = membre[0].text.strip()
        for h in membre[1:]:
            composition['membres'] = composition['membres'] + ', ' + h.text.strip()
    return composition


def presence(url):
    page = make_request(url)
    iframe = make_request('https://www.assemblee-nationale.fr' + page.find('iframe')['src'])
    presence = iframe.find_all('p')
    worker = {}
    worker['present'] = ''
    worker['absent'] = ''
    worker['assiste'] = ''
    for x in presence:
        if x.text.strip().startswith("Présent"):
            tmp = x.text.strip().replace('\xa0', ' ')
            worker['present'] = re.split(' – | – | - | - | - | - ', tmp)[-1]
        elif x.text.strip().startswith("Excus"):
            tmp = x.text.strip().replace('\xa0', ' ')
            worker['absent'] = re.split(' – | – | - | - | - | - ', tmp)[-1]
        elif x.text.strip().startswith("Assist"):
            tmp = x.text.strip().replace('\xa0', ' ')
            worker['assiste'] = re.split(' – | – | - | - | - | - ', tmp)[-1]
    return worker

def crc(url):
    crc = {}
    while True:
        page = make_request(url)
        test = page.find_all('li', class_='ha-grid-item _size-3')
        crc['commission'] = page.find('span', class_='h1').text.strip()
        for li in test:
            crc['title'] = li.find('span', class_='h5').text.strip()
            date = li.find('span', class_='_colored-primary').text.strip()
            crc['date'] = datetime.strptime(date, "%A %d %B %Y")
            crc['session'] = li.find('span', class_='_colored-travaux').text.strip()
            crc['corps'] = li.find('p').text.strip()
            crc['link'] = 'https://www.assemblee-nationale.fr' + li.find('a')['href']
            present = presence(crc['link'])
            crc.update(present)
            save_crc_to_database(crc, CommissionWork)
                
        # Get next page
        pagination = page.find('div', class_='an-pagination')
        try:
            url = 'https://www2.assemblee-nationale.fr' + pagination.find_all('div')[-1].find('a')['href']
        except:
            url = None
        if url is None:
            break   
    return crc

def commissions(list = [], start_date = None, done = False):
    # Set the timeout to 5 seconds
    signal.alarm(30)
    try:
        # Start with the first page
        url = 'https://www.assemblee-nationale.fr/dyn/commissions-et-autres-organes'
        # Parse the HTML content
        soup = make_request(url)

        # Get Permanent Commissions
        permanent = list
        if len(list) == 0:
            permanent = soup.find_all('div', class_='section')[2].find_all('a', class_='inner')
            permanent.pop(-1)
        save = permanent.copy()

        if start_date == None:
                start_date = datetime.strptime("2022-06-30", "%Y-%m-%d").date()
        end_date = date.today()

        for link in permanent:
            # Extract composition
            url = 'https://www.assemblee-nationale.fr' + link['href']
            page = make_request(url)
            #composition_link = 'https://www.assemblee-nationale.fr' + page.find('a', class_='composition-link')['href']
            ### TEMP to get composition through time

            delta = timedelta(days=1)
            if done == False:
                while start_date <= end_date:
                    composition_link = 'https://www.assemblee-nationale.fr' + page.find('a', class_='composition-link')['href'] + '?date=' + start_date.strftime('%d/%m/%Y')
                    ########################
                    compo = composition(composition_link, start_date)
                    save_compo_to_database(compo, Commission)
                    start_date += delta
                
                start_date = datetime.strptime("2022-06-30", "%Y-%m-%d").date()
                end_date = date.today()
            done = True
            
            # Extract Comptes Rendus
            crc_url = 'https://www.assemblee-nationale.fr' + page.find('section', id='comptes_rendus_des_reunions').find('a', class_='link')['href']
            data = crc(crc_url)
            done = False
            save.pop(0)

    except Exception as e:
        print(f'An error occurred, restarting...')
        commissions(save, start_date, done)

    except TimeoutError:
        print("Function timed out! Restarting...")
        commissions(save, start_date, done)

commissions()