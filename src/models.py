import pathlib
from typing import Any

from pydantic import BaseModel, SerializerFunctionWrapHandler, ValidationError, computed_field, EmailStr, Field, field_serializer, field_validator, model_validator
from pydantic_core import ErrorDetails, PydanticCustomError

from src.config import config
from src.enums import HTML
from src.exceptions import TestException


class Destinations(BaseModel):
    dest_yandex: HTML.InputValue | None = Field(...)
    dest_ftp_moscow: HTML.InputValue | None = Field(...)
    dest_ftp_morning: HTML.InputValue | None = Field(...)


class UploadData(BaseModel):
    fname: str = Field(...)
    rename: str | None = Field(default=None, validate_default=False, min_length=5, max_length=120,
                        pattern=r"^[a-zA-Z0-9А-Яа-я][\w ,.!?\"\':;»«]{3,118}[a-zA-Z0-9А-Яа-я.!?\"\'»«]$")  # если поле остаётся незаполненным, приходит простая строка которая из-за паттерна бракутеся на стадии создания модели. нужно это обойти либо добавив в регулярку возможность пустой строки либо обойдя валидацию поля пайдентиком
    destinations: Destinations = Field(...)
    notif_email: EmailStr = Field(...)

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

    @field_validator("fname", "notif_email", mode="after")
    @classmethod
    def check_field_value_is_provided(cls, field_value: str | EmailStr):
        if not field_value:
            if isinstance(field_value, EmailStr):
                raise PydanticCustomError("invalid_email", "input is an invalid email address")
            raise PydanticCustomError("no_fname", "no filename provided")
        return field_value

    @field_validator("fname", mode="after")
    @classmethod
    def check_file_still_exists(cls, fname: str):
        fpath = config.NETWORK_STORAGE / config.STORAGE_DIR / fname
        if not fpath.exists():
            raise PydanticCustomError("file_no_longer_exists", "provided file does no longer exist in specified location")
        return fname
