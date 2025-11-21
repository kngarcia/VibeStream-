from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# Crear engine asíncrono
engine = create_async_engine(
    settings.db_url,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

# Crear session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base para modelos
Base = declarative_base()


async def get_db():
    """Dependency para obtener sesión de BD"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Inicializar base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
