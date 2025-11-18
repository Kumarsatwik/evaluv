from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional
from ..models.user import User, UserCreate, UserUpdate
from ..utils.security import get_password_hash, verify_password
from ..utils.exceptions import UserNotFoundException, DuplicateUserException
from uuid import UUID


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        statement = select(User).where(User.id == user_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        statement = select(User).where(User.email == email)
        result = await self.session.exec(statement)
        return result.first()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        statement = select(User).where(User.username == username)
        result = await self.session.exec(statement)
        return result.first()

    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_create.email)
        if existing_user:
            raise DuplicateUserException()
        
        existing_user = await self.get_user_by_username(user_create.username)
        if existing_user:
            raise DuplicateUserException()
        
        # Hash password
        hashed_password = get_password_hash(user_create.password)
        
        # Create user
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            hashed_password=hashed_password
        )
        
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        
        return db_user

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            raise UserNotFoundException()
        
        # Update fields
        for field, value in user_update.model_dump(exclude_unset=True).items():
            setattr(db_user, field, value)
        
        await self.session.commit()
        await self.session.refresh(db_user)
        
        return db_user

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        user = await self.get_user_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise UserNotFoundException()
        
        return user

    async def get_all_users(self) -> list[User]:
        """Get all users"""
        statement = select(User)
        result = await self.session.exec(statement)
        return list(result.all())

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if not verify_password(old_password, user.hashed_password):
            return False

        user.hashed_password = get_password_hash(new_password)
        await self.session.commit()
        return True
