import sqlalchemy
from sqlalchemy import between
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
from pprint import pprint
from deputes import Deputes
from scrutins import Scrutins
from votes import Votes
from groupes import Groupes

# Global Variable
legislature = 17

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class Pourcentages_GroupesAN(Base):
    __tablename__ = 'pourcentages_GroupesAN'

    id: Mapped[int] = mapped_column(primary_key=True)
    groupe_id: Mapped[str]
    legislature: Mapped[int]
    vote: Mapped[float]
    date: Mapped[datetime]

    def __repr__(self):
        return f"<Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

Base.metadata.create_all(engine)

def get_all_groupes(legislature):
    groupes = session.query(Groupes).filter(Groupes.legislature == legislature).all()
    return groupes

def scrutins_numbers(legislature, start_date, end_date):
    if end_date is None:
        end_date = date.today()
    scrutins = session.query(Scrutins).filter(Scrutins.legislature == legislature).where(between(Scrutins.date_seance, start_date, end_date)).all()
    return len(scrutins)

def get_number_votes_depute(depute_id, legislature):
    votes = session.query(Votes).filter(Votes.legislature == legislature).all()
    count = 0
    for vote in votes:
        if depute_id in vote.pour or depute_id in vote.contre or depute_id in vote.abstention or depute_id in vote.non_votants:
            count = count + 1
    return count

def get_depute_dates(depute_id, legslature):
    depute = session.query(Deputes).filter(Deputes.legislature == legislature).first()
    return depute.date_debut_mandat, depute.date_fin_mandat

def calcul_pourcentage_groupe_vote():
    groupes = get_all_groupes(legislature)
    
    for groupe in groupes:
        moyenne_groupe = 0
        total = 0
        count = 0
        for depute_id in (groupe.president + ',' + groupe.membres + ',' + groupe.apparentes).split(","):
            if depute_id == "":
                continue
            count = count + 1
            numerateur = get_number_votes_depute(depute_id, groupe.legislature)
            start_date, end_date = get_depute_dates(depute_id, legislature)
            denominateur = scrutins_numbers(groupe.legislature, start_date, end_date)
            pourcentage_vote = 0
            if numerateur != 0 or denominateur != 0:
                pourcentage_vote = round(numerateur / denominateur * 100, 2)
            total = total + pourcentage_vote

        moyenne_groupe = round(total / count, 2)
        print(f'{groupe.nom} {moyenne_groupe}%')

        session = Session() 
        db = session.query(Pourcentages_GroupesAN).filter(Pourcentages_GroupesAN.groupe_id == groupe.groupe_id and Pourcentages_GroupesAN.date == groupe.date).first()
        if db:
            db.vote = moyenne_groupe
            session.commit()
            continue

        # Store data in the database
        depute = Pourcentages_GroupesAN(
            groupe_id=groupe.groupe_id,
            legislature=groupe.legislature,
            vote=moyenne_groupe,
            date=groupe.date
        )
        
        session.add(depute)  # Use merge to update or insert
        session.commit()
        session.close() 

def main():
    calcul_pourcentage_groupe_vote()

if __name__ == "__main__":
    main()