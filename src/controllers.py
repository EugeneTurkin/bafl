from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.models import UploadData


def submit_upload(upload_data: UploadData):
    ...
