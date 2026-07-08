# Arquitetura do PingWake

## Princípios

1. O PingWake é independente do DevBase.
2. Configuração e lógica permanecem separadas.
3. Destinos monitorados são persistidos no PostgreSQL.
4. Toda execução relevante deixa um registro auditável.
5. Falhas isoladas não geram incidentes imediatamente.
6. O executor limita concorrência para não sobrecarregar o serviço.
7. O monitor não acessa redes privadas por padrão.
8. Credenciais de targets são criptografadas antes da persistência.
9. Segredos são descriptografados somente durante a montagem do request.

## Fluxo

```text
Cron -> autenticação -> busca de destinos vencidos -> checks concorrentes
     -> descriptografia em memória -> request HTTP -> check_runs
     -> atualização do alvo -> abertura/resolução de incidente
```

## Entidades

### monitoring_targets

Configuração e estado agregado de cada destino. Headers e body opcionais são armazenados em colunas criptografadas; a API expõe apenas indicadores booleanos.

### check_runs

Registro imutável de cada tentativa de verificação.

### incidents

Períodos consolidados de indisponibilidade.

## Integração com o DevBase

O DevBase consome a API do PingWake para cadastrar destinos e consultar o resumo de status. Não há acesso direto entre os bancos. A versão atual do DevBase ainda não edita headers ou body secretos; essa configuração pode ser feita pelo Swagger do PingWake.
