from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import time 
Base = declarative_base()
engine = create_engine('sqlite:///credentials.db',echo=False)
Session = sessionmaker()

class Employee(Base):
    __tablename__ = 'employee'
    id = Column(Integer(), primary_key=True, nullable=False)
    username = Column(String(), nullable=False)
    email = Column(String(),nullable=False)
    password = Column(String(), nullable=False)
    date_joined = Column(String(),default=datetime.utcnow())
    last_used = Column(DateTime(),default=datetime.utcnow())
    
