# ADR 0001 — Estratégia de Nuvem e Escalabilidade

- **Status:** aceito
- **Data:** 2026-06-02
- **Decisores:** Equipe Arquiteto Decisor
- **Contexto técnico:** Ciclo 3 (Fase Cloud) — migração do monólito para malha de microsserviços

## Contexto e Problema

Nas Fases 1 e 2 o Arquiteto Decisor era um monólito FastAPI implantado em um
único servidor. Com a evolução para multi-tenant, a carga deixou de ser
uniforme: o `decisions-service` (escrita/consulta de ADRs) recebe muito mais
tráfego do que o `catalog-service`, e picos ocorrem em horários de revisão
arquitetural. Escalar o monólito inteiro para atender um só componente é
desperdício de recurso e de custo.

**Pergunta de decisão:** qual modelo de serviço de nuvem (IaaS, PaaS, SaaS ou
Serverless/FaaS) e qual estratégia de escalabilidade (vertical vs. horizontal)
adotar para que cada serviço escale de forma independente, com bom custo-
benefício e baixo esforço operacional para uma equipe pequena?

## Drivers da Decisão

- **Escalabilidade independente por serviço** — escalar o `decisions-service`
  sem arrastar os demais.
- **Esforço operacional baixo** — a equipe é pequena e acadêmica; não há SRE
  dedicado para gerenciar VMs, patches e clusters.
- **Custo elástico** — pagar próximo ao uso real, com capacidade de reduzir a
  zero/quase-zero em ociosidade.
- **Portabilidade** — evitar acoplamento forte a um único provedor (lock-in).
- **Previsibilidade de latência** — a API é interativa; latência de cauda
  importa.

## Opções Consideradas

1. **IaaS + escalabilidade vertical** — VMs (ex.: EC2/Compute Engine)
   gerenciadas pela equipe, crescendo a máquina conforme a carga.
2. **PaaS de contêineres + escalabilidade horizontal** — empacotar cada serviço
   em contêiner e rodar em orquestração gerenciada (ex.: Cloud Run, AWS
   ECS/Fargate, Azure Container Apps), replicando instâncias sob demanda.
3. **Serverless / FaaS puro** — cada endpoint como função (ex.: AWS Lambda),
   escalando por invocação.

## Decisão

Escolhemos a **Opção 2 — PaaS de contêineres com escalabilidade horizontal**.

Cada microsserviço é empacotado em uma imagem OCI (ver `Dockerfile`s em
`/src`) e implantado em uma plataforma gerenciada de contêineres com
*autoscaling* horizontal por métrica (CPU/RPS). O estado fica fora da camada de
cômputo (Postgres gerenciado por serviço, RabbitMQ gerenciado, Redis), tornando
as instâncias **stateless** e descartáveis — pré-requisito para escalar
horizontalmente conforme os *Twelve-Factor App* (Wiggins, 2011) e o conceito de
"gado, não bichos de estimação" de Newman (2021).

A escalabilidade **horizontal** (mais réplicas) é preferida à **vertical**
(máquinas maiores) porque oferece tolerância a falhas (várias instâncias) e não
esbarra no teto físico de uma única máquina (Bass, Clements & Kazman, 2021,
sobre o tático *"manter múltiplas cópias da computação"*).

Os modelos de nuvem seguem as definições do **NIST SP 800-145** (Mell & Grance,
2011): adotamos **PaaS** para o cômputo e **SaaS** gerenciado para os recursos de
estado (banco, broker), reservando **IaaS** apenas onde houver necessidade
específica — que hoje não existe.

## Consequências

**Positivas**
- Escala fina por serviço; o `decisions-service` replica sem afetar os demais.
- Instâncias stateless permitem *rolling deploys* e recuperação automática.
- Imagens OCI dão portabilidade entre provedores, mitigando lock-in.
- Operação enxuta: a plataforma cuida de orquestração, health checks e scaling.

**Negativas / Custos**
- Introduz a complexidade de empacotamento, registry de imagens e configuração
  de autoscaling.
- Estado externalizado exige cuidado com conexões (pooling) e latência de rede.
- Custo de manter um piso mínimo de réplicas para evitar latência de cold start.

## Alternativas Rejeitadas

- **IaaS + vertical (Opção 1):** rejeitada pelo alto esforço operacional
  (patches, hardening, monitoração de SO) e pelo teto de escala de uma única
  máquina. Escalonar verticalmente também implica *downtime* ou migração para
  troca de instância, ferindo a disponibilidade (Bass, Clements & Kazman, 2021).
- **Serverless/FaaS puro (Opção 3):** atraente no custo-ocioso, mas rejeitada
  como base do núcleo por três trade-offs: (a) **cold start** prejudica a
  latência de cauda de uma API interativa; (b) o **lock-in** a um runtime
  proprietário reduz portabilidade; (c) conexões persistentes a banco/broker e
  o modelo de consumo AMQP do `notification-service` se encaixam mal no modelo
  efêmero de funções (Richardson, 2018; Roberts & Chapin, 2017). FaaS
  permanece como candidato para tarefas event-driven pontuais no futuro.

## Trade-offs Mapeados

| Critério | PaaS contêiner (escolhida) | IaaS + vertical | Serverless/FaaS |
|---|---|---|---|
| Esforço operacional | Baixo | Alto | Muito baixo |
| Escala independente | Alta (por serviço) | Baixa | Alta (por função) |
| Latência de cauda | Previsível | Previsível | Sujeita a cold start |
| Lock-in | Baixo (OCI) | Baixo | Alto |
| Custo em ociosidade | Médio (piso de réplicas) | Alto | Muito baixo |

## Referências

- Mell, P. & Grance, T. *The NIST Definition of Cloud Computing* (SP 800-145), 2011.
- Newman, S. *Building Microservices*, 2ª ed., O'Reilly, 2021.
- Richardson, C. *Microservices Patterns*, Manning, 2018.
- Bass, L., Clements, P. & Kazman, R. *Software Architecture in Practice*, 4ª ed., 2021.
- Burns, B. *Designing Distributed Systems*, O'Reilly, 2018.
- Wiggins, A. *The Twelve-Factor App*, 2011.
- Roberts, M. & Chapin, J. *What Is Serverless?*, O'Reilly, 2017.
