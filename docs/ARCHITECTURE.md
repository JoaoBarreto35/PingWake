# Arquitetura do PingWake

## Princípios

1. O PingWake é independente do DevBase.
2. Configuração e lógica permanecem separadas.
3. Destinos monitorados são persistidos no PostgreSQL.
4. Toda execução relevante deixa um registro auditável.
5. Falhas isoladas não geram incidentes imediatamente.
6. O executor limita concorrência para não sobrecarregar o serviço.
7. O monitor não acessa redes privadas por padrão.

## Fluxo

```text
Cron -> autenticação -> busca de destinos vencidos -> checks concorrentes
     -> check_runs -> atualização do alvo -> abertura/resolução de incidente
```

## Entidades

### monitoring_targets

Configuração e estado agregado de cada destino.

### check_runs

Registro imutável de cada tentativa de verificação.

### incidents

Períodos consolidados de indisponibilidade.

## Integração futura com o DevBase

O DevBase consumirá a API do PingWake para cadastrar destinos e consultar resumo,
histórico e incidentes. Não haverá acesso direto ao banco local do DevBase.
