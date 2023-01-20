import requests, re
from bs4 import BeautifulSoup

def scrape_page(url):
    # Make a request to the webpage
    response = requests.get(url)
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find the table containing the data
    table = soup.find('table', class_='scrutins')
    # Find all the rows in the table
    t = table.find('tbody')
    rows = t.find_all('tr')
    
    # Iterate over the rows
    for row in rows:
        # Find the cells in the row
        cells = row.find_all('td')

        # Extract the data from the cells
        number = cells[0].text
        date = cells[1].text
        object = cells[2].text
        votes_for = cells[3].text
        votes_against = cells[4].text
        votes_abstention = cells[5].text

        # Extract url Analyse du scrutin
        url_analyse_scrutin = 'https://www2.assemblee-nationale.fr' + cells[2].find_all('a')[-1]['href']
        r = requests.get(url_analyse_scrutin)
        s = BeautifulSoup(r.content, 'html.parser')
        div = s.find_all('div', class_='Non-votant')
        list_nv = []
        # Extract Number of Non Votant
        non_votants = 0
        for d in div:
            non_votants = non_votants + int(d.find('p').find('b').text)
            list_nv.append(d.find('ul').text.strip().split('(')[0].replace('\xa0', ' ').strip())   
        
        # Extract group votes
        groups = s.find('ul', {"id": "index-groupe"}).find_all('li')
        for g in groups:
            gr = g.find_all('span')
            group = gr[0].text
            nb_votes = 0
            if len(gr) != 1:
                for n in gr[1:]:
                    nb_votes = nb_votes + int(n.find('b').text)

# Start with the first page
url = 'https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/16'

# Scrape the first page
scrape_page(url)

# Loop until there are no more pages
while True:
    # Make a request to the webpage
    response = requests.get(url)
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find the link to the next page
    pagination = soup.find('div', class_='pagination-bootstrap')
    next_page_link = pagination.find_all('li')[-1].find('a')

    # Check if there is a next page
    if next_page_link:
        # If there is a next page, follow the link
        url = 'https://www2.assemblee-nationale.fr' + next_page_link['href']
        # Scrape the next page
        scrape_page(url)
    else:
        # If there are no more pages, break the loop
        break
