import os
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from src import controllers
from src.config import config
from src.database import DB
from src.models import Destinations, RequestData, UploadData
from src.utils import convert_errors, CUSTOM_MESSAGES


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(db: DB, request: Request):
    tickets = await controllers.home(db=db)
    return templates.TemplateResponse(
        request=request, name="home.html",
        context={
            "context": "Homepage",
            "client": f"{request.client.host}:{request.client.port}",
            "tickets": tickets,
        }
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    # TODO: на этом и аналогичных вызовах, если хранилище недоступно, упадём с ошибкой. нужно обработать, прикрутить хэндлер, указать в сигне эндпоинта возможные статус коды. ещё надо проверять права потому что у сервера может не оказаться прав на чтение
    files = [file.name for file in sorted(os.scandir(config.UPLOAD_DST), key=lambda x: x.stat().st_mtime, reverse=True) if file.is_file()]
    try:
        files.remove("Thumbs.db")
    except ValueError:
        pass
    return templates.TemplateResponse(
        request=request, name="upload.html", context={"files": files}
    )


@router.post("/upload")
async def submit_upload(
    db: DB,
    request: Request,
    fname: Annotated[str | None, Form()] = None,
    rename: Annotated[str | None, Form()] = None,
    dest_yandex: Annotated[str | None, Form()] = None,
    dest_ftp_moscow: Annotated[str | None, Form()] = None,
    dest_ftp_morning: Annotated[str | None, Form()] = None,
    notif_email: Annotated[str | None, Form()] = None,
):
    try:
        request_data = RequestData(request_host=f"{request.client.host}", request_port=f"{request.client.port}")
        destinations = Destinations(
            dest_yandex=dest_yandex,
            dest_ftp_moscow=dest_ftp_moscow,
            dest_ftp_morning=dest_ftp_morning,
        )
        upload_data=UploadData(
            fpath=config.UPLOAD_DST / fname,
            rename=rename,
            destinations=destinations,
            notif_email=notif_email,
        )
        UploadData.model_validate(upload_data)
    except ValidationError as e:
        errors = convert_errors(e, CUSTOM_MESSAGES)
        files = [file.name for file in sorted(os.scandir(config.UPLOAD_DST), key=lambda x: x.stat().st_mtime, reverse=True) if (file.is_file() and file.name != fname)]
        try:
            files.remove("Thumbs.db")
        except ValueError:
            pass

        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                "errors": errors,
                "files": files,
                "prev_fname": fname,
                "prev_rename": rename,
                "prev_notif_email": notif_email,
                "prev_dest_yandex": dest_yandex,
                "prev_dest_ftp_moscow": dest_ftp_moscow,
                "prev_dest_ftp_morning": dest_ftp_morning,
            },
        )

    _ = await controllers.submit_upload(db, upload_data, request_data)

    redirect_home_url = request.url_for("home")
    return RedirectResponse(redirect_home_url, status_code=status.HTTP_303_SEE_OTHER)
