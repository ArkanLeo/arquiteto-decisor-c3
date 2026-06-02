# Pipeline de Integração Contínua

O repositório possui um pipeline real em
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml), executado a cada push
e pull request.

## Etapas

1. **Matriz por serviço** — roda em paralelo para `api-gateway`,
   `decisions-service`, `catalog-service` e `notification-service`:
   - instala as dependências do serviço;
   - **lint** com `ruff`;
   - **testes** com `pytest` (usam SQLite local / dublês, sem infraestrutura).
2. **Validação do compose** — `docker compose config -q` garante que o
   `docker-compose.yml` é válido.

## Por que isso importa

- **Qualidade contínua:** nenhum serviço entra na branch sem passar lint+testes.
- **Isolamento:** a matriz reflete a independência dos microsserviços — cada um
  é validado por conta própria, como seria implantado.
- **Feedback rápido:** falhas aparecem por serviço, facilitando o diagnóstico.

## Evolução prevista

- Build e push das imagens Docker para um registry.
- Testes de integração subindo a malha completa via `docker compose`.
- Análise de cobertura e *security scanning* (ex.: `pip-audit`).
