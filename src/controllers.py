from __future__ import annotations

import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
import shutil

from fastapi import HTTPException
import httpx
from sqlalchemy import desc, insert, select

from src.config import config
from src.database import DB
from src.db_models import Ticket, UploadTicket
from src.enums import Status
from src.models import RequestData
from src.tasks import test_task


if TYPE_CHECKING:
    from src.models import UploadData
    from sqlalchemy.ext.asyncio import AsyncSession


async def home(db: AsyncSession):
    stmt = select(UploadTicket).order_by(desc(UploadTicket.created_at))  # TODO: relocate it to models and add pagination
    result = await db.scalars(stmt)
    return result.all()


async def submit_upload(db: AsyncSession, upload_data: UploadData, request_data: RequestData):
    new_ticket_id = await UploadTicket.create_and_add(db, upload_data, request_data)
    await db.commit()
    await db.close()
    test_task(id=new_ticket_id)

    return None
