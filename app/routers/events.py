from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.database import get_db
from app.routers.auth import get_current_user
import uuid
import qrcode
import os 
router = APIRouter(prefix="/events", tags=["Events"])

@router.post("/create", response_model=schemas.EventResponse)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "organizer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers can create events"
        )
    return crud.create_event(db, event.title, event.description, event.date, current_user.id)

@router.get("/", response_model=list[schemas.EventResponse])
def list_events(db: Session = Depends(get_db)):
    return crud.get_events(db)


@router.get("/{event_id}", response_model=schemas.EventDetail)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=schemas.EventResponse)
def update_event(event_id: int, event_data: schemas.EventCreate, 
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    result = crud.update_event(db, event_id, event_data, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if result == "forbidden":
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    return result


@router.delete("/{event_id}")
def delete_event(event_id: int,
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    result = crud.delete_event(db, event_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if result == "forbidden":
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")
    return {"detail": "Event deleted successfully"}


@router.post("/{event_id}/register")
def register_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = (
        db.query(models.Registration)
        .filter_by(user_id=current_user.id, event_id=event_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already registered for this event")

    reg = models.Registration(user_id=current_user.id, event_id=event_id)
    db.add(reg)
    db.commit()
    db.refresh(reg)
    
   # Create a ticket for the registration
    ticket = models.Ticket(code=str(uuid.uuid4()), registration_id=reg.id)
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