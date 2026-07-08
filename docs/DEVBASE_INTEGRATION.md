# Integração com o DevBase 4.1.0

O DevBase usa a chave administrativa do PingWake apenas em memória, carregada pelo arquivo `.env` local.

Endpoint otimizado:

```http
GET /api/v1/integrations/devbase/targets/{target_id}
X-PingWake-Key: PINGWAKE_API_KEY
```

A resposta reúne:

- estado atual do target;
- última e próxima verificação;
- latência e status HTTP do último check;
- contadores de falha e sucesso;
- existência e início de incidente aberto.

Não há criação, edição ou exclusão de targets por esse endpoint.
