# Atualização para PingWake 0.5.0

A versão 0.5.0 adiciona confiabilidade operacional sem exigir recadastro dos targets.

## Variáveis recomendadas

```env
APP_VERSION=0.5.0
DEFAULT_DEGRADED_LATENCY_MS=5000
STALE_AFTER_MULTIPLIER=2.5
CRON_EXPECTED_INTERVAL_MINUTES=5
CRON_STALE_AFTER_MULTIPLIER=3.0
NOTIFICATION_MAX_ATTEMPTS=4
NOTIFICATION_RETRY_DELAYS_SECONDS=60,300,900
CHECK_RETENTION_DAYS=90
NOTIFICATION_RETENTION_DAYS=365
SCHEDULER_RUN_RETENTION_DAYS=90
```

As variáveis existentes, principalmente `DATABASE_URL`, `PINGWAKE_API_KEY`,
`PINGWAKE_CRON_KEY`, `PINGWAKE_ENCRYPTION_KEY` e `DISCORD_WEBHOOK_URL`, devem ser
preservadas.

## Deploy

```powershell
git add .
git commit -m "feat: add monitoring reliability layer"
git push
```

O container executa `alembic upgrade head` e aplica a migration `20260708_0004`.
