import requests
from bs4 import BeautifulSoup

URL = 'https://www2.assemblee-nationale.fr/16/les-groupes-politiques'
#/instances/embed/121314/GP/instance/legislature/16
# Make a request to the webpage
page = requests.get(URL)
# Parse the HTML content
soup = BeautifulSoup(page.content, 'html.parser')
# Find the div containing the data
content = soup.find('a', class_='ajax')['data-uri-suffix']

ajax = requests.get('https://www2.assemblee-nationale.fr' + content)
s = BeautifulSoup(ajax.content, 'html.parser')
content = s.find('ul', class_='liens-liste').find_all('li', recursive=False)

for c in content:
    name = c.find("h3").text

    url_gr = c.find('ul').find_all('li')[1].find('a')['href']
    gr = requests.get('https://www2.assemblee-nationale.fr' + url_gr)
    s1 = BeautifulSoup(gr.content, 'html.parser')
    content1 = s1.find('a', class_='ajax')['data-uri-suffix']
    ajax1 = requests.get('https://www2.assemblee-nationale.fr' + content1)
    s2 = BeautifulSoup(ajax1.content, 'html.parser')
    content2 = s2.find('div', {"id": "instance-composition-list"})

    # Extract Number of deputes
    number_deputes = len(content2.find_all('li'))

    # Extract list of depute of the group by rank (president, membre, apprenté)
    all = content2.find_all('ul')
    president = ''
    members = []
    affiliates = []
    if len(all) == 1:
        members_list = all[0].find_all('a', class_='instance-composition-nom')
        for m in members_list:
            members.append(m.text.replace('\xa0', ' '))
    elif len(all) == 2:
        president = all[0].find('div', class_='instance-composition-nom').find('a').text
        members_list = all[1].find_all('a', class_='instance-composition-nom')
        for m in members_list:
            members.append(m.text.replace('\xa0', ' '))
    elif len(all) == 3:
        president = all[0].find('div', class_='instance-composition-nom').find('a').text
        members_list = all[1].find_all('a', class_='instance-composition-nom')
        for m in members_list:
            members.append(m.text.replace('\xa0', ' '))
        aff = all[2].find_all('a', class_='instance-composition-nom')
        for a in aff:
            affiliates.append(a.text.replace('\xa0', ' '))
