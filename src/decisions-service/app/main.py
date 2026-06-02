"""decisions-service — núcleo do Arquiteto Decisor.

Responsável pelo ciclo de vida dos ADRs: criação, listagem, consulta e
aprovação. Combina os dois modelos de comunicação (ADR 0003):
  • síncrono  — valida o sistema no catalog-service antes de criar a decisão;
  • assíncrono — publica `decision.approved` ao aceitar uma decisão.
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .catalog_client import CatalogUnavailable, system_exists
from .db import Base, engine, get_session
from .events import publish_decision_approved
from .models import Decision, DecisionStatus
from .schemas import DecisionCreate, DecisionOut

app = FastAPI(
    title="Arquiteto Decisor — Decisions Service",
    version="1.0.0",
    description="Registro, versionamento e aprovação de decisões arquiteturais (ADRs).",
)


@app.on_event("startup")
def _bootstrap() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "decisions-service"}


@app.post(
    "/decisions",
    response_model=DecisionOut,
    status_code=status.HTTP_201_CREATED,
    tags=["decisions"],
)
def create_decision(payload: DecisionCreate, db: Session = Depends(get_session)) -> Decision:
    # Comunicação síncrona com o catálogo (com timeout/resiliência).
    try:
        if not system_exists(payload.system_id):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sistema inexistente")
    except CatalogUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Catálogo indisponível, tente mais tarde"
        ) from None

    decision = Decision(**payload.model_dump())
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@app.get("/decisions", response_model=list[DecisionOut], tags=["decisions"])
def list_decisions(db: Session = Depends(get_session)) -> list[Decision]:
    return list(db.scalars(select(Decision).order_by(Decision.created_at)))


@app.get("/decisions/{decision_id}", response_model=DecisionOut, tags=["decisions"])
def get_decision(decision_id: str, db: Session = Depends(get_session)) -> Decision:
    decision = db.get(Decision, decision_id)
    if not decision:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Decisão não encontrada")
    return decision


@app.post("/decisions/{decision_id}/approve", response_model=DecisionOut, tags=["decisions"])
def approve_decision(decision_id: str, db: Session = Depends(get_session)) -> Decision:
    decision = db.get(Decision, decision_id)
    if not decision:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Decisão não encontrada")
    if decision.status == DecisionStatus.accepted:
        raise HTTPException(status.HTTP_409_CONFLICT, "Decisão já aceita")

    decision.status = DecisionStatus.accepted
    db.commit()
    db.refresh(decision)

    # Efeito colateral propagado de forma assíncrona (não bloqueia a resposta).
    publish_decision_approved(
        {
            "decision_id": decision.id,
            "system_id": decision.system_id,
            "title": decision.title,
            "version": decision.version,
        }
    )
    return decision
