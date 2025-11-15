"""
Database base configuration and session management
"""

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://tpa_user:tpa_password@localhost:5432/tpa_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """
    Dependency function to get database session

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables if they don't exist
    This runs automatically on app startup
    """
    logger.info("🔧 Initializing database...")
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered with Base
            from . import models  # noqa: F401
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}", exc_info=True)
        raise


async def close_db():
    """
    Close database connections
    This runs automatically on app shutdown
    """
    logger.info("🔌 Closing database connections...")
    await engine.dispose()
    logger.info("✅ Database connections closed")
