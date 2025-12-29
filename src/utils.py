# https://docs.pydantic.dev/latest/errors/errors/#customize-error-messages
import os

from pydantic import ValidationError
from pydantic_core import ErrorDetails
from tqdm import tqdm


CUSTOM_MESSAGES = {
    "invalid_email": "Указан некорректный адрес электронной почты",
    "no_dest": "необходимо выбрать минимум одно место назначения для загрузки",
    "no_fname": "необходимо выбрать файл для загрузки",
    "string_pattern_mismatch": "введено некорректное имя файла: обратитесь к справке, нажав на кнопку справа от поля ввода",
    "string_too_long": "введено слишком длинное название",
    "string_too_short": "введено слишком короткое название",
    "path_not_file": "либо выбранное имя указывает не на файл, либо указанный файл более не существует",
    "bad_ext": "выбранный файл имеет некорректное расширение. скорее всего это ссылка или скрипт. обратитесь к сис. администратору",
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


def data_generator_progress_bar(fpath):
    size = os.path.getsize(fpath)
    with tqdm(ascii=True, unit_scale=True, unit='B', unit_divisor=1024, total=size) as bar:
        with open(fpath, "rb") as f:
            print("opened file")
            while data := f.read(1024):
                yield data
                bar.update(len(data))
