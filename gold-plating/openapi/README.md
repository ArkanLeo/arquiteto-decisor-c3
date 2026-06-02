# Contratos OpenAPI

Cada microsserviço FastAPI gera automaticamente sua especificação **OpenAPI 3.1**
e uma UI Swagger:

| Serviço | Spec | UI |
|---|---|---|
| api-gateway | `http://localhost:8080/openapi.json` | `http://localhost:8080/docs` |
| decisions-service | `http://localhost:8002/openapi.json` | `.../docs` |
| catalog-service | `http://localhost:8001/openapi.json` | `.../docs` |
| notification-service | `http://localhost:8003/openapi.json` | `.../docs` |

> Em produção apenas o gateway é exposto; as portas internas acima referem-se ao
> ambiente de desenvolvimento.

## Exportar os contratos

Com a malha no ar, é possível materializar os contratos para versionamento ou
geração de SDKs de cliente:

```bash
curl -s http://localhost:8080/openapi.json -o gold-plating/openapi/api-gateway.json
```

## Por que isso agrega

- **Contrato como fonte da verdade:** consumidores podem gerar clientes tipados.
- **Governança de API:** mudanças incompatíveis ficam visíveis no diff do JSON.
- **Documentação viva:** a UI Swagger acompanha o código sem esforço manual.
