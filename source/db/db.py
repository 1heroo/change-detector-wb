from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from source.core.settings import settings

DATABASE_URL = settings.DATABASE_URL


async_engine = create_async_engine(DATABASE_URL, pool_size=10)


async_session = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False,
)

Base = declarative_base()


async def get_session():
    db = async_session()
    try:
        yield db
    finally:
        db.close()
