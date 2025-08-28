from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.database import get_db
from app.routers.auth import get_current_user

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
