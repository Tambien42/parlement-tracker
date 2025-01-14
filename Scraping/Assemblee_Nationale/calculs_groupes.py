import sqlalchemy
from sqlalchemy import between
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
from pprint import pprint
from deputes import AN_Deputes
from scrutins import AN_Scrutins
from votes import AN_Votes
from groupes import AN_Groupes

# Global Variable
legislature = 17

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class AN_Pourcentages_Groupes(Base):
    __tablename__ = 'AN_pourcentages_groupes'

    id: Mapped[int] = mapped_column(primary_key=True)
    groupe_id: Mapped[str]
    legislature: Mapped[int]
    vote: Mapped[float]
    date: Mapped[datetime]

    def __repr__(self):
        return f"<AN_Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

Base.metadata.create_all(engine)

def get_all_groupes(legislature):
    groupes = session.query(AN_Groupes).filter(AN_Groupes.legislature == legislature).all()
    return groupes

def scrutins_numbers(legislature, start_date, end_date):
    if end_date is None:
        end_date = date.today()
    scrutins = session.query(AN_Scrutins).filter(AN_Scrutins.legislature == legislature).where(between(AN_Scrutins.date_seance, start_date, end_date)).all()
    return len(scrutins)

def get_number_votes_depute(depute_id, legislature):
    votes = session.query(AN_Votes).filter(AN_Votes.legislature == legislature).all()
    count = 0
    for vote in votes:
        if depute_id in vote.pour or depute_id in vote.contre or depute_id in vote.abstention or depute_id in vote.non_votants:
            count = count + 1
    return count

def get_depute_dates(depute_id, legislature):
    depute = session.query(AN_Deputes).filter(AN_Deputes == depute_id, AN_Deputes.legislature == legislature).first()
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

        # session = Session() 
        # db = session.query(AN_Pourcentages_Groupes).filter(AN_Pourcentages_Groupes.groupe_id == groupe.groupe_id and AN_Pourcentages_Groupes.date == groupe.date).first()
        # if db:
        #     db.vote = moyenne_groupe
        #     session.commit()
        #     continue

        # # Store data in the database
        # depute = AN_Pourcentages_Groupes(
        #     groupe_id=groupe.groupe_id,
        #     legislature=groupe.legislature,
        #     vote=moyenne_groupe,
        #     date=groupe.date
        # )
        
        # session.add(depute)  # Use merge to update or insert
        # session.commit()
        # session.close() 

def main():
    calcul_pourcentage_groupe_vote()

if __name__ == "__main__":
    main()