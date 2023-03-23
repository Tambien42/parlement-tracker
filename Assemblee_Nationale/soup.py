import requests
from bs4 import BeautifulSoup
import time

# Make request on url
def make_request(url):
    # Make a request to the webpage
    response = requests.get(url)
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

# Find url of next page
def next_page(page):
    try:
        pagination = page.find('div', class_='pagination-bootstrap')
        return (
            'https://www2.assemblee-nationale.fr' + pagination.find_all('li')[-1].find('a')['href']
        )
    except:
        return None