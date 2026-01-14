from app.database.models import Users  # type: ignore
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email_or_username(self, email: str, username: str) -> Users | None:
        stmt = select(Users).where(  # type: ignore
            or_(
                col(Users.email) == email,
                col(Users.username) == username,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()  # scalars() 會自動取出 User

    async def create(self, user: Users) -> Users:
        self.session.add(user)
        # flush 會將物件存入資料庫，並取得自動生成的 ID，但不會結束 transaction
        await self.session.flush()  # 不 commit (transaction 是 Service 的責任)
        return user
