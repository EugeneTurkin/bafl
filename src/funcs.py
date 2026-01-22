import datetime
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import time

from fastapi import HTTPException
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.baflmail import email
from src.config import config, huey
from src.database import sync_session
from src.enums import Status
from src.db_models import UploadTicket
from src.utils import data_generator_progress_bar


def change_ticket_status_returning_ticket(db: Session, id: int, status: Status, finished_at=None):
    stmt = select(UploadTicket).where(UploadTicket.id == id)
    ticket = db.scalar(stmt)
    ticket.status = status
    if finished_at:
        ticket.finished_at = finished_at
    db.add(ticket)
    db.commit()
    db.close()
    return ticket


def get_upload_link(client, ticket: UploadTicket):
    spoofed_data = json.dumps({"os": "windows"}, separators=(',', ':'))
    headers = {"User-Agent": f"Yandex.Disk {spoofed_data}"}
    yadisk_fpath_no_ext = config.YADISK_DIR + (ticket.rename if ticket.rename else ticket.fname)
    params = dict(path=yadisk_fpath_no_ext + ticket.ext)

    resp = client.get("/resources/upload", params=params, headers=headers)
    if resp.status_code == 409:
        params = dict(path=yadisk_fpath_no_ext + " " + datetime.datetime.now().strftime("%d%m%y%H%M%S%f") + ticket.ext)
        resp = client.get("/resources/upload", params=params, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(500, "could not retrieve upload link from yandex")
    elif resp.status_code != 200:
        raise HTTPException(500, "could not retrieve upload link from yandex")

    return resp.json()["href"], params


def check_yadisk_free_space(db, client, fsize):
    resp = client.get("")
    if resp.status_code != 200:
        ticket = change_ticket_status_returning_ticket(db, ticket.id, Status.FAILED)
        raise HTTPException(500, "yandex is down apparently")  # TODO: replace with retry by dividing the single task into a task pipeline
    resp = resp.json()
    free_space = resp.get("total_space") - resp.get("used_space")
    trash_size = resp.get("trash_size")
    if free_space < fsize:
        if (trash_size > fsize) or ((free_space + trash_size) > fsize):
            resp = client.delete("/trash/resources")
            if resp.status_code == 204:
                pass
            elif resp.status_code == 202:
                time.sleep(60)
            else:
                raise HTTPException(500, "couldn't delete yadisk trash")
        else:
            raise HTTPException(500, "not enough space")


def commence_upload(db, client, upload_link, ticket, params, fsize):
    resp = client.put(upload_link, content=data_generator_progress_bar(ticket.src), timeout=None)

    if resp.status_code not in (201, 202):  # TODO: if 202 we need a timeout, a check until 201, then proceed
        raise HTTPException(500, "couldn't upload or something wrong with yandex")  # TODO: exc

    resp = client.put("/resources/publish", params=params)

    if resp.status_code != 200:
        raise HTTPException(500, "somethimg wrong with yandex")  # TODO: exc

    params["fields"] = "public_url,size,name"  # TODO: size, perhaps other metadata as well
    resp = client.get("/resources", params=params)

    if resp.status_code != 200:
        raise HTTPException(500, "somethimg wrong with yandex")  # TODO: exc

    if not resp.json()["size"] == fsize:
        raise HTTPException(500, "file wasnt uploaded in full")

    # TODO: here we need to also add a link, a final name as it is in dst, and perhaps an extension
    change_ticket_status_returning_ticket(db, ticket.id, Status.COMPLETED, finished_at=datetime.datetime.now())

    return resp.json()["public_url"]
