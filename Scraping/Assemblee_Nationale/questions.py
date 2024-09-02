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

class Questions(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    legislature: Mapped[int]
    numero: Mapped[int]
    date_question: Mapped[datetime]
    date_reponse: Mapped[datetime]
    lien: Mapped[str]
    titre: Mapped[str]
    ministere: Mapped[str]
    type: Mapped[str]
    nom: Mapped[str]

    def __repr__(self):
        return f"<Questions(id={self.id}, legislature={self.legislature}, numero={self.numero})>"

def parse(url):
    pass

def parse_question():
    pass

def get_question(legislature):
    session = Session()
    # Define the query
    stmt = (
        sqlalchemy.select(Questions.president)
        .where(Questions.legislature == legislature)
        .order_by(Questions.date_question.desc())
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