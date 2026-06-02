"""Modelo de domínio do núcleo: ADRs (Architecture Decision Records).

Uma decisão segue um ciclo de vida explícito (`proposed → accepted →
superseded/deprecated`), espelhando o estado de um ADR real. A transição para
`accepted` é o gatilho de um evento de domínio publicado de forma assíncrona.
"""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class DecisionStatus(enum.StrEnum):
    proposed = "proposed"
    accepted = "accepted"
    superseded = "superseded"
    deprecated = "deprecated"


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    system_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(200))
    context: Mapped[str] = mapped_column(Text, default="")
    decision: Mapped[str] = mapped_column(Text, default="")
    consequences: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[DecisionStatus] = mapped_column(
        Enum(DecisionStatus), default=DecisionStatus.proposed
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
