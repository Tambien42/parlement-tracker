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

class AN_Lois(Base):
    __tablename__ = 'AN_propositions_loi'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    numero: Mapped[int]
    titre: Mapped[str]
    lien: Mapped[str]
    date: Mapped[datetime]
    author: Mapped[str]
    cosignataire: Mapped[str]

    def __repr__(self):
        return f"<AN_Lois(id={self.id}, legislature={self.legislature}, numero={self.numero})>"

def parse(url):
    pass

def parse_loi():
    pass

def get_loi(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(AN_Lois.titre)
        .where(AN_Lois.legislature == legislature)
    )
    # Execute the query
    results = session.execute(stmt).scalars().all()
    return results

def main():
    #Create the table in the database
    Base.metadata.create_all(engine)
    #Start URL
    url = ""
    parse(url)

if __name__ == "__main__":
    main()