# ADR 0002 — Padrões de Resiliência

- **Status:** aceito
- **Data:** 2026-06-02
- **Decisores:** Equipe Arquiteto Decisor
- **Contexto técnico:** Ciclo 3 (Fase Cloud) — comunicação entre microsserviços

## Contexto e Problema

Ao quebrar o monólito em serviços, uma chamada do usuário passa a atravessar a
rede e a depender de vários processos. A rede é, por natureza, não confiável
(Deutsch, *Fallacies of Distributed Computing*, 1994). Sem cuidado, a falha de
um serviço lento se propaga: chamadas se acumulam, *threads/conexões* esgotam e
a indisponibilidade de um componente derruba todo o sistema — a clássica **falha
em cascata** (Nygard, 2018).

**Pergunta de decisão:** quais padrões de resiliência adotar para que falhas
parciais (um serviço lento ou fora do ar) sejam contidas, sem comprometer a
disponibilidade do conjunto, e como expor uma fronteira única e protegida ao
cliente?

## Drivers da Decisão

- **Isolamento de falhas** — a falha de um serviço não pode esgotar os recursos
  dos demais nem do cliente.
- **Fail-fast** — diante de um upstream em colapso, responder rápido é melhor do
  que travar esperando timeout.
- **Fronteira única** — clientes não devem conhecer a topologia interna nem
  lidar com autenticação/limites em cada serviço.
- **Recuperação automática** — o sistema deve voltar ao normal sozinho quando o
  serviço se restabelecer.

## Opções Consideradas

1. **Acesso direto cliente→serviços, sem padrões** — cada cliente chama cada
   serviço diretamente e trata erros por conta própria.
2. **API Gateway + Circuit Breaker + Bulkhead (+ Timeout/Retry)** — uma borda
   única aplicando os padrões de estabilidade.
3. **Service mesh (sidecar, ex.: Istio/Linkerd)** — resiliência delegada à
   infraestrutura de rede via sidecars.

## Decisão

Escolhemos a **Opção 2**: um **API Gateway** como ponto único de entrada,
combinando **Circuit Breaker**, **Bulkhead**, **Timeout** e **Retry** prudente.

- **API Gateway** (Richardson, 2018; Newman, 2021): centraliza roteamento, rate
  limiting, autenticação e *cross-cutting concerns*, desacoplando o cliente da
  topologia interna. Implementado em `src/api-gateway`.
- **Circuit Breaker** (Nygard, 2018; Fowler, 2014): cada upstream tem um
  disjuntor (`pybreaker`) que **abre** após N falhas consecutivas, passando a
  responder de imediato (fail-fast) e poupando o serviço em colapso; após um
  *reset timeout* entra em **half-open** para testar a recuperação. Ver
  `app/main.py` (`_breakers`).
- **Bulkhead** (Nygard, 2018): um disjuntor por upstream isola os recursos —
  problemas no `decisions-service` não consomem a capacidade reservada ao
  `catalog-service`. No consumidor assíncrono, o `prefetch_count` (QoS) limita
  mensagens em voo, outra forma de antepara.
- **Timeout** explícito em toda chamada de saída (gateway e
  `catalog_client.py`): nenhuma chamada bloqueia indefinidamente.

## Consequências

**Positivas**
- Falhas parciais ficam contidas; o sistema degrada de forma graciosa em vez de
  colapsar.
- O disjuntor protege o serviço em recuperação de uma "tempestade de retries".
- O gateway simplifica os clientes e concentra políticas de segurança e limite.
- Recuperação automática via estado *half-open*.

**Negativas / Custos**
- O gateway é um ponto crítico: precisa ser replicado (escala horizontal, ADR
  0001) para não virar *single point of failure*.
- Ajustar limiares (`fail_max`, `reset_timeout`, timeouts) exige observação e
  pode causar aberturas indevidas se mal calibrado.
- Retry precisa ser idempotente e com *backoff*, sob risco de amplificar carga.

## Alternativas Rejeitadas

- **Acesso direto sem padrões (Opção 1):** rejeitada por empurrar resiliência,
  segurança e limites para cada cliente e por permitir falhas em cascata — o
  cenário que Nygard (2018) descreve como causa típica de queda total.
- **Service mesh (Opção 3):** poderosa, mas rejeitada por **excesso de
  complexidade operacional** para a escala atual. Um mesh adiciona sidecars,
  *control plane* e curva de aprendizado desproporcionais a quatro serviços
  (Newman, 2021, alerta contra adotar mesh cedo demais). Permanece como evolução
  natural caso a malha cresça.

## Trade-offs Mapeados

| Critério | Gateway + CB/Bulkhead (escolhida) | Acesso direto | Service mesh |
|---|---|---|---|
| Contenção de falhas | Alta | Baixa | Alta |
| Complexidade operacional | Média | Baixa | Alta |
| Acoplamento do cliente | Baixo | Alto | Baixo |
| Ponto único de falha | Gateway (mitigável) | Não há | Control plane |
| Esforço de implementação | Médio | Baixo | Alto |

## Referências

- Nygard, M. *Release It!*, 2ª ed., Pragmatic Bookshelf, 2018 (Circuit Breaker, Bulkhead, Timeout).
- Fowler, M. *CircuitBreaker* (martinfowler.com), 2014.
- Richardson, C. *Microservices Patterns*, Manning, 2018 (API Gateway).
- Newman, S. *Building Microservices*, 2ª ed., O'Reilly, 2021.
- Deutsch, P. *The Eight Fallacies of Distributed Computing*, 1994.
- Resilience4j / Netflix Hystrix — implementações de referência dos padrões.
