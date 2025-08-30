from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud, models
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/interactions", tags=["interactions"])


# Comment endpoints
@router.post("/events/{event_id}/comments", response_model=schemas.CommentResponse)
def create_comment(
    event_id: int,
    comment_data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new comment on an event"""
    # Check if event exists
    event = crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Create the comment
    comment = crud.create_comment(
        db=db,
        content=comment_data.content,
        user_id=current_user.id,
        event_id=event_id
    )
    
    # Notify event organizer about new comment (if not the organizer themselves)
    if event.organizer_id != current_user.id:
        crud.create_notification(
            db=db,
            title="New Comment on Your Event",
            message=f"{current_user.name} commented on your event '{event.title}': {comment_data.content[:50]}{'...' if len(comment_data.content) > 50 else ''}",
            user_id=event.organizer_id,
            event_id=event_id
        )
    
    return comment


@router.get("/events/{event_id}/comments", response_model=List[schemas.CommentResponse])
def get_event_comments(
    event_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all comments for an event"""
    # Check if event exists
    event = crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    comments = crud.get_comments_by_event(db, event_id, skip, limit)
    return comments


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a comment (only by the author or admin)"""
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check if user can delete (author or admin)
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    result = crud.delete_comment(db, comment_id, comment.user_id)
    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    return {"message": "Comment deleted successfully"}


# Notification endpoints
@router.get("/notifications", response_model=List[schemas.NotificationResponse])
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user's notifications"""
    notifications = crud.get_user_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    return notifications


@router.get("/notifications/count")
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = crud.get_unread_notification_count(db, current_user.id)
    return {"unread_count": count}


@router.patch("/notifications/{notification_id}/read", response_model=schemas.NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    notification = crud.mark_notification_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.patch("/notifications/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    crud.mark_all_notifications_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}


# Admin endpoint to create system notifications
@router.post("/notifications/broadcast", response_model=List[schemas.NotificationResponse])
def broadcast_notification(
    notification_data: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Admin only: Broadcast a notification to all users"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can broadcast notifications"
        )
    
    # Get all users
    users = db.query(models.User).all()
    notifications = []
    
    for user in users:
        notification = crud.create_notification(
            db=db,
            title=notification_data.title,
            message=notification_data.message,
            user_id=user.id,
            event_id=notification_data.event_id
        )
        notifications.append(notification)
    
    return notifications
