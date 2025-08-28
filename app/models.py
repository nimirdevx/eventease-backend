from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from .database import Base
from sqlalchemy.orm import relationship
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="attendee")  # organizer / attendee
    events = relationship("Event", back_populates="organizer")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    organizer_id = Column(Integer, ForeignKey("users.id"))  # link to User

    organizer = relationship("User", back_populates="events")
