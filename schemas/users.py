from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserCreate(BaseModel):
    """
    Model for creating a new user.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    """
    Model for user login.
    """
    email: EmailStr
    password: str

class ScanCreate(BaseModel):
    userId: str # This should be the Convex document ID for the user
    url: str

class PaymentWebhook(BaseModel):
    userId: str
    amount: int
    currency: str = "usd"
    transactionId: str
    creditsPurchased: int

class UserResponse(BaseModel):
    """
    Model for user response.
    """
    id: str
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    createdAt: datetime

    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    """
    Model for token response.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse