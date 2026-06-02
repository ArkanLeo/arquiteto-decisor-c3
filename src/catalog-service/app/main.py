"""catalog-service — cadastro de sistemas/times do Arquiteto Decisor.

Serviço síncrono (REST) consultado pelo decisions-service para validar a que
sistema uma decisão pertence. Mantém seu próprio banco (database-per-service).
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, engine, get_session
from .models import SystemEntry
from .schemas import SystemCreate, SystemOut

app = FastAPI(
    title="Arquiteto Decisor — Catalog Service",
    version="1.0.0",
    description="Catálogo de sistemas e times aos quais as decisões se vinculam.",
)


@app.on_event("startup")
def _bootstrap() -> None:
    # Em produção, a evolução de schema é feita por migrações (Alembic).
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "catalog-service"}


@app.post(
    "/systems",
    response_model=SystemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["systems"],
)
def create_system(payload: SystemCreate, db: Session = Depends(get_session)) -> SystemEntry:
    if db.scalar(select(SystemEntry).where(SystemEntry.name == payload.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Sistema já cadastrado")
    entry = SystemEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/systems", response_model=list[SystemOut], tags=["systems"])
def list_systems(db: Session = Depends(get_session)) -> list[SystemEntry]:
    return list(db.scalars(select(SystemEntry).order_by(SystemEntry.created_at)))


@app.get("/systems/{system_id}", response_model=SystemOut, tags=["systems"])
def get_system(system_id: str, db: Session = Depends(get_session)) -> SystemEntry:
    entry = db.get(SystemEntry, system_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sistema não encontrado")
    return entry
