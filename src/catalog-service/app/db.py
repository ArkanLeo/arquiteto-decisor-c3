"""Configuração de persistência do catalog-service.

Segue o padrão *database-per-service*: este serviço é dono exclusivo do seu
schema. Em produção aponta para um Postgres dedicado; em desenvolvimento/CI
cai para um SQLite local, permitindo subir o serviço sem infraestrutura.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./catalog.db")

# check_same_thread só é relevante para SQLite usado em testes/dev.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    """Dependência FastAPI: abre e fecha uma sessão por requisição."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
