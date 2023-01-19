import requests
from bs4 import BeautifulSoup

URL = 'https://www2.assemblee-nationale.fr/recherche/resultats_questions/'
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

while True:
    # Find all the rows in the table
    rows = soup.find('table').find('tbody').find_all('tr')
    # Iterate over the rows
    for row in rows:
        column = row.find_all('td')
        # Extract Link
        link = column[0].find('a')['href']
        # Extract the type of question
        type = column[0].find('strong').text.split('-')[1].split(' ')[1]
        # Extract the title
        number = column[0].find('strong').text.split('-')[1].split(' ')[2]
        # Extract legislature
        legislature = column[0].find('strong').text.split('-')[0].split(' ')[0]
        # Extract name of person who asked the question
        name = column[1].find('strong').text
        # Extract title
        title = column[1].find('em').text
        # Extract concerned ministry
        ministry = column[1].find_all('strong')[-1].text
        # Extract asked Date
        asked_date = column[2].find('strong').text
        # Extract answered Date
        if column[2].find('form'):
            answered_date = 'en attente de réponse'
        else:
            answered_date = column[2].find_all('strong')[-1].text

        print(f'Type: {type}, number: {number}, legislature: {legislature}, name: {name}, title: {title}, ministry: {ministry}, asked_date: {asked_date}, answered_date: {answered_date}, link: {link}')

    # Iterate over all pages    
    pagination = soup.find('div', class_='pagination-bootstrap')
    if pagination:
        next = pagination.find_all('li')[-1].find('a')
        if next:
            url_next = 'https://www2.assemblee-nationale.fr' + next['href']
            next = requests.get(url_next)
            soup = BeautifulSoup(next.content, 'html.parser')
        else:
            break
    else:
        break
        