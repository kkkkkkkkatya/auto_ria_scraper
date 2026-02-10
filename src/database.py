from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)
