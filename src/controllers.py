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
    stmt = select(UploadTicket).order_by(desc(UploadTicket.created_at))
    result = await db.scalars(stmt)
    return result.all()


async def submit_upload(db: AsyncSession, upload_data: UploadData, request_data: RequestData):
    """
    1. create db entity
    2. make sure everything is validated and operational
    3. change task status to ACCEPTED
    4. transfer the file to server (make sure there are no duplicate names along the way (including yadisk/ftp, server downloads dir))
    5. rename file if any
    5. check if enough space in destination
        5.1 if not try to clear if possible else throw exc with changing status to failed
    6. upload file
    7. run checks i.e. check file size on server and in destination
    8. delete no longer needed copy on server
    9. change statuse to complete, add finished timestamp, send notification
    """
    try:
        new_ticket = UploadTicket(
            creation_ip=str(request_data.request_host),
            src=str(upload_data.fpath),
            dst="файлообменник",
            fname=upload_data.fpath.name,
            rename=upload_data.rename,
            notif_email=str(upload_data.notif_email),
        )

        result = await db.execute(insert(UploadTicket).returning(UploadTicket.id), new_ticket.__dict__)
        new_id = result.scalar()
        await db.commit()

    except Exception as e:
        print(e)
        raise HTTPException(500, "database exception")

    test_task(id=new_id)

    return None
