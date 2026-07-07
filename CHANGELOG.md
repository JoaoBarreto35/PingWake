# Changelog

Todas as alterações relevantes do PingWake serão registradas neste arquivo.

## [0.1.0] - 2026-07-07

### Adicionado

- estrutura inicial do projeto FastAPI;
- configuração assíncrona do PostgreSQL com SQLAlchemy e asyncpg;
- adaptação automática da URL de conexão do Neon;
- migrations com Alembic;
- CRUD de destinos monitorados;
- execução manual e agendada de health checks;
- histórico de verificações;
- gerenciamento automático de incidentes;
- proteção por chaves administrativas e de Cron;
- proteção básica contra SSRF;
- Docker e Docker Compose;
- testes automatizados;
- lint, tipagem e CI com GitHub Actions;
- documentação do projeto, arquitetura, Neon e DevBase.
