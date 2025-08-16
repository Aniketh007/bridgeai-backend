from database.init_db import get_db
from schemas.users import UserCreate, UserLogin
from utils.auth import hash_password, verify_password

class UserService:

    async def create_user(self, user_data: UserCreate):
        """
        Create a new user in the database.
        """
        prisma = await get_db.get_client()
        hashed_password = hash_password(user_data.password)
        user = await prisma.user.create(
            data={
                "email": user_data.email,
                "passwordHash": hashed_password,
                "name": user_data.name,
                "phone": user_data.phone
            }
        )
        return user

    async def get_user_by_email(self, email: str):
        """
        Get a user by email.
        """
        prisma = await get_db.get_client()
        user = await prisma.user.find_unique(
            where={
                "email": email
            }
        )
        return user

    async def login_user(self, user_data: UserLogin):
        """
        Login a user.
        """
        prisma = await get_db.get_client()
        user = await prisma.user.find_unique(
            where={
                "email": user_data.email
            }
        )
        if user and verify_password(user_data.password, user.passwordHash):
            return user
        return None

user_service = UserService()