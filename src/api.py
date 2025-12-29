from fastapi import APIRouter
from pydantic import BaseModel

from src.database import DB
from src.db_models import Ticket, UploadTicket
from src.tasks import test_task


router = APIRouter(prefix="/api")


@router.get("/test")
async def test_func():
    result = test_task()
    return "yes"
