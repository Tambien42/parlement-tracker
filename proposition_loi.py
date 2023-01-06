import requests
from bs4 import BeautifulSoup

URL = 'https://www2.assemblee-nationale.fr/documents/liste/(type)/propositions-loi'
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

while True:
    # Find all the rows in the table
    lis = soup.find('ul', class_='liens-liste').find_all('li', recursive=False)
    # Iterate over the rows
    for p in lis:
        # Extract the number of the proposal
        number = p.find('h3').text.split('-')[-1].replace(u'\xa0', ' ').split(' ')[-1]
        # Extract title
        title = p.find('h3').text
        # Extract link
        link = p.find('ul').find_all('li')[-1].find('a')['href']
        # Extract date
        date = p.find('ul').find_all('li')
        # TODO Extract author and cosigners
        # Extract author
        #url_redirect = 'https://www.assemblee-nationale.fr/dyn/16/textes/l16b' + number.zfill(4) + '_proposition-loi#'
        #signers = BeautifulSoup(page_text.content, 'html.parser')
        #author = signers.find('div', class_='assnatSection1')
        # Extract cosigner
        #print(f'author: {signers}')

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
        