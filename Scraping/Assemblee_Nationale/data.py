import httpx
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
import re
import os
import time
from urllib.parse import unquote
from pprint import pprint
from urllib.parse import urlparse, parse_qs
import requests

# create a database connection
engine = sqlalchemy.create_engine('sqlite:///parlements.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class AN_Deputes(Base):
    __tablename__ = 'AN_deputes'

    id: Mapped[int] = mapped_column(primary_key=True)
    depute_id: Mapped[str]
    legislature: Mapped[int]
    nom: Mapped[str]
    photo: Mapped[str]
    profession: Mapped[str]
    date_naissance: Mapped[datetime]
    lieu_naissance: Mapped[str]
    date_election: Mapped[datetime]
    date_debut_mandat: Mapped[datetime]
    raison_debut: Mapped[str]
    date_fin_mandat: Mapped[datetime] = mapped_column(nullable=True)
    raison_fin: Mapped[str] = mapped_column(nullable=True)
    circonscription: Mapped[str]
    numero_siege: Mapped[int] = mapped_column(nullable=True)
    groupe: Mapped[str]
    mail: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<AN_Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"
    
#Create the table in the database
Base.metadata.create_all(engine)

def format_date(str):
    date_format = "%d %B %Y"
    # Convert the date string to a datetime object
    date_object = datetime.strptime(str, date_format)
    return date_object

# open a new database session
session = Session()
depute = AN_Deputes(
            depute_id="PA840737",
            nom="Flavien Termet",
            legislature=17,
            photo="PA840737-17.jpg",
            profession="(33) - Cadre de la fonction publique",
            date_naissance=format_date("29 january 2002"), # 29 janvier 2002
            lieu_naissance="Lorient-56",
            date_election=format_date("7 July 2024"), # 7 juillet 2024
            date_debut_mandat=format_date("8 July 2024"), # 8 juillet 2024
            raison_debut="élection générales",
            date_fin_mandat=format_date("4 october 2024"), # 4 octobre 2024
            raison_fin="Démission",
            circonscription="08-1",
            numero_siege=0,
            groupe="PO845401",
            mail=""
        )
session.add(depute)
session.commit()
session.close()