import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from dateutil import parser
import json
import locale

# set the locale to French
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
# TODO Number of people in groups and list votes
Base = declarative_base()

class Groups(Base):
    __tablename__ = 'groups'

    ids = Column("id", Integer, primary_key=True)
    name = Column("name", String)
    president = Column("president", String)
    members = Column("members", TEXT)
    affiliates = Column("affiliates", TEXT)
    number = Column("number", Integer)
    votes = Column("votes", TEXT)


    def __init__(self, groups):
        self.name = groups["name"]
        self.president = groups["president"]
        self.members = groups["members"]
        self.affiliates = groups["affiliates"]
        self.number = groups["number_deputes"]
        #self.votes = groups["votes"]

    
    def __repr__(self):
        return f'(Group n {self.name})'

# SQLAlchemy
engine = create_engine('sqlite:///votes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

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

groups = {}

for c in content:
    groups["name"] = c.find("h3").text

    url_gr = c.find('ul').find_all('li')[1].find('a')['href']
    gr = requests.get('https://www2.assemblee-nationale.fr' + url_gr)
    s1 = BeautifulSoup(gr.content, 'html.parser')
    content1 = s1.find('a', class_='ajax')['data-uri-suffix']
    ajax1 = requests.get('https://www2.assemblee-nationale.fr' + content1)
    s2 = BeautifulSoup(ajax1.content, 'html.parser')
    content2 = s2.find('div', {"id": "instance-composition-list"})

    # Extract Number of deputes
    groups['number_deputes'] = len(content2.find_all('li'))

    # Extract list of depute of the group by rank (president, membre, apprenté)
    all = content2.find_all('ul')
    groups['president'] = ''
    groups['members'] = ''
    groups['affiliates'] = ''
    if len(all) == 1:
        members_list = all[0].find_all('a', class_='instance-composition-nom')
        for m in members_list:
            groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
    elif len(all) == 2:
        groups['president'] = all[0].find('div', class_='instance-composition-nom').find('a').text.replace('\xa0', ' ')
        members_list = all[1].find_all('a', class_='instance-composition-nom')
        for m in members_list:
            groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
    elif len(all) == 3:
        groups['president'] = all[0].find('div', class_='instance-composition-nom').find('a').text.replace('\xa0', ' ')
        members_list = all[1].find_all('a', class_='instance-composition-nom')
        for m in members_list:
            groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
        aff = all[2].find_all('a', class_='instance-composition-nom')
        for a in aff:
            groups['affiliates'] = groups['affiliates'] + ', ' + a.text.replace('\xa0', ' ')
    
    print(f'members: {groups["members"]}')
    # Store in DB
    group = Groups(groups)
    session.add(group)
    session.commit() 
