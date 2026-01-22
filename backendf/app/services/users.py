from app.api.schemas.users import UserCreate  # type: ignore
from app.database.models import Users  # type: ignore
from app.repositories.users import UserRepository  # type: ignore
from passlib.context import CryptContext  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

password_context = CryptContext(schemes=["argon2"])


class UserAlreadyExistsError(Exception):
    pass


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def add(self, data: UserCreate) -> Users:
        # 1. 業務邏輯檢查
        existing = await self.repo.get_by_email_or_username(data.email, data.username)
        if existing:
            # Service 層丟 domain error
            raise UserAlreadyExistsError("Email or username already exists")

        # 2. 資料轉換 (將 DTO 轉為 Model)
        user = Users(
            **data.model_dump(exclude={"password"}),
            password_hash=password_context.hash(data.password),
        )

        # 3. 持久化與事務控制
        try:
            # 這邊create 為什麼要await?
            await self.repo.create(user)
            await self.session.commit()
            # 只有在 commit 後需要立即回傳帶有 ID 的物件時才 refresh
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            raise e

        # user = User(
        #     **credentials.model_dump(exclude=["password"]),
        #     # Hashed password
        #     password_hash=password_context.hash(credentials.password),
        # )
        # self.session.add(user)
        # await self.session.commit()
        # await self.session.refresh(user)
        # return user
