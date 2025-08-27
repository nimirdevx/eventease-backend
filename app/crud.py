from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from . import models

def create_user(db: Session, name: str, email: str, password: str):
    hashed_pw = bcrypt.hash(password)
    db_user = models.User(name=name, email=email, password_hash=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
