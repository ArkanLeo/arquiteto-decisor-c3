"""Contratos de entrada/saída (DTOs) do decisions-service."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import DecisionStatus


class DecisionCreate(BaseModel):
    system_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=3, max_length=200)
    context: str = Field(default="", max_length=8000)
    decision: str = Field(default="", max_length=8000)
    consequences: str = Field(default="", max_length=8000)


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    system_id: str
    title: str
    context: str
    decision: str
    consequences: str
    status: DecisionStatus
    version: int
    created_at: datetime
    updated_at: datetime
