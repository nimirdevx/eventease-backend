from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "attendee"
    
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
        
        
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    

class EventCreate(BaseModel):
    title: str
    description: str | None = None
    date: datetime

class EventResponse(BaseModel):
    id: int
    title: str
    description: str | None
    date: datetime
    organizer_id: int

    class Config:
        from_attributes = True
        
class EventDetail(EventResponse):
    organizer_id: int
    comments: List['CommentResponse'] = []

    class Config:
        from_attributes = True


# Comment schemas
class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
    event_id: int
    user: UserResponse

    class Config:
        from_attributes = True


# Notification schemas
class NotificationCreate(BaseModel):
    title: str
    message: str
    user_id: int
    event_id: int | None = None


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    user_id: int
    event_id: int | None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: bool