import os
from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from src import controllers
from src.config import config
from src.models import Destinations, UploadData


router = APIRouter()
templates = Jinja2Templates(directory="templates")


CUSTOM_MESSAGES = {
    "invalid_email": "Указанный некорректный адрес электронной почты",
    "no_dest": "необходимо выбрать минимум одно место назначения для загрузки",
    "no_fname": "необходимо выбрать файл для загрузки",
    "string_pattern_mismatch": "введено некорректное имя файла: обратитесь к справке, нажав на кнопку справа от поля ввода",
    "file_no_longer_exists": "указанный файлл более не существует в указанном расположении",
}


def convert_errors(
    e: ValidationError, custom_messages: dict[str, str]
) -> list[ErrorDetails]:
    new_errors: list[ErrorDetails] = []
    for error in e.errors():
        custom_message = custom_messages.get(error['type'])
        if custom_message:
            ctx = error.get('ctx')
            error['msg'] = (
                custom_message.format(**ctx) if ctx else custom_message
            )
        new_errors.append(error)
    return new_errors


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html", context={"context": "Homepage"}
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    files = [file.name for file in os.scandir(config.NETWORK_STORAGE / config.STORAGE_DIR)]
    return templates.TemplateResponse(
        request=request, name="upload.html", context={"files": files}
    )


@router.post("/upload")
async def submit_upload(
    request: Request,
    fname: Annotated[str | None, Form()] = None,
    rename: Annotated[str | None, Form()] = None,
    dest_yandex: Annotated[str | None, Form()] = None,
    dest_ftp_moscow: Annotated[str | None, Form()] = None,
    dest_ftp_morning: Annotated[str | None, Form()] = None,
    notif_email: Annotated[str | None, Form()] = None,
):
    try:
        destinations = Destinations(
            dest_yandex=dest_yandex,
            dest_ftp_moscow=dest_ftp_moscow,
            dest_ftp_morning=dest_ftp_morning,
        )
        data=UploadData(
            fname=fname,
            rename=rename,
            destinations=destinations,
            notif_email=notif_email,
        )
        UploadData.model_validate(data)
    except ValidationError as e:
        errors = convert_errors(e, CUSTOM_MESSAGES)
        files = [file.name for file in os.scandir(config.NETWORK_STORAGE / config.STORAGE_DIR) if file.name != fname]

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

    redirect_home_url = request.url_for("home")
    return RedirectResponse(redirect_home_url, status_code=status.HTTP_303_SEE_OTHER)
