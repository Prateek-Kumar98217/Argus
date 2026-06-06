#Manage engine and session configs seprately


from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.settings import settings

engine = create_async_engine(
    settings.db_uri, 
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

AsyncSessionLocal = async_sessionmaker(
    bind= engine,
    class_=AsyncSession,
    expire_on_commit=False
)