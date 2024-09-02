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

class Commissions(Base):
    __tablename__ = 'commissions'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    nom: Mapped[str]
    date: Mapped[datetime]
    president = Mapped[str]
    secretaires = Mapped[str]
    membres = Mapped[str]
    rapporteurs = Mapped[str]

    def __repr__(self):
        return f"<Groupes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

def parse(url):
    pass

def parse_commissions():
    pass

def get_president(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Commissions.president)
        .where(Commissions.nom == nom)
        .order_by(Commissions.date.desc())
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
        sqlalchemy.select(Commissions.membres)
        .where(Commissions.nom == nom)
        .order_by(Commissions.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    membres = ''
    if len(results) !=  0:
        membres = results[0]
    return membres

def get_secretaires(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Commissions.secretaires)
        .where(Commissions.nom == nom)
        .order_by(Commissions.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    secretaires = ''
    if len(results) !=  0:
        secretaires = results[0]
    return secretaires

def get_rapporteurs(nom):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Commissions.rapporteurs)
        .where(Commissions.nom == nom)
        .order_by(Commissions.date.desc())
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    rapporteurs = ''
    if len(results) !=  0:
        rapporteurs = results[0]
    return rapporteurs

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = ""
    parse(url)

if __name__ == "__main__":
    main()