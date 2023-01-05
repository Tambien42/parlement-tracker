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

    # Extract Rapport
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
                print(f'name: {name}, numero: {numero}, date: {date}, link: {link}, titre: {titre}')
            
            pagination = pr.find('div', class_='pagination-bootstrap')
            if pagination:
                if pagination.find_all('li')[-1].find('a'):
                    next = pagination.find_all('li')[-1].find('a')
                    url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                    page_rapport = requests.get(url_next)
                    pq = BeautifulSoup(page_rapport.content, 'html.parser')
                else:
                    break
            else:
                break

    
    
    
    
