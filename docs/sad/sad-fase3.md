# SAD — Documento de Arquitetura de Software
## Arquiteto Decisor — Fase 3 (Cloud & Microsserviços)

> Estrutura inspirada no template **arc42** e no modelo de visões **C4**.
> Versão 1.0 — 2026-06-02.

### Índice
1. [Introdução e Objetivos](#1-introdução-e-objetivos)
2. [Restrições da Arquitetura](#2-restrições-da-arquitetura)
3. [Contexto e Escopo](#3-contexto-e-escopo)
4. [Estratégia de Solução](#4-estratégia-de-solução)
5. [Visão de Containers (C4 L2)](#5-visão-de-containers-c4-l2)
6. [Visão de Componentes (C4 L3)](#6-visão-de-componentes-c4-l3)
7. [Visão de Execução (Runtime)](#7-visão-de-execução-runtime)
8. [Visão de Implantação (Deployment)](#8-visão-de-implantação-deployment)
9. [Arquitetura de Dados](#9-arquitetura-de-dados)
10. [Conceitos Transversais](#10-conceitos-transversais)
11. [Decisões Arquiteturais (ADRs)](#11-decisões-arquiteturais-adrs)
12. [Atributos de Qualidade](#12-atributos-de-qualidade)
13. [Riscos e Dívida Técnica](#13-riscos-e-dívida-técnica)
14. [Glossário](#14-glossário)

---

## 1. Introdução e Objetivos

O **Arquiteto Decisor** é um SaaS multi-tenant que ajuda times de engenharia a
**registrar, versionar, revisar e comparar trade-offs** de decisões
arquiteturais (ADRs). O conhecimento arquitetural costuma se perder em wikis
dispersas e conversas informais; o produto torna esse conhecimento um ativo
versionado, rastreável e vinculado aos sistemas a que pertence.

**Objetivo da Fase 3:** evoluir a aplicação — antes um monólito (Fases 1–2) —
para uma arquitetura de **microsserviços executando em nuvem**, demonstrando
estratégia de nuvem/escalabilidade, padrões de resiliência e um modelo de
comunicação adequado.

### Stakeholders

| Papel | Interesse principal |
|---|---|
| Arquiteto / Tech Lead | Registrar e aprovar decisões; rastrear histórico |
| Desenvolvedor | Consultar decisões vigentes de cada sistema |
| Coordenação acadêmica | Avaliar a qualidade arquitetural e a fundamentação |
| Equipe de operação (futuro) | Disponibilidade, custo e observabilidade |

---

## 2. Restrições da Arquitetura

| # | Restrição | Origem |
|---|---|---|
| R1 | Stack **Python + FastAPI** | Decisão de equipe |
| R2 | Deve executar localmente via `docker-compose` | Critério de avaliação |
| R3 | Documentação versionada em Markdown no repositório | Enunciado |
| R4 | Equipe pequena, sem operação dedicada | Contexto do projeto |
| R5 | Diagramas C4 em Mermaid (sem imagens externas) | Enunciado |

---

## 3. Contexto e Escopo

O sistema atende arquitetos e desenvolvedores e integra-se a um provedor de
identidade (OIDC) e a canais de notificação. Detalhe em
[`docs/diagrams/c4-context.md`](../diagrams/c4-context.md).

**Dentro do escopo:** ciclo de vida de ADRs, catálogo de sistemas, notificação
de aprovações.
**Fora do escopo (Fase 3):** autenticação real (mockada), UI web, billing.

---

## 4. Estratégia de Solução

| Driver de qualidade | Abordagem arquitetural | ADR |
|---|---|---|
| Escalabilidade | Microsserviços stateless em PaaS de contêineres, escala horizontal | [0001](../adrs/0001-estrategia-nuvem.md) |
| Resiliência | API Gateway + Circuit Breaker + Bulkhead + Timeout | [0002](../adrs/0002-padrao-resiliencia.md) |
| Desacoplamento | Comunicação híbrida (REST síncrono + eventos assíncronos) | [0003](../adrs/0003-modelo-comunicacao.md) |
| Autonomia de dados | Database-per-service | §9 |

A decomposição segue o princípio de **serviços alinhados a capacidades de
negócio** (Newman, 2021): catálogo, decisões e notificação são fronteiras de
responsabilidade distintas.

---

## 5. Visão de Containers (C4 L2)

Quatro serviços de aplicação (api-gateway, decisions, catalog, notification) e
quatro recursos de estado (2× PostgreSQL, RabbitMQ, Redis). Diagrama completo em
[`docs/diagrams/c4-container.md`](../diagrams/c4-container.md) e no README.

| Container | Tecnologia | Responsabilidade |
|---|---|---|
| api-gateway | FastAPI | Borda: roteamento, rate limit, circuit breaker |
| decisions-service | FastAPI + SQLAlchemy + pika | Núcleo: ADRs, aprovação, publicação de eventos |
| catalog-service | FastAPI + SQLAlchemy | Cadastro de sistemas/times |
| notification-service | FastAPI + pika | Consome eventos e notifica |

---

## 6. Visão de Componentes (C4 L3)

O núcleo (`decisions-service`) é detalhado em
[`docs/diagrams/c4-component-decisions.md`](../diagrams/c4-component-decisions.md):
API REST, cliente do catálogo (síncrono), publicador de eventos (assíncrono) e
repositório ORM.

---

## 7. Visão de Execução (Runtime)

Dois cenários representativos:

- **Criar decisão (síncrono):** valida o sistema no catálogo com timeout; em
  indisponibilidade, responde *fail-fast*. Ver
  [`sequence-sync.md`](../diagrams/sequence-sync.md).
- **Aprovar decisão (assíncrono):** publica `decision.approved` e responde sem
  esperar o consumidor. Ver [`sequence-async.md`](../diagrams/sequence-async.md).

---

## 8. Visão de Implantação (Deployment)

Alvo: contêineres OCI em PaaS gerenciado, com autoscaling horizontal e recursos
de estado gerenciados. Ver [`deployment-cloud.md`](../diagrams/deployment-cloud.md).
Localmente, todo o ambiente sobe com `docker-compose` (ver README).

---

## 9. Arquitetura de Dados

Adotamos **database-per-service**: cada serviço de domínio é dono exclusivo do
seu schema, acessado apenas por sua API. Não há banco compartilhado — isso
preserva o desacoplamento e permite evolução independente de schema (Richardson,
2018).

- `decisions` → entidade `Decision` (id, system_id, título, contexto, decisão,
  consequências, status, versão, timestamps).
- `catalog` → entidade `SystemEntry` (id, name, team, description, created_at).

A integridade entre serviços é **referencial fraca**: o `decisions-service`
guarda `system_id` e valida sua existência via API do catálogo, não via FK de
banco.

---

## 10. Conceitos Transversais

- **Resiliência:** timeouts, circuit breaker e bulkhead (ADR 0002).
- **Segurança:** ponto único de autenticação no gateway (OIDC previsto);
  `x-api-key`/IP como chave de rate limit no protótipo.
- **Configuração:** 12-factor via variáveis de ambiente (`.env.example`).
- **Observabilidade:** logs estruturados por serviço; tracing distribuído e
  métricas descritos em [`gold-plating/observability.md`](../../gold-plating/observability.md).
- **Mensageria:** topic exchange durável, consumo *at-least-once* com ack manual.

---

## 11. Decisões Arquiteturais (ADRs)

| ADR | Decisão | Status |
|---|---|---|
| [0001](../adrs/0001-estrategia-nuvem.md) | PaaS de contêineres + escala horizontal | Aceito |
| [0002](../adrs/0002-padrao-resiliencia.md) | API Gateway + Circuit Breaker + Bulkhead | Aceito |
| [0003](../adrs/0003-modelo-comunicacao.md) | Comunicação híbrida (síncrono + assíncrono) | Aceito |

---

## 12. Atributos de Qualidade

| Atributo | Cenário | Tática aplicada |
|---|---|---|
| Escalabilidade | Pico de escrita de ADRs | Réplicas horizontais do decisions-service |
| Disponibilidade | Notification-service cai | Aprovação segue via fila (desacoplamento) |
| Resiliência | Catálogo lento | Timeout + circuit breaker (fail-fast) |
| Manutenibilidade | Novo reagente a "aprovação" | Novo consumidor sem alterar o produtor |
| Desempenho | Latência interativa | Caminho síncrono curto; efeitos fora do caminho crítico |

---

## 13. Riscos e Dívida Técnica

| Item | Risco | Mitigação prevista |
|---|---|---|
| Evento perdido | Publish falha após commit | Padrão *Transactional Outbox* |
| Gateway como SPOF | Indisponibilidade total | Múltiplas réplicas atrás do LB |
| Autenticação mockada | Não pronta para produção | Integração OIDC real |
| Migrações de schema | `create_all` no startup | Adotar Alembic |
| Sem tracing distribuído | Difícil depurar fluxos async | OpenTelemetry (ver gold-plating) |

---

## 14. Glossário

| Termo | Definição |
|---|---|
| **ADR** | Architecture Decision Record — registro de uma decisão arquitetural |
| **SAD** | Software Architecture Document — este documento |
| **Circuit Breaker** | Disjuntor que interrompe chamadas a um serviço em falha |
| **Bulkhead** | Antepara: isola recursos para conter falhas |
| **Database-per-service** | Cada microsserviço é dono do próprio banco |
| **At-least-once** | Garantia de entrega: a mensagem chega ao menos uma vez |
| **PaaS** | Platform as a Service (NIST SP 800-145) |
