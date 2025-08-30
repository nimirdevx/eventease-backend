from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from typing import List, Literal
import re

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password must be at least 8 characters")
    role: Literal["attendee", "organizer", "admin"] = Field(default="attendee", description="User role")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v.strip()):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: EmailStr
    role: str
        
        
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=1, description="User password")
    

class EventCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Event title")
    description: str | None = Field(None, max_length=2000, description="Event description")
    date: datetime = Field(..., description="Event date and time")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and not v.strip():
            return None  # Convert empty string to None
        return v.strip() if v else v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if v <= datetime.now():
            raise ValueError('Event date must be in the future')
        return v

class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str | None
    date: datetime
    organizer_id: int
        
class EventDetail(EventResponse):
    model_config = ConfigDict(from_attributes=True)
    
    organizer_id: int
    comments: List['CommentResponse'] = []


# Comment schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="Comment content")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Comment cannot be empty or only whitespace')
        return v.strip()


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content: str
    created_at: datetime
    user_id: int
    event_id: int
    user: UserResponse


# Notification schemas
class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=1000, description="Notification message")
    user_id: int = Field(..., gt=0, description="User ID")
    event_id: int | None = Field(None, gt=0, description="Optional event ID")
    
    @field_validator('title', 'message')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty or only whitespace')
        return v.strip()


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    user_id: int
    event_id: int | None


class NotificationUpdate(BaseModel):
    is_read: bool