import requests
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
print(f'composition: {composition}')

# Extract Compte rendus




# Extract Composition
# Extract Compte rendus