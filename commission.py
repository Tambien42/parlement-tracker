import requests, re
from bs4 import BeautifulSoup
from datetime import date

# Commisssion Affaires Culturelles
# Extract Composition
URL = 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-culturelles/composition'
# Make a GET request to the URL
response = requests.get(URL)
# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')
# Extract the rows from the table
container = soup.find('div', class_='antabs-items')
#composition = container.find_all('div', class_='ha-grid-item')
members = container.find('table').find('tbody').find_all('tr')
composition = []
for m in members:
    member = m.find_all('td')[0].find('a').get_text().strip()
    fonction = m.find_all('td')[1].get_text().strip() if m.find_all('td')[1].get_text().strip() else "Membre"
    me = [member, fonction]
    composition.append(me)
date = date.today()

# Extract Compte rendus
URL = 'https://www.assemblee-nationale.fr/dyn/16/organes/commissions-permanentes/affaires-culturelles/documents'
# Make a GET request to the URL
response = requests.get(URL)
# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')
while True:
    list = soup.find('div', {"id": "embedFrame"}).find('ul').find_all('li', recursive=False)
    for l in list:
        title = l.find('span', class_='h5').text
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
            presence = soup2.find(text=re.compile('Présents')).parent.parent.text.strip().replace('\xa0', ' ').replace('–', '-').split(' - ').pop().split(', ')
            absence = soup2.find(text=re.compile('Excusés'))
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
