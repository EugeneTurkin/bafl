from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, EmailStr, Field, field_validator, IPvAnyAddress
from pydantic_core import PydanticCustomError
from pydantic.types import FilePath

from src.config import config
from src.enums import HTML, BadExtensions, Status


class RequestData(BaseModel):
    request_host: IPvAnyAddress | None = Field(default=None)
    request_port: str | None


class Destinations(BaseModel):
    dest_yandex: HTML.InputValue | None = Field(...)
    dest_ftp_moscow: HTML.InputValue | None = Field(...)
    dest_ftp_morning: HTML.InputValue | None = Field(...)


class UploadData(BaseModel):
    # fname: str = Field(...)
    fpath: FilePath = Field(...)
    rename: str | None = Field(default=None, validate_default=False, min_length=5, max_length=120,
                        pattern=r"^[a-zA-Z0-9А-Яа-я][\w ,.!?\"\':;»«]{3,118}[a-zA-Z0-9А-Яа-я.!?\"\'»«]$")
    destinations: Destinations = Field(...)
    notif_email: EmailStr = Field(..., max_length=120)

    @field_validator("rename", mode="before")
    def cast_empty_strings_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("destinations", mode="after")
    @classmethod
    def check_at_least_one_destination_provided(cls, destinations: Destinations):
        destinations: dict = destinations.model_dump()
        provided_destinations = 0
        for value in destinations.values():
            if value is None:
                continue
            provided_destinations += 1

        if provided_destinations == 0:
            raise PydanticCustomError("no_dest", "no destination provided")
        return destinations

    @field_validator("fpath", "notif_email", mode="after")
    @classmethod
    def check_field_value_is_provided(cls, field_value: str | EmailStr):
        if not field_value:
            if isinstance(field_value, EmailStr):
                raise PydanticCustomError("invalid_email", "input is an invalid email address")
            raise PydanticCustomError("no_fname", "no filename provided")
        return field_value

    @field_validator("fpath", mode="after")
    @classmethod
    def check_bad_extension(cls, fpath: FilePath):
        if fpath.suffix in BadExtensions.values():
            raise PydanticCustomError("bad_ext", "invalid file provided, likely a link or a script")
        return fpath


# class UploadTicket(BaseModel):
#     id: int
#     ticket_type: str
#     created_at: datetime
#     creation_ip: str | None = Field(default=None)
#     finished_at: datetime | None = Field(default=None)
#     status: Status
#     src: str
#     dst: str
#     fname: str
#     rename: str | None = Field(default=None)
#     notif_email: str
