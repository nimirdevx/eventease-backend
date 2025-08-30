from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.database import get_db
from app.routers.auth import get_current_user
from typing import List

import uuid
import qrcode
import os 
router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", response_model=schemas.EventResponse)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["organizer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers or admins can create events"
        )
    
    # Create the event
    new_event = crud.create_event(db, event.title, event.description, event.date, current_user.id)
    
    # Create notification for the organizer
    crud.create_notification(
        db=db,
        title="Event Created Successfully",
        message=f"Your event '{new_event.title}' has been created successfully!",
        user_id=current_user.id,
        event_id=new_event.id
    )
    
    return new_event

@router.get("/my", response_model=List[schemas.EventResponse])
def my_events(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Get events created by the current user"""
    return db.query(models.Event).filter(models.Event.organizer_id == current_user.id).all()

@router.get("", response_model=List[schemas.EventResponse])
def list_events(
    search: str = None,
    date: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return crud.search_events(db, search, date, skip, limit)


@router.get("/upcoming", response_model=List[schemas.EventResponse])
def upcoming_events(db: Session = Depends(get_db)):
    return crud.get_upcoming_events(db)

@router.get("/past", response_model=List[schemas.EventResponse])
def past_events(db: Session = Depends(get_db)):
    return crud.get_past_events(db)


@router.get("/{event_id}", response_model=schemas.EventDetail)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event_by_id(db, event_id)
    return event

@router.put("/{event_id}", response_model=schemas.EventResponse)
def update_event(event_id: int, event_data: schemas.EventCreate, 
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    result = crud.update_event(db, event_id, event_data, current_user.id)
    
    # Notify all registered participants about event update
    crud.notify_event_participants(
        db=db,
        event_id=event_id,
        title="Event Updated",
        message=f"The event '{result.title}' has been updated. Please check the latest details.",
        exclude_user_id=current_user.id
    )
    
    return result


@router.delete("/{event_id}")
def delete_event(event_id: int,
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    result = crud.delete_event(db, event_id, current_user.id)
    return {"detail": "Event deleted successfully"}


@router.post("/{event_id}/register")
def register_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Use the new CRUD function for registration
    registration = crud.register_for_event(db, current_user.id, event_id)
    event = crud.get_event_by_id(db, event_id)
    
    # Create a ticket for the registration
    ticket = models.Ticket(code=str(uuid.uuid4()), registration_id=registration.id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Create tickets directory if it doesn't exist
    tickets_dir = "tickets"
    os.makedirs(tickets_dir, exist_ok=True)

    # Define filename first
    filename = f"{ticket.code}.png"
    filepath = os.path.join(tickets_dir, filename)

    # Generate and save QR code
    img = qrcode.make(ticket.code)
    img.save(filepath)

    # Now safely build the URL
    ticket_url = f"http://localhost:8000/tickets/{filename}"
    
    # Create notifications
    # 1. Notify the user about successful registration
    crud.create_notification(
        db=db,
        title="Registration Successful",
        message=f"You have successfully registered for '{event.title}'. Your ticket code is {ticket.code}",
        user_id=current_user.id,
        event_id=event_id
    )
    
    # 2. Notify the event organizer about new registration
    crud.create_notification(
        db=db,
        title="New Registration",
        message=f"{current_user.name} has registered for your event '{event.title}'",
        user_id=event.organizer_id,
        event_id=event_id
    )
    
    return {"message": f"Successfully registered for {event.title}!",
            "ticket_code": ticket.code,
             "ticket_url": ticket_url}


@router.get("/{event_id}/attendees")
def get_event_attendees(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Only organizer of this event can view
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view attendees")

    attendees = [
    {"id": reg.user.id, "name": reg.user.name, "email": reg.user.email, "ticket": reg.ticket.code if reg.ticket else None}
    for reg in event.registrations
                ]

    return {"event": event.title, "attendees": attendees}


@router.delete("/{event_id}/register")
def cancel_registration(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get event for notification
    event = crud.get_event_by_id(db, event_id)
    
    crud.cancel_registration(db, current_user.id, event_id)
    
    # Notify user about cancellation
    crud.create_notification(
        db=db,
        title="Registration Cancelled",
        message=f"Your registration for '{event.title}' has been cancelled",
        user_id=current_user.id,
        event_id=event_id
    )
    
    # Notify organizer about cancellation
    crud.create_notification(
        db=db,
        title="Registration Cancelled",
        message=f"{current_user.name} has cancelled their registration for '{event.title}'",
            user_id=event.organizer_id,
            event_id=event_id
        )
    
    return {"message": "Registration cancelled"}
