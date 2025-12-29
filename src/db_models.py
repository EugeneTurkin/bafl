from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import func, DateTime, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.enums import Status


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
    # ext: Mapped[str]
    # link: Mapped[str]
    # final_name: Mapped[str]
    rename: Mapped[str | None] = mapped_column(default=None, nullable=True)
    notif_email: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "upload_ticket",
    }
