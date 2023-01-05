import requests, re
from bs4 import BeautifulSoup

URL = 'https://www2.assemblee-nationale.fr/deputes/liste/alphabetique'
# Make a request to the webpage
page = requests.get(URL)
# Parse the HTML content
soup = BeautifulSoup(page.content, 'html.parser')
# Find the div containing the data
content = soup.find('div', {"id": "deputes-list"})

deputes = []

for div in content.find_all('li'):
    name = div.find('a').text
    url_depute = 'https://www2.assemblee-nationale.fr' + div.find('a')['href']

    #print(f'Name: {name}, Link: {url_depute}')

    r = requests.get(url_depute)
    s = BeautifulSoup(r.content, 'html.parser')
    fiche = s.find('div', {"id": "deputes-fiche"})

    # TODO extract date
    date_election = fiche.find('div', {"id": "fonctions-an"}).find('li').get_text().strip()
    circonscription = fiche.find_all('p', class_='deputy-healine-sub-title')[0].get_text()
    # mandat 'en cours' ou non
    mandat = fiche.find_all('p', class_='deputy-healine-sub-title')[1].get_text()

    photo = 'https://www2.assemblee-nationale.fr' + fiche.find('div', class_='deputes-image').find('img')['src']

    party = fiche.find('div', {"id": "deputes-illustration"}).find('span').get_text()

    # TODO check if personal account
    facebook = fiche.find_all('span', class_='cartouche')[0].find('a')['href']
    twitter = fiche.find_all('span', class_='cartouche')[1].find('a')['href']
    instagram = fiche.find_all('span', class_='cartouche')[2].find('a')['href']

    current_commision = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[0].find('li').get_text()
    # TODO extract date
    birthdate = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[1].find('li').get_text().strip()
    profession = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[1].find_all('li')[1].get_text().strip()
    suppleant = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[2].find('li').get_text()
    mail = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[3].find_all('a')[1].get_text()
    rattachement_financement = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[4].find('li').get_text().strip()
    declaration_interet = fiche.find('dl', class_='deputes-liste-attributs').find_all('dd')[5].find('a')['href']

    numero_siege = fiche.find('div', {"id": "hemicycle-container"})['data-place']

    collaborateur = []
    co = fiche.find(text=re.compile('Liste des collaborateurs')).parent.parent.parent.find_all('li')
    for c in co:
        collaborateur.append(c.get_text())

    #TODO extract commission history and date in fonctions tab
    print(f'date_election: {date_election}')
