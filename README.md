# PingWake

Serviço pessoal de monitoramento e keep-alive para APIs, sites e bancos de dados,
desenvolvido com Python, FastAPI e PostgreSQL.

O PingWake é executado por um Cron externo, verifica os destinos pendentes, mede a
latência, registra o histórico e gerencia incidentes automaticamente. O projeto não
possui frontend no MVP: o Swagger funciona como interface administrativa e, no futuro,
o DevBase será integrado por API.

## Estado atual

**Versão:** 0.1.0  
**Fase:** MVP funcional inicial  
**Banco recomendado:** Neon PostgreSQL  
**Frontend:** não necessário no MVP

## Funcionalidades implementadas

- Health check do próprio PingWake (`live` e `ready`);
- CRUD de destinos monitorados;
- execução manual de um health check;
- execução em lote dos destinos pendentes;
- cliente HTTP assíncrono com timeout;
- medição de latência;
- persistência do histórico;
- abertura de incidente após falhas consecutivas;
- resolução automática após recuperações consecutivas;
- bloqueio de redes privadas e locais para reduzir risco de SSRF;
- chaves separadas para administração e Cron;
- migrations com Alembic;
- Docker e Docker Compose;
- testes e CI no GitHub.

## Arquitetura

```text
Cron externo
    |
    v
PingWake /internal/checks/run-due
    |
    +--> monitoring_targets
    +--> HTTP checks concorrentes
    +--> check_runs
    +--> incidents
    |
    v
Neon PostgreSQL
```

## Requisitos

- Python 3.12 ou superior;
- PostgreSQL 15 ou superior, ou uma conta Neon;
- Git;
- Docker opcional.

## Configuração local

### 1. Crie e ative o ambiente virtual

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. Instale as dependências

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Configure as variáveis

Copie `.env.example` para `.env` e informe a conexão do banco e duas chaves diferentes.

```bash
cp .env.example .env
```

No Windows:

```powershell
Copy-Item .env.example .env
```

O Neon fornece normalmente uma URL iniciada por `postgresql://`. O PingWake adapta
automaticamente a URL para o driver assíncrono e remove o parâmetro `channel_binding`,
que não é utilizado pelo `asyncpg`.

### 4. Execute as migrations

```bash
alembic upgrade head
```

### 5. Inicie a API

```bash
uvicorn app.main:app --reload
```

Acesse:

- Swagger: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health/live`
- Readiness: `http://localhost:8000/health/ready`

## Uso da API

Os endpoints administrativos exigem o header:

```http
X-PingWake-Key: sua-chave-administrativa
```

O endpoint do Cron exige:

```http
X-PingWake-Cron-Key: sua-chave-do-cron
```

### Criar um destino

```bash
curl -X POST "http://localhost:8000/api/v1/targets" \
  -H "Content-Type: application/json" \
  -H "X-PingWake-Key: sua-chave-administrativa" \
  -d '{
    "name": "Minha API",
    "description": "API de exemplo",
    "project_name": "Projeto exemplo",
    "target_type": "api",
    "monitoring_mode": "monitor",
    "environment": "production",
    "provider": "Render",
    "url": "https://api.exemplo.com/health/ready",
    "http_method": "GET",
    "expected_status_code": 200,
    "interval_minutes": 30,
    "timeout_seconds": 10,
    "enabled": true
  }'
```

### Executar um destino manualmente

```bash
curl -X POST "http://localhost:8000/api/v1/targets/ID/check" \
  -H "X-PingWake-Key: sua-chave-administrativa"
```

### Executar destinos pendentes pelo Cron

```bash
curl -X POST "http://localhost:8000/internal/checks/run-due" \
  -H "X-PingWake-Cron-Key: sua-chave-do-cron"
```

## Política inicial de incidentes

- 3 falhas consecutivas: abre incidente;
- 2 sucessos consecutivos: resolve incidente;
- os limites são configuráveis por variáveis de ambiente.

## Segurança

- Não publique o arquivo `.env`;
- use chaves diferentes para administração e Cron;
- HTTPS é recomendado em produção;
- redes privadas, loopback, link-local e endereços reservados são bloqueados por padrão;
- redirecionamentos HTTP não são seguidos;
- corpos das respostas monitoradas não são persistidos;
- habilite `ALLOW_PRIVATE_TARGETS=true` apenas em ambiente controlado.

## Desenvolvimento

```bash
ruff check .
ruff format .
mypy app
pytest --cov=app
```

## Docker

Para subir API e PostgreSQL local:

```bash
docker compose up --build
```

## Roadmap

- [x] Fundação FastAPI;
- [x] PostgreSQL assíncrono;
- [x] migrations;
- [x] CRUD de destinos;
- [x] executor HTTP;
- [x] histórico de verificações;
- [x] ciclo básico de incidentes;
- [x] endpoint para Cron;
- [ ] deploy do backend;
- [ ] configuração do Cron externo;
- [ ] integração com o DevBase;
- [ ] monitor específico para atividade de banco;
- [ ] notificações;
- [ ] métricas e gráficos.

## Licença

MIT.
