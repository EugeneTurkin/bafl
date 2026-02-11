import datetime
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import time

from fastapi import HTTPException
import httpx
from sqlalchemy import select

from src.baflmail import email
from src.config import config, huey
from src.database import sync_session
from src.enums import Status
from src.db_models import UploadTicket
from src.funcs import change_ticket_status_returning_ticket, check_yadisk_free_space, commence_upload, get_upload_link
from src.utils import data_generator_progress_bar


@huey.task()
def test_task(id: int):
    db = sync_session()
    try:
        ticket = change_ticket_status_returning_ticket(db, id, Status.ACCEPTED)
        with TemporaryDirectory(dir=config.FILES_DIR) as tmpdir:
            fpath = shutil.copy2(ticket.src, tmpdir)
            fsize = Path(fpath).stat().st_size
            headers = dict(Authorization=f"OAuth {config.YADISK_OAUTH_TOKEN}")

            with httpx.Client(base_url=str(config.YADISK_API_BASE_URL), headers=headers) as client:
                upload_link, params = get_upload_link(client, ticket)

                check_yadisk_free_space(db, client, fsize)  # TODO: needs to be tested

                public_url = commence_upload(db, client, upload_link, ticket, params, fsize)

                email.send(  # TODO: move server email creds to .env file
                    subject=f"cсылка -- {ticket.fname}",
                    sender="test@komigor.com",
                    receivers=[ticket.notif_email],
                    text=f"{public_url}",
                )
    except Exception as e:
        db.rollback()
        print("something went wrong")
        print(e)
        raise
    finally:
        db.close()
