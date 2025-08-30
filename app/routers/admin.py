from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.routers.auth import get_current_user
from app.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
def list_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return db.query(models.User).all()

@router.put("/users/{user_id}/role")
def change_role(user_id: int, new_role: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    db.commit()
    return {"message": f"User {user.name} is now {new_role}"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

@router.delete("/events/{event_id}")
def admin_delete_event(event_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"message": "Event deleted by admin"}
