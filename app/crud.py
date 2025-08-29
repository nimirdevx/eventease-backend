from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from . import models

def create_user(db: Session, name: str, email: str, password: str, role: str = "attendee"):
    hashed_pw = bcrypt.hash(password)
    db_user = models.User(name=name, email=email, password_hash=hashed_pw, role=role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_event(db: Session, title: str, description: str, date, organizer_id: int):
    event = models.Event(
        title=title,
        description=description,
        date=date,
        organizer_id=organizer_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_events(db: Session):
    return db.query(models.Event).all()

def get_event_by_id(db: Session, event_id: int):
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def update_event(db: Session, event_id: int, event_data, user_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return None
    if event.organizer_id != user_id:
        return "forbidden"
    
    event.title = event_data.title
    event.description = event_data.description
    event.date = event_data.date
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int, user_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return None
    if event.organizer_id != user_id:
        return "forbidden"
    
    db.delete(event)
    db.commit()
    return event

