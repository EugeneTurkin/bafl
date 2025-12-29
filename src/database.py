from typing import Annotated, Iterator
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, scoped_session


class Base(AsyncAttrs, DeclarativeBase):
    ...


async_engine = create_async_engine("sqlite+aiosqlite:///database.db")
sync_engine = create_engine("sqlite+pysqlite:///database.db")

async_session = async_sessionmaker(bind=async_engine, expire_on_commit=False)
sync_session = scoped_session(sessionmaker(bind=sync_engine))


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()  # Auto-rollback on error
            raise
        finally:
            await session.close()  # Always close session


def get_sync_db() -> Iterator[scoped_session[Session]]:  # pragma: no cover
    """Create session for a request then close it when request is done."""
    try:  # pylint: disable=too-many-try-statements
        yield sync_session
        sync_session.commit()
    except Exception:  # noqa: BLE001
        sync_session.rollback()
    finally:
        sync_session.close()


# used by FastAPI routes to inject database session dependency
syncDB = Annotated[Session, Depends(get_db)]
DB = Annotated[AsyncSession, Depends(get_db)]
