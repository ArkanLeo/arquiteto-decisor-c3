# 🏅 Gold Plating — Artefatos de Excelência

Esta pasta reúne entregas **acima do mínimo exigido**, demonstrando capricho e
relevância técnica. Cada item abaixo amplia a qualidade do projeto sem ser
requisito obrigatório.

| Artefato | O que é | Por que agrega |
|---|---|---|
| [`adr-new.py`](adr-new.py) | Gerador de ADRs a partir do template | Automação **temática**: a ferramenta gera os próprios artefatos do produto, padronizando numeração e estrutura |
| [`ci-pipeline.md`](ci-pipeline.md) | Documentação do pipeline de CI | Explica a automação real em `.github/workflows/ci.yml` (lint + testes por serviço + validação do compose) |
| [`observability.md`](observability.md) | Estratégia de observabilidade | Tracing distribuído, métricas e logs correlacionados para fluxos síncronos e assíncronos |
| [`openapi/`](openapi/) | Notas sobre contratos OpenAPI | Cada serviço FastAPI expõe `/openapi.json`; aqui está como agregá-los |

## Destaque: automação de ADRs

O Arquiteto Decisor é uma ferramenta sobre decisões — então automatizamos a
criação de decisões. O script `adr-new.py` lê `docs/adrs/template.md`, descobre o
próximo número sequencial e gera um novo ADR pronto para preencher:

```bash
python gold-plating/adr-new.py "Escolha do banco de eventos"
# → cria docs/adrs/0004-escolha-do-banco-de-eventos.md
```
