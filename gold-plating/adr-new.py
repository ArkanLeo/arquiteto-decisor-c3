#!/usr/bin/env python3
"""Gera um novo ADR a partir do template do projeto.

Uso:
    python gold-plating/adr-new.py "Título da decisão"

Descobre o maior número de ADR existente em docs/adrs/, incrementa, gera um
slug a partir do título e cria o arquivo já com cabeçalho preenchido (status
proposto e data de hoje). É a automação temática do Arquiteto Decisor: a
ferramenta de decisões padroniza a criação das próprias decisões.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adrs"
TEMPLATE = ADR_DIR / "template.md"


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return normalized or "decisao"


def next_number() -> int:
    maior = 0
    for arquivo in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"):
        maior = max(maior, int(arquivo.name[:4]))
    return maior + 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: python gold-plating/adr-new.py \"Título da decisão\"", file=sys.stderr)
        return 2

    titulo = " ".join(argv[1:]).strip()
    numero = next_number()
    nome = f"{numero:04d}-{slugify(titulo)}.md"
    destino = ADR_DIR / nome

    if destino.exists():
        print(f"Já existe: {destino}", file=sys.stderr)
        return 1

    conteudo = TEMPLATE.read_text(encoding="utf-8")
    conteudo = conteudo.replace(
        "# ADR NNNN — <título curto da decisão>",
        f"# ADR {numero:04d} — {titulo}",
    )
    conteudo = conteudo.replace(
        "- **Status:** proposto | aceito | substituído por [ADR-XXXX] | obsoleto",
        "- **Status:** proposto",
    )
    conteudo = conteudo.replace("- **Data:** AAAA-MM-DD", f"- **Data:** {date.today().isoformat()}")

    destino.write_text(conteudo, encoding="utf-8")
    print(f"✓ Criado {destino.relative_to(ADR_DIR.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
