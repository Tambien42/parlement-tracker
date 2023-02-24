from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import *

# Function called connectDB that creates a connection to a SQLite database using SQLAlchemy
def connectDB():
    engine = create_engine('sqlite:///' + DB)
    metadata = MetaData(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, metadata, session

def instantiate(Init, data):
    engine, metadata, session = connectDB()
    class_init = Init(data)
    session.add(class_init)
    session.commit() 