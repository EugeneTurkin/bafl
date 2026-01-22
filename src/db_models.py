from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import ForeignKey, insert
from sqlalchemy import func, DateTime, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Base
from src.enums import Status
from src.models import RequestData, UploadData


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_type: Mapped[str]
    # owner: Mapped[str]  # TODO: add later when we have User table
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    creation_ip: Mapped[str] = mapped_column(default=None, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    status: Mapped[Status] = mapped_column(default=Status.PENDING)

    __mapper_args__ = {
        "polymorphic_identity": "ticket",
        "polymorphic_on": "ticket_type",
    }


class UploadTicket(Ticket):
    __tablename__ = "upload_ticket"

    id: Mapped[int] = mapped_column(ForeignKey("ticket.id"), primary_key=True)
    src: Mapped[str]
    dst: Mapped[str]
    fname: Mapped[str]
    ext: Mapped[str] = mapped_column(nullable=False)
    # link: Mapped[str]
    # final_name: Mapped[str]
    rename: Mapped[str | None] = mapped_column(default=None, nullable=True)
    notif_email: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "upload_ticket",
    }

    def change_status(self, db, status):
        self.status = status
        db.add(self)
        db.flush()

    def finalize(self, db, link, final_name):
        self.finished_at = datetime.now()
        self.link = link
        self.final_name = final_name
        db.add(self)
        db.flush()
        self.change_status(db, Status.COMPLETED)
        return ...

    async def _add_instance(self, db: AsyncSession) -> int:
        try:
            result = await db.execute(insert(UploadTicket).returning(UploadTicket.id), self.__dict__)
            await db.flush()
            id = result.scalar()
        except:
            print("couldn't add instance to database")
            raise HTTPException(500, "database exception")
        return id

    @classmethod
    async def _create_instance_from_upload_and_request_data(cls, upload_data: UploadData, request_data: RequestData) -> UploadTicket:
        try:
            new_instance = UploadTicket(
                creation_ip=str(request_data.request_host),
                src=str(upload_data.fpath),
                ext=upload_data.fpath.suffix,
                dst="файлообменник",  # TODO: this one is a big bad. need to choose how to handle multiple destinations and get rid of that magic value somehow some day
                fname=upload_data.fpath.stem,
                rename=upload_data.rename,
                notif_email=str(upload_data.notif_email),
            )
        except:
            print("couldn't create a new ticket instance")
            raise HTTPException(500, "orm exception")
        return new_instance

    @classmethod
    async def create_and_add(cls, db: AsyncSession, upload_data: UploadData, request_data: RequestData) -> int:
        new_ticket = await UploadTicket._create_instance_from_upload_and_request_data(upload_data, request_data)
        id = await new_ticket._add_instance(db)

        return id
