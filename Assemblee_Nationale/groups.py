from sqlalchemy import create_engine, Column, Integer, String, DATE, TEXT
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from soup import make_request
from datetime import datetime

# create a database connection
engine = create_engine('sqlite:///votes.db')
Session = sessionmaker(bind=engine)

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

#Create the table in the database
Base.metadata.create_all(engine)

def save_to_database(data: dict, Model):
    """
    Save data to a database using the provided session and model.
    :param data: dictionary containing data to be saved
    :param model: SQLAlchemy model class
    :return: None
    """
    #print(f'{data["name"]}')
    # open a new database session
    session = Session()
    # retrieve the row you want to check by its id and sort it by date
    group = session.query(Groups).filter_by(name=data["name"]).order_by(Groups.date.desc()).first()
    if group != None:
        # compare all columns except for the date column
        if (group.name == data['name'] and
            group.president == data['president'] and
            group.members == data['members'] and
            group.affiliates == data['affiliates'] and
            group.number == data['number_deputes']):
            print('All columns except for date are the same')
            return
    # create a new user object
    new_data = Model(data)
    # add the user to the session
    session.add(new_data)
    # commit the changes to the database
    session.commit()
    # close the session
    session.close()

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
            groups['members'] = members_list[0].text.replace('\xa0', ' ')
            for m in members_list[1:]:
                groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
        elif len(composition) == 2:
            groups['president'] = composition[0].find('div', class_='instance-composition-nom').find('a').text.replace('\xa0', ' ')
            members_list = composition[1].find_all('a', class_='instance-composition-nom')
            groups['members'] = members_list[0].text.replace('\xa0', ' ')
            for m in members_list[1:]:
                groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
        elif len(composition) == 3:
            groups['president'] = composition[0].find('div', class_='instance-composition-nom').find('a').text.replace('\xa0', ' ')
            members_list = composition[1].find_all('a', class_='instance-composition-nom')
            groups['members'] = members_list[0].text.replace('\xa0', ' ')
            for m in members_list[1:]:
                groups['members'] = groups['members'] + ', ' + m.text.replace('\xa0', ' ')
            aff = composition[2].find_all('a', class_='instance-composition-nom')
            groups['affiliates'] = aff[0].text.replace('\xa0', ' ')
            for a in aff[1:]:
                groups['affiliates'] = groups['affiliates'] + ', ' + a.text.replace('\xa0', ' ')
        save_to_database(groups, Groups)
    print('Groups Done')
