from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from . import models
from .exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    EventNotFoundError,
    UnauthorizedError,
    AlreadyRegisteredError
)
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

def create_user(db: Session, name: str, email: str, password: str, role: str = "attendee"):
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise UserAlreadyExistsError(email)
    
    hashed_pw = bcrypt.hash(password)
    db_user = models.User(name=name, email=email, password_hash=hashed_pw, role=role)
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise UserAlreadyExistsError(email)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise UserNotFoundError(f"ID {user_id}")
    return user

def create_event(db: Session, title: str, description: str, date, organizer_id: int):
    # Verify organizer exists
    organizer = db.query(models.User).filter(models.User.id == organizer_id).first()
    if not organizer:
        raise UserNotFoundError(f"ID {organizer_id}")
    
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
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise EventNotFoundError(event_id)
    return event

def update_event(db: Session, event_id: int, event_data, user_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise EventNotFoundError(event_id)
    if event.organizer_id != user_id:
        raise UnauthorizedError("Only the event organizer can update this event")
    
    event.title = event_data.title
    event.description = event_data.description
    event.date = event_data.date
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int, user_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise EventNotFoundError(event_id)
    if event.organizer_id != user_id:
        raise UnauthorizedError("Only the event organizer can delete this event")
    
    db.delete(event)
    db.commit()
    return event


def cancel_registration(db: Session, user_id: int, event_id: int):
    # Verify event exists
    event = get_event_by_id(db, event_id)
    
    reg = db.query(models.Registration).filter(
        models.Registration.user_id == user_id,
        models.Registration.event_id == event_id
    ).first()
    if not reg:
        raise EventNotFoundError(f"Registration not found for event {event_id}")
    
    db.delete(reg)
    db.commit()
    return reg

def search_events(db: Session, search: str = None, date: str = None, skip: int = 0, limit: int = 10):
    query = db.query(models.Event)
    
    if search:
        query = query.filter(models.Event.description.ilike(f"%{search}%"))
    
    if date:
        try:
            # Parse input "YYYY-MM-DD" into start and end of that day
            start = datetime.strptime(date, "%Y-%m-%d")
            end = start + timedelta(days=1)
            query = query.filter(and_(models.Event.date >= start, models.Event.date < end))
        except ValueError:
            pass  # Ignore invalid date format
    
    return query.offset(skip).limit(limit).all()


def get_upcoming_events(db: Session):
    now = datetime.now()
    return db.query(models.Event).filter(models.Event.date >= now).all()

def get_past_events(db: Session):
    now = datetime.now()
    return db.query(models.Event).filter(models.Event.date < now).all()


# Comment CRUD operations
def create_comment(db: Session, content: str, user_id: int, event_id: int):
    # Verify user and event exist
    get_user_by_id(db, user_id)
    get_event_by_id(db, event_id)
    
    comment = models.Comment(
        content=content,
        user_id=user_id,
        event_id=event_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments_by_event(db: Session, event_id: int, skip: int = 0, limit: int = 50):
    # Verify event exists
    get_event_by_id(db, event_id)
    
    return db.query(models.Comment).filter(
        models.Comment.event_id == event_id
    ).order_by(models.Comment.created_at.desc()).offset(skip).limit(limit).all()


def get_comment_by_id(db: Session, comment_id: int):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise EventNotFoundError(f"Comment with ID {comment_id} not found")
    return comment


def delete_comment(db: Session, comment_id: int, user_id: int):
    comment = get_comment_by_id(db, comment_id)
    if comment.user_id != user_id:
        raise UnauthorizedError("You can only delete your own comments")
    
    db.delete(comment)
    db.commit()
    return comment


# Notification CRUD operations
def create_notification(db: Session, title: str, message: str, user_id: int, event_id: int = None):
    # Verify user exists
    get_user_by_id(db, user_id)
    
    # Verify event exists if provided
    if event_id:
        get_event_by_id(db, event_id)
    
    notification = models.Notification(
        title=title,
        message=message,
        user_id=user_id,
        event_id=event_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

# Registration CRUD operations
def register_for_event(db: Session, user_id: int, event_id: int):
    # Verify user and event exist
    user = get_user_by_id(db, user_id)
    event = get_event_by_id(db, event_id)
    
    # Check if already registered
    existing_registration = db.query(models.Registration).filter(
        models.Registration.user_id == user_id,
        models.Registration.event_id == event_id
    ).first()
    
    if existing_registration:
        raise AlreadyRegisteredError(event_id)
    
    # Create registration
    registration = models.Registration(user_id=user_id, event_id=event_id)
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration

def get_user_registrations(db: Session, user_id: int):
    return db.query(models.Registration).filter(
        models.Registration.user_id == user_id
    ).all()

def get_event_registrations(db: Session, event_id: int):
    # Verify event exists
    get_event_by_id(db, event_id)
    
    return db.query(models.Registration).filter(
        models.Registration.event_id == event_id
    ).all()


def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 20, unread_only: bool = False):
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    
    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_notification_as_read(db: Session, notification_id: int, user_id: int):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == user_id
    ).first()
    
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification
    return None


def mark_all_notifications_as_read(db: Session, user_id: int):
    db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return True


def get_unread_notification_count(db: Session, user_id: int):
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()


# Helper function to create notifications for event-related activities
def notify_event_participants(db: Session, event_id: int, title: str, message: str, exclude_user_id: int = None):
    # Get all registered users for the event
    registrations = db.query(models.Registration).filter(models.Registration.event_id == event_id).all()
    
    notifications = []
    for registration in registrations:
        if exclude_user_id and registration.user_id == exclude_user_id:
            continue
            
        notification = create_notification(
            db=db,
            title=title,
            message=message,
            user_id=registration.user_id,
            event_id=event_id
        )
        notifications.append(notification)
    
    return notifications

