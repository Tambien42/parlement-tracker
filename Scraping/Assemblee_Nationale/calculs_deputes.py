import sqlalchemy
from sqlalchemy import between
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base
from datetime import datetime, date
from pprint import pprint
from deputes import Deputes
from scrutins import Scrutins
from votes import Votes

# Global Variable
legislature = 17

# SQLAlchemy setup
DATABASE_URL = "sqlite:///parlements.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class Pourcentages_deputesAN(Base):
    __tablename__ = 'pourcentages_deputesAN'

    id: Mapped[int] = mapped_column(primary_key=True)
    depute_id: Mapped[str]
    legislature: Mapped[int]
    vote: Mapped[float]
    date_debut_mandat: Mapped[datetime]

    def __repr__(self):
        return f"<Deputes(id={self.id}, legislature={self.legislature}, nom={self.nom})>"

Base.metadata.create_all(engine)

def get_deputes(legislature):
    deputes = session.query(Deputes).filter(Deputes.legislature == legislature).all()
    return deputes

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

def calcul_pourcentage_vote():
    deputes = get_deputes(legislature)
    
    for depute in deputes:
        #print(f"nom: {depute.nom}, id: {depute.id}, legislature: {depute.legislature}, date_debut_mandat: {depute.date_debut_mandat}, date_fin: {depute.date_fin_mandat}")
        numerateur = get_number_votes_depute(depute.depute_id, depute.legislature)
        denominateur = scrutins_numbers(depute.legislature, depute.date_debut_mandat, depute.date_fin_mandat)
        pourcentage_vote = 0
        if numerateur != 0 or denominateur != 0:
            pourcentage_vote = round(numerateur / denominateur * 100, 2)

        print(f"{depute.nom} : {pourcentage_vote}%")

        session = Session() 
        db = session.query(Pourcentages_deputesAN).filter(Pourcentages_deputesAN.depute_id == depute.depute_id and Pourcentages_deputesAN.date_debut_mandat == depute.date_debut_mandat).first()
        if db:
            db.vote = pourcentage_vote
            session.commit()
            continue

        # Store data in the database
        depute = Pourcentages_deputesAN(
            depute_id=depute.depute_id,
            legislature=legislature,
            vote=pourcentage_vote,
            date_debut_mandat=depute.date_debut_mandat
        )
        
        session.add(depute)  # Use merge to update or insert
        session.commit()
        session.close() 

def main():
    calcul_pourcentage_vote()

if __name__ == "__main__":
    main()