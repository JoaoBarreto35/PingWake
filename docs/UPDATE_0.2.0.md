# Atualização 0.2.0 — Notificações no Discord

## O que esta versão adiciona

- alerta no Discord quando um incidente é aberto;
- alerta no Discord quando um incidente é resolvido;
- tabela `notification_events`;
- endpoint `GET /api/v1/notifications`;
- migration `20260707_0002`;
- migrations automáticas antes da inicialização do container no Render.

## Variáveis de ambiente

Mantenha no `.env` local e no Render:

```env
NOTIFICATIONS_ENABLED=true
DISCORD_WEBHOOK_URL=SUA_URL_SECRETA_DO_WEBHOOK
NOTIFICATION_TIMEOUT_SECONDS=10
APP_VERSION=0.2.0
```

Nunca envie a URL do webhook ao GitHub.

## Publicação

Depois de substituir os arquivos:

```powershell
git add .
git commit -m "feat: add Discord incident notifications"
git push
```

O Render deve iniciar um novo deploy. O `Dockerfile` executa automaticamente:

```text
alembic upgrade head
```

antes de iniciar o Uvicorn. A tabela nova será criada no Neon sem apagar dados existentes.

## Teste seguro de abertura

Cadastre um alvo temporário apontando para:

```text
https://pingwake.onrender.com/health/live
```

mas use:

```json
{
  "expected_status_code": 418
}
```

Execute o check manual três vezes. Na terceira falha o PingWake deve:

1. abrir o incidente;
2. enviar a mensagem vermelha ao Discord;
3. gravar um evento `incident_opened` com status `sent`.

## Teste seguro de recuperação

Atualize o alvo para:

```json
{
  "expected_status_code": 200
}
```

Execute o check manual duas vezes. No segundo sucesso o PingWake deve:

1. resolver o incidente;
2. enviar a mensagem verde ao Discord;
3. gravar um evento `incident_resolved` com status `sent`.

Consulte os registros em:

```http
GET /api/v1/notifications
```

Depois do teste, desative o alvo temporário em vez de excluí-lo caso queira preservar o
histórico do incidente e das notificações.
