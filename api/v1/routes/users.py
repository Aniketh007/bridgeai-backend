from fastapi import APIRouter, HTTPException, Depends
from schemas.users import UserCreate, UserLogin, TokenResponse, UserResponse
from core.user_service import user_service
from utils.auth import create_access_token
from utils.dependencies import get_current_user
from datetime import timedelta

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate):
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await user_service.create_user(user_data)
    if not user:
        raise HTTPException(status_code=500, detail="User creation failed")
    return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            createdAt=user.createdAt
        )

@router.get("/me", response_model=UserResponse)
async def profile(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await user_service.login_user(user_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            createdAt=user.createdAt
        )
    )