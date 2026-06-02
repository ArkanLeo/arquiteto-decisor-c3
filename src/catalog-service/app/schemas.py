"""Contratos de entrada/saída (DTOs) do catalog-service."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SystemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    team: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)


class SystemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    team: str
    description: str
    created_at: datetime
