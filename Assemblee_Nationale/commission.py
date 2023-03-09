import re
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from soup import make_request
import locale

# Set the locale to French
# Needed to translate date
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

Base = declarative_base()

class Commission(Base):
    __tablename__ = 'groups'

    ids = Column("id", Integer, primary_key=True)
    name = Column("name", String)
    composition = Column("composition", TEXT)
    date = Column("date", DATE)

    def __init__(self, commission):
        self.name = commission["name"]
        self.composition = commission["composition"]
        self.date = commission["date"]

    
    def __repr__(self):
        return f'(Commission {self.name})'

#TODO get old composition with date?
# def to get composition of commission
def composition(url):
    page = make_request(url)
    section = page.find('section', class_='an-section printable')
    div = section.find('div', class_='_gutter-ms _vertical').find_all('div', recursive=False)
    president = div[0].find('span', class_='h5').text.strip()
    #print(president)
    if len(div) == 4:
        vp = div[1].find_all('span', class_='h5')
        vps = vp[0].text.strip()
        for h in vp[1:]:
            vps = vps + ', ' + h.text.strip()
        secretaire = div[2].find_all('span', class_='h5')
        secretaires = secretaire[0].text.strip()
        for h in secretaire[1:]:
            secretaires = secretaires + ', ' + h.text.strip()
        membre = div[3].find_all('span', class_='h5')
        membres = membre[0].text.strip()
        for h in membre[1:]:
            membres = membres + ', ' + h.text.strip()
    elif len(div) == 5:
        rapporteur = div[1].find('span', class_='h5').text.strip()
        #print(rapporteur)
        vp = div[2].find_all('span', class_='h5')
        vps = vp[0].text.strip()
        for h in vp[1:]:
            vps = vps + ', ' + h.text.strip()
        secretaire = div[3].find_all('span', class_='h5')
        secretaires = secretaire[0].text.strip()
        for h in secretaire[1:]:
            secretaires = secretaires + ', ' + h.text.strip()
        membre = div[4].find_all('span', class_='h5')
        membres = membre[0].text.strip()
        for h in membre[1:]:
            membres = membres + ', ' + h.text.strip()
    #print(vps)
    #print(secretaires)
    #print(membres)

def presence(url):
    page = make_request(url)
    iframe = make_request('https://www.assemblee-nationale.fr' + page.find('iframe')['src'])
    presence = iframe.find().find_all('p')
    present = ''
    absent = ''
    assiste = ''
    for x in presence:
        if x.text.strip().startswith("Présent"):
            tmp = x.text.strip().replace('\xa0', ' ')
            present = re.split(' – | – | - | - | - | - ', tmp)[-1]
            print(present)
        elif x.text.strip().startswith("Excus"):
            tmp = x.text.strip().replace('\xa0', ' ')
            absent = re.split(' – | – | - | - | - | - ', tmp)[-1]
            print(absent)
        elif x.text.strip().startswith("Assist"):
            tmp = x.text.strip().replace('\xa0', ' ')
            assiste = re.split(' – | – | - | - | - | - ', tmp)[-1]
            print(assiste)
    return None

def crc(url):
    crc = {}
    while True:
        page = make_request(url)
        test = page.find_all('li', class_='ha-grid-item _size-3')
        for li in test:
            crc['title'] = li.find('span', class_='h5').text.strip()
            print(f'{crc["title"]}')
            date = li.find('span', class_='_colored-primary').text.strip()
            crc['date'] = datetime.strptime(date, "%A %d %B %Y")
            crc['session'] = li.find('span', class_='_colored-travaux').text.strip()
            crc['corps'] = li.find('p').text.strip()
            crc['link'] = 'https://www.assemblee-nationale.fr' + li.find('a')['href']
            crc['presence'] = presence(crc['link'])
        
        # Get next page
        pagination = page.find('div', class_='an-pagination')
        try:
            url = 'https://www2.assemblee-nationale.fr' + pagination.find_all('div')[-1].find('a')['href']
        except:
            url = None
        if url is None:
            break   

def commissions():
    # Start with the first page
    url = 'https://www.assemblee-nationale.fr/dyn/commissions-et-autres-organes'
    # Parse the HTML content
    soup = make_request(url)

    # Get Permanent Commissions
    permanent = soup.find_all('div', class_='section')[2].find_all('a', class_='inner')
    permanent.pop(-1)
    for link in permanent:
        # Extract composition
        url = 'https://www.assemblee-nationale.fr' + link['href']
        page = make_request(url)
        composition_link = 'https://www.assemblee-nationale.fr' + page.find('a', class_='composition-link')['href']
        composition(composition_link)
        # Extract Comptes Rendus
        crc_url = 'https://www.assemblee-nationale.fr' + page.find('section', id='comptes_rendus_des_reunions').find('a', class_='link')['href']
        crc(crc_url)

    # Get all links to the commissions
    # content = soup.find('main')
    # permanent = content.find_all('a', class_="inner")
    # permanent.pop(12)
    # for link in permanent[4:-3]:
    #     if link["href"][0] == "/":
    #         url = 'https://www.assemblee-nationale.fr' + link["href"]
    #     else:
    #         url = link["href"]
        
    #     # Extract Composition
    #     # Parse the HTML content
    #     soup = make_request(url + '/composition')

    #     # Extract Document
    #     # Parse the HTML content
    #     soup = make_request(url + '/documents?typeDocument=crc')

commissions()