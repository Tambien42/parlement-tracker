import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime
from pprint import pprint

# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Groupes(Base):
    __tablename__ = 'groupes'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    nom: Mapped[str]
    date: Mapped[datetime]
    president = Mapped[str]
    membres = Mapped[str]
    affilies = Mapped[str]

    def __repr__(self):
        return f"<Groupes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

def parse(url):
    pass

def parse_groupes():
    pass

def get_president(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.president)
        .where(Groupes.nom == nom)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    president = ''
    if len(results) !=  0:
        president = results[0]
    return president

def get_membres(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.membres)
        .where(Groupes.nom == nom)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    membres = ''
    if len(results) !=  0:
        membres = results[0]
    return membres

def get_affilies(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Groupes.affilies)
        .where(Groupes.nom == nom)
        .order_by(Groupes.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    affilies = ''
    if len(results) !=  0:
        affilies = results[0]
    return affilies

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = ""
    parse(url)

if __name__ == "__main__":
    main()