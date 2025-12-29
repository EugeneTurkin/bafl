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
from src.utils import data_generator_progress_bar


@huey.task()
def test_task(id: int):
    print(f"id is {id}")
    db = sync_session()
    try:
        print("were trying")
        stmt = select(UploadTicket).where(UploadTicket.id == id)
        ticket = db.scalar(stmt)
        ticket.status = Status.ACCEPTED
        db.add(ticket)
        db.flush()

        with TemporaryDirectory(dir=config.FILES_DIR) as tmpdir:
            fpath = shutil.copy2(ticket.src, tmpdir)
            fsize = Path(fpath).stat().st_size
            headers = dict(Authorization=f"OAuth {config.YADISK_OAUTH_TOKEN}")
            yadisk_fpath = config.YADISK_DIR + (ticket.rename if ticket.rename else ticket.fname)
            with httpx.Client(base_url=str(config.YADISK_API_BASE_URL), headers=headers) as client:
                # check fname doesnt already exist and get upload link
                spoofed_data = json.dumps({"os": "windows"}, separators=(',', ':'))
                headers = {"User-Agent": f"Yandex.Disk {spoofed_data}"}
                params = dict(path=yadisk_fpath)
                resp = client.get("/resources/upload", params=params, headers=headers)
                if resp.status_code == 409:
                    params = dict(path=yadisk_fpath + " " + datetime.datetime.now().strftime("%d%m%y%H%M%S%f"))
                    resp = client.get("/resources/upload", params=params, headers=headers)
                    if resp.status_code != 200:
                        raise HTTPException(500, "could not retrieve upload link from yandex")
                elif resp.status_code != 200:
                    raise HTTPException(500, "could not retrieve upload link from yandex")
                upload_link = resp.json()["href"]

                # check yadisk free space  # TODO: needs to be tested
                resp = client.get("")
                if resp.status_code != 200:
                    ticket.status = Status.FAILED
                    db.add(ticket)
                    db.commit()
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

                # commence upload
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

                ticket.status = Status.COMPLETED
                ticket.finished_at = datetime.datetime.now()
                # TODO: here we need to also add a link, a final name as it is in dst, and perhaps an extension
                db.add(ticket)
                db.commit()

                email.send(
                    subject=f"cсылка -- {ticket.fname}",
                    sender="test@komigor.com",
                    receivers=[ticket.notif_email],
                    text=f"{resp.json()["public_url"]}",
                )
    except Exception as e:
        db.rollback()
        print("something went wrong")
        print(e)
        raise
    finally:
        db.close()
