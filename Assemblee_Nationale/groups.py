from sqlalchemy import create_engine, Column, Integer, String, DATE, INTEGER, TEXT, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from soup import make_request, next_page
from datetime import datetime

Base = declarative_base()

class Groups(Base):
    __tablename__ = 'groups'

    ids = Column("id", Integer, primary_key=True)
    name = Column("name", String)
    president = Column("president", String)
    members = Column("members", TEXT)
    affiliates = Column("affiliates", TEXT)
    number = Column("number", Integer)
    date = Column("date", DATE)


    def __init__(self, groups):
        self.name = groups["name"]
        self.president = groups["president"]
        self.members = groups["members"]
        self.affiliates = groups["affiliates"]
        self.number = groups["number_deputes"]
        self.date = groups["date"]
    
    def __repr__(self):
        return f'(Group: {self.name})'

def groups():
    url = 'https://www2.assemblee-nationale.fr/16/les-groupes-politiques'

    groups = {}
    # Parse the HTML content
    soup = make_request(url)
    # Find the ajax url containing the data
    ajax_url = soup.find('a', class_='ajax')['data-uri-suffix']
    ajax = make_request('https://www2.assemblee-nationale.fr' + ajax_url)
    list = ajax.find('ul', class_='liens-liste').find_all('li', recursive=False)
    for party in list:
        # Get Date input
        #TODO get all composition for all date
        #date_input = content.find('input', id='datepicker-instance')
        today = datetime.today().strftime('%d/%m/%Y')
        groups['date'] = datetime.strptime(today, "%d/%m/%Y")

        # Extract name of group
        groups["name"] = party.find("h3").text

        # Go to the composition url and get ajax content
        url_composition = party.find("ul").find_all("li")[1].find("a")["href"]
        comp_page_ajax = make_request('https://www2.assemblee-nationale.fr' + url_composition)
        ajax_comp_url = comp_page_ajax.find('a', class_='ajax')['data-uri-suffix']
        comp_page = make_request('https://www2.assemblee-nationale.fr' + ajax_comp_url)
        content = comp_page.find('div', {"id": "instance-composition-list"})

        # Extract Number of deputes
        groups['number_deputes'] = len(content.find_all('li'))

        # Extract composition
        composition = content.find_all('ul')
        groups['president'] = ''
        groups['members'] = ''
        groups['affiliates'] = ''
        if len(composition) == 1:
            members_list = composition[0].find_all('a', class_='instance-composition-nom')
            for m in members_list:
                groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
        elif len(composition) == 2:
            groups['president'] = composition[0].find('div', class_='instance-composition-nom').find('a').text.replace('\xa0', ' ')
            members_list = composition[1].find_all('a', class_='instance-composition-nom')
            for m in members_list:
                groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
        elif len(composition) == 3:
            groups['president'] = composition[0].find('div', class_='instance-composition-nom').find('a').text.replace('\xa0', ' ')
            members_list = composition[1].find_all('a', class_='instance-composition-nom')
            for m in members_list:
                groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
            aff = composition[2].find_all('a', class_='instance-composition-nom')
            for a in aff:
                groups['affiliates'] = groups['affiliates'] + ', ' + a.text.replace('\xa0', ' ')
        print(f'{groups["president"]}')
