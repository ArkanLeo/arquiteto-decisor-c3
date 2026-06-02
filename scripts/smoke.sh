#!/usr/bin/env bash
# Teste de fumaça end-to-end via gateway. Requer a malha no ar (`make up`).
set -euo pipefail

GW="${GATEWAY_URL:-http://localhost:8080}"

echo "▶ 1) Cadastrando um sistema no catálogo..."
SYS=$(curl -sf -X POST "$GW/api/systems" \
  -H 'content-type: application/json' \
  -d '{"name":"checkout","team":"Payments","description":"Fluxo de pagamento"}')
echo "  $SYS"
SYS_ID=$(echo "$SYS" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

echo "▶ 2) Registrando uma decisão (ADR) para o sistema..."
DEC=$(curl -sf -X POST "$GW/api/decisions" \
  -H 'content-type: application/json' \
  -d "{\"system_id\":\"$SYS_ID\",\"title\":\"Adotar Circuit Breaker\",\"decision\":\"Sim, via pybreaker\"}")
echo "  $DEC"
DEC_ID=$(echo "$DEC" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

echo "▶ 3) Aprovando a decisão (dispara evento assíncrono)..."
curl -sf -X POST "$GW/api/decisions/$DEC_ID/approve" | python3 -m json.tool

echo "✓ Fluxo completo. Veja o log do notification-service para a notificação."
