from pydantic import BaseModel, EmailStr
from datetime import datetime

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
        orm_mode = True
        
        
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
        orm_mode = True
        
class EventDetail(EventResponse):
    organizer_id: int