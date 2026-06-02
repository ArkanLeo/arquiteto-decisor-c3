# ADR 0003 — Modelo de Comunicação

- **Status:** aceito
- **Data:** 2026-06-02
- **Decisores:** Equipe Arquiteto Decisor
- **Contexto técnico:** Ciclo 3 (Fase Cloud) — integração entre microsserviços

## Contexto e Problema

Com a malha de serviços, surge a pergunta de como eles conversam. Há duas
naturezas de interação no Arquiteto Decisor:

1. **Comandos/consultas interativos** que o usuário espera ver respondidos
   imediatamente (criar uma decisão, listar ADRs, validar um sistema).
2. **Efeitos colaterais** disparados por um fato de negócio (uma decisão foi
   aprovada → notificar o time, futuramente registrar auditoria, atualizar
   métricas) — onde o solicitante não precisa do resultado para prosseguir.

**Pergunta de decisão:** usar comunicação **síncrona** (request/response) ou
**assíncrona** (mensageria/eventos) entre os serviços — e como balancear os
trade-offs de acoplamento, consistência e resiliência?

## Drivers da Decisão

- **Experiência do usuário** — operações interativas exigem resposta imediata e
  consistência de leitura.
- **Desacoplamento** — adicionar novos reagentes a um fato (ex.: auditoria) sem
  alterar quem produziu o fato.
- **Resiliência** — um consumidor lento/fora do ar não pode travar a operação
  principal.
- **Simplicidade** — não introduzir mensageria onde uma chamada direta resolve.

## Opções Consideradas

1. **100% síncrono (REST/HTTP everywhere).**
2. **100% assíncrono (todo fluxo via mensageria).**
3. **Híbrido** — síncrono para comandos/consultas; assíncrono (event-driven)
   para efeitos colaterais.

## Decisão

Escolhemos a **Opção 3 — modelo híbrido**, aplicando o princípio de usar a
ferramenta certa para cada interação (Newman, 2021).

- **Síncrono (REST/JSON)** para o que exige resposta imediata: cliente →
  `api-gateway` → serviços, e a validação `decisions-service` →
  `catalog-service` (ver `catalog_client.py`). Toda chamada síncrona é protegida
  por timeout e circuit breaker (ADR 0002), contendo o acoplamento temporal.
- **Assíncrono (event-driven, AMQP/RabbitMQ)** para efeitos colaterais: ao
  aceitar uma decisão, o `decisions-service` **publica** o evento de domínio
  `decision.approved` num *topic exchange* e segue adiante; o
  `notification-service` **consome** e reage de forma independente (ver
  `events.py` e `consumer.py`). Publicador e consumidor se conhecem apenas pelo
  **contrato do evento** — o estilo *publish/subscribe* de Hohpe & Woolf (2003).

A mensagem é durável e o consumo usa *ack* manual (entrega *at-least-once*),
priorizando disponibilidade e tolerância a falhas em detrimento de consistência
imediata — uma escolha consciente alinhada à consistência eventual (Kleppmann,
2017).

## Consequências

**Positivas**
- Operações interativas permanecem simples e consistentes (síncrono).
- O fluxo de aprovação não depende da disponibilidade do `notification-service`:
  resiliência e desacoplamento temporal (assíncrono).
- Novos consumidores do evento podem ser adicionados sem tocar no produtor
  (extensibilidade).
- Absorção de picos: a fila funciona como amortecedor de carga.

**Negativas / Custos**
- O broker (RabbitMQ) é nova peça de infraestrutura a operar e monitorar.
- Consistência eventual: a notificação não é instantânea nem transacional com a
  aprovação; sem cuidado, há risco de "evento perdido" se o publish falhar após
  o commit.
- Depuração de fluxos assíncronos é mais difícil (exige *correlation id* e
  tracing distribuído — ver `gold-plating/observability.md`).

## Alternativas Rejeitadas

- **100% síncrono (Opção 1):** rejeitada porque encadear chamadas para efeitos
  colaterais cria **acoplamento temporal** e propaga falhas — se o serviço de
  notificação cai, a aprovação falharia sem necessidade. Aumenta também a
  latência percebida (soma das chamadas) e o risco de cascata (Richardson,
  2018).
- **100% assíncrono (Opção 2):** rejeitada por **complexidade desproporcional**.
  Modelar consultas interativas (listar ADRs) como mensagens introduz
  consistência eventual onde o usuário espera leitura imediata, exigindo
  correlação de respostas e tornando o sistema mais difícil de entender (Newman,
  2021).

## Trade-offs Mapeados

| Critério | Híbrido (escolhida) | 100% síncrono | 100% assíncrono |
|---|---|---|---|
| Latência interativa | Baixa | Baixa→média (encadeada) | Alta (correlação) |
| Acoplamento temporal | Baixo (nos efeitos) | Alto | Muito baixo |
| Consistência | Forte onde importa | Forte | Eventual em tudo |
| Resiliência a falha de consumidor | Alta | Baixa | Alta |
| Complexidade | Média | Baixa | Alta |

## Referências

- Hohpe, G. & Woolf, B. *Enterprise Integration Patterns*, Addison-Wesley, 2003.
- Richardson, C. *Microservices Patterns*, Manning, 2018.
- Newman, S. *Building Microservices*, 2ª ed., O'Reilly, 2021.
- Kleppmann, M. *Designing Data-Intensive Applications*, O'Reilly, 2017.
- Fowler, M. *What do you mean by "Event-Driven"?* (martinfowler.com), 2017.
