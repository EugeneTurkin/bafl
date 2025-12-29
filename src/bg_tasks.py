import pathlib
import shutil

from fastapi import HTTPException

from src.config import config
from src.models import UploadData


def copy_file(data: UploadData):
    src = config.UPLOAD_DST / data.fname
    dst = config.FILES_DIR

    if not src.exists():
        raise HTTPException(500)

    src = pathlib.Path(shutil.copy2(src, dst))

