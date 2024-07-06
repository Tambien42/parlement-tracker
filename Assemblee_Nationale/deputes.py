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

class Deputes(Base):
    __tablename__ = 'deputes'

    id: Mapped[int] = mapped_column(primary_key=True)
    depute_id: Mapped[str]
    legislature: Mapped[int]
    nom: Mapped[str]
    photo: Mapped[str]
    date_election: Mapped[datetime]
    date_debut_mandat: Mapped[datetime]
    date_fin_mandat: Mapped[datetime]
    raison_fin: Mapped[str]
    circonscription: Mapped[str]
    numero_siege: Mapped[int]
    groupe: Mapped[str]
    rattachement_finance: Mapped[str]
    suppleant: Mapped[str]
    collaborateurs: Mapped[str]
    lien_interet: Mapped[str]
    mail: Mapped[str]
    twitter: Mapped[str]
    facebook: Mapped[str]
    instagram: Mapped[str]
    linkedin: Mapped[str]
    commission: Mapped[str]
    commission_presence: Mapped[str]
    position_vote: Mapped[str]
    questions: Mapped[str]
    loi_auteur: Mapped[str]
    loi_cosigneur: Mapped[str]
    rapports: Mapped[str]

    def __repr__(self):
        return f"<Groupes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

def parse(url):
    pass

def parse_depute():
    pass

def get_all_deputes(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Deputes.deputes_id)
        .where(Deputes.legislature == legislature)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    return results

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = "https://www2.assemblee-nationale.fr/deputes/liste/alphabetique"
    parse(url)

if __name__ == "__main__":
    main()