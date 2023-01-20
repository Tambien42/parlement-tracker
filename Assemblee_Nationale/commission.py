import requests, re
from bs4 import BeautifulSoup
from datetime import date

commissions = [
    ['Commission des affaires culturelles et de l\'éducation', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-culturelles/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-culturelles/documents?typeDocument=crc'],
    ['Commission des affaires économiques', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-economiques/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-economiques/documents?typeDocument=crc'],
    ['Commission des affaires étrangères', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-etrangeres/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-etrangeres/documents?typeDocument=crc'],
    ['Commission des affaires sociales', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-sociales/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-sociales/documents?typeDocument=crc'],
    ['Commission de la défense nationale et des forces armées', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/defense/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/defense/documents?typeDocument=crc'],
    ['Commission du développement durable et de l\'aménagement du territoire', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/developpement-durable/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/developpement-durable/documents?typeDocument=crc'],
    ['Commission des finances', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/finances/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/finances/documents?typeDocument=crc'],
    ['Commission des lois', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/lois/composition', 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/lois/documents?typeDocument=crc']
]

for commission in commissions:
    # Extract Composition
    URL = commission[1]
    # Make a GET request to the URL
    response = requests.get(URL)
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    # Extract the rows from the table
    container = soup.find('div', class_='antabs-items')
    name = commission[0]
    members = container.find('table').find('tbody').find_all('tr')
    composition = []
    for m in members:
        member = m.find_all('td')[0].find('a').get_text().strip()
        fonction = m.find_all('td')[1].get_text().strip() if m.find_all('td')[1].get_text().strip() else "Membre"
        me = [member, fonction]
        composition.append(me)

    # Extract Compte rendus
    URL = commission[2]
    # Make a GET request to the URL
    response = requests.get(URL)
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    while True:
        list = soup.find('div', {"id": "embedFrame"}).find('ul').find_all('li', recursive=False)
        for l in list:
            title = l.find('span', class_='h5').text
            session = l.find('span', class_='_colored-travaux')
            if session:
                s = session.text
            else:
                s = ''
            date = l.find('span', class_='_colored-primary').text
            corps = l.find('p').text
            link = l.find('a')['href']
            type = link.split('/')[3]
            # Extract participation
            if type == 'comptes-rendus':
                url_cr = 'https://www.assemblee-nationale.fr' + link
                response1 = requests.get(url_cr)
                soup1 = BeautifulSoup(response1.content, 'html.parser')
                url_iframe = 'https://www.assemblee-nationale.fr' + soup1.find('iframe')['src']
                response2 = requests.get(url_iframe)
                soup2 = BeautifulSoup(response2.content, 'html.parser')
                presence = soup2.find(text=re.compile('Présent')).parent.parent.text.strip().replace('\xa0', ' ').replace('–', '-').split(' - ').pop().split(', ')
                absence = soup2.find(text=re.compile('Excusé'))
                if absence:
                    abs = absence.parent.parent.text.strip().replace('\xa0', ' ').replace('–', '-').split(' - ').pop().split(', ')
                assistance = soup2.find(text=re.compile('également à la réunion'))
                if assistance:
                    a = assistance.parent.parent.text.strip().replace('\xa0', ' ').replace('–', '-').split(' - ').pop().split(', ')
        
        pagination = soup.find('div', class_='an-pagination')
        if pagination:
            next = pagination.find_all('div')[-1].find('a')
            if next:
                url_next = 'https://www2.assemblee-nationale.fr' + next['href']
                page_question = requests.get(url_next)
                soup = BeautifulSoup(page_question.content, 'html.parser')
            else:
                break
        else:
            break
