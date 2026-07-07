# Cadastro no DevBase — PingWake

## Dados gerais

- **Nome:** PingWake
- **Tipo:** API / Backend
- **Modelo:** Personalizado
- **Finalidade:** Uso pessoal + Portfólio
- **Status:** Em desenvolvimento
- **Prioridade:** Alta
- **Fase atual:** MVP funcional inicial
- **Horas registradas:** preencher conforme execução
- **Próxima ação:** criar o banco PostgreSQL no Neon, preencher o `.env`, executar as migrations e validar o CRUD no Swagger
- **Bloqueio atual:** banco Neon e deploy ainda não configurados

## Objetivo

Monitorar periodicamente APIs, sites e bancos de dados, manter serviços selecionados
ativos, registrar latência e histórico de disponibilidade e gerenciar incidentes.

## Regras importantes

- Backend e banco são serviços independentes;
- destinos ficam no banco, nunca hardcoded;
- toda chamada possui timeout;
- três falhas consecutivas abrem incidente;
- dois sucessos consecutivos resolvem incidente;
- segredos ficam somente em variáveis de ambiente;
- o endpoint do Cron é protegido por uma chave própria;
- redes privadas são bloqueadas por padrão;
- respostas completas dos alvos não são armazenadas;
- o PingWake funciona sem depender do DevBase.

## Problemas conhecidos

- APIs antigas podem não possuir `/health/live` e `/health/ready`;
- banco Neon ainda precisa ser criado;
- backend ainda precisa ser publicado;
- Cron externo ainda precisa ser escolhido e configurado;
- integração com o DevBase pertence a uma fase posterior.

## Estrutura técnica

### Backend / API

- Python 3.12;
- FastAPI;
- Uvicorn;
- HTTPX assíncrono;
- Pydantic Settings.

### Banco

- PostgreSQL;
- Neon como provedor recomendado;
- SQLAlchemy assíncrono;
- asyncpg;
- Alembic.

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
- status: desenvolvimento;
- repositório: `pingwake`;
- health check: `/health/live` e `/health/ready`;
- deploy: pendente.

### Banco PingWake

- Categoria: Banco de dados;
- tecnologia: PostgreSQL;
- provedor: Neon;
- status: pendente de criação;
- migrations: Alembic.

### Cron externo

- Categoria: Automação / Agendamento;
- função: chamar `POST /internal/checks/run-due`;
- status: pendente de definição.
