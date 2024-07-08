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

class Votes(Base):
    __tablename__ = 'votes'

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int]
    legislature: Mapped[str]
    pour: Mapped[str]
    contre: Mapped[str]
    abstention: Mapped[str]
    non_votants: Mapped[str]

    def __repr__(self):
        return f"<Votes(id={self.id}, legislature={self.legislature}, numero={self.numero})>"

def parse(url):
    pass

def parse_vote():
    pass

def get_votes(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Votes.numero)
        .where(Votes.legislature == legislature)
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