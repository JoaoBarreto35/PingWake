# Cadastro no DevBase — PingWake

## Dados gerais

- **Nome:** PingWake
- **Tipo:** API / Backend
- **Modelo:** Personalizado
- **Finalidade:** Uso pessoal + Portfólio
- **Status:** Em desenvolvimento
- **Prioridade:** Alta
- **Fase atual:** MVP publicado, automatizado, com notificações e requests autenticados
- **Horas registradas:** preencher conforme execução
- **Próxima ação:** cadastrar e validar os projetos Supabase por RPC
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
- segredos globais ficam somente em variáveis de ambiente;
- headers e bodies dos targets ficam criptografados no PostgreSQL;
- o endpoint do Cron é protegido por uma chave própria;
- redes privadas são bloqueadas por padrão;
- respostas completas dos alvos não são armazenadas;
- o PingWake funciona sem depender do DevBase.

## Problemas conhecidos

- APIs antigas podem não possuir `/health/live` e `/health/ready`;
- APIs antigas podem exigir criação de uma função RPC ou endpoint de health;
- o formulário atual do DevBase ainda não edita headers e body secretos.

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

### Monitoramento Supabase

- Categoria: Banco de dados / API;
- método: RPC pela Data API;
- autenticação: publishable key no header `apikey`;
- armazenamento: header e body criptografados;
- status: implementado.

### Alertas

- Categoria: Integração / Notificação;
- serviço: Discord Webhook;
- eventos: incidente aberto e incidente resolvido;
- status: em validação.


## Integração implementada

O DevBase 4.1.0 consulta:

```http
GET /api/v1/integrations/devbase/targets/{target_id}
```

O endpoint usa `X-PingWake-Key`, é somente leitura e retorna o estado atual, o último check e o incidente aberto em uma única chamada.
