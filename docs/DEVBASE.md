# Cadastro no DevBase — PingWake

## Dados gerais

- **Nome:** PingWake
- **Tipo:** API / Backend
- **Modelo:** Personalizado
- **Finalidade:** Uso pessoal + Portfólio
- **Status:** Em desenvolvimento
- **Prioridade:** Alta
- **Fase atual:** MVP publicado, automatizado e com notificações
- **Horas registradas:** preencher conforme execução
- **Próxima ação:** validar abertura e resolução de incidente com alerta no Discord
- **Bloqueio atual:** nenhum

## Objetivo

Monitorar periodicamente APIs, sites e bancos de dados, manter serviços selecionados
ativos, registrar latência e histórico de disponibilidade, gerenciar incidentes e avisar
quando um serviço fica indisponível ou se recupera.

## Regras importantes

- Backend e banco são serviços independentes;
- destinos ficam no banco, nunca hardcoded;
- toda chamada possui timeout;
- três falhas consecutivas abrem incidente;
- dois sucessos consecutivos resolvem incidente;
- alertas são enviados somente na abertura e na resolução;
- falha no Discord não interrompe o monitoramento;
- segredos ficam somente em variáveis de ambiente;
- o endpoint do Cron é protegido por uma chave própria;
- redes privadas são bloqueadas por padrão;
- respostas completas dos alvos não são armazenadas;
- o PingWake funciona sem depender do DevBase.

## Problemas conhecidos

- APIs antigas podem não possuir `/health/live` e `/health/ready`;
- monitor específico de atividade de banco ainda não foi implementado;
- integração visual com o DevBase pertence a uma fase posterior.

## Estrutura técnica

### Backend / API

- Python 3.12;
- FastAPI;
- Uvicorn;
- HTTPX assíncrono;
- Pydantic Settings;
- deploy no Render.

### Banco

- PostgreSQL;
- Neon;
- SQLAlchemy assíncrono;
- asyncpg;
- Alembic.

### Automação e notificações

- cron-job.org chamando `POST /internal/checks/run-due`;
- webhook do Discord;
- logs em `notification_events`.

### Qualidade e infraestrutura

- Pytest;
- Ruff;
- Mypy;
- Docker;
- GitHub Actions.

## Serviços

### Backend PingWake

- Categoria: Backend / API;
- tecnologia: Python + FastAPI;
- status: publicado;
- repositório: `PingWake`;
- health check: `/health/live` e `/health/ready`;
- deploy: Render.

### Banco PingWake

- Categoria: Banco de dados;
- tecnologia: PostgreSQL;
- provedor: Neon;
- status: ativo;
- migrations: Alembic.

### Cron externo

- Categoria: Automação / Agendamento;
- serviço: cron-job.org;
- função: chamar `POST /internal/checks/run-due`;
- status: ativo.

### Alertas

- Categoria: Integração / Notificação;
- serviço: Discord Webhook;
- eventos: incidente aberto e incidente resolvido;
- status: em validação.
