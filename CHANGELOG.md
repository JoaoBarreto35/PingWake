# Changelog

Todas as alterações relevantes do PingWake serão registradas neste arquivo.

## [0.4.0] - 2026-07-08

### Adicionado

- suporte ao método HTTP `POST`;
- headers personalizados por target;
- body JSON opcional por target;
- criptografia Fernet dos headers e bodies antes da persistência;
- indicadores públicos `has_custom_headers` e `has_request_body`;
- migration `20260708_0003`;
- documentação e exemplo completo para Supabase RPC;
- testes de criptografia, redaction, atualização e envio HTTP.

### Segurança

- valores secretos não são retornados pelos endpoints administrativos;
- proteção contra CRLF em headers;
- bloqueio de headers gerenciados pelo cliente HTTP;
- limites de quantidade e tamanho para headers e body;
- falha segura como `configuration_error` quando a chave não permite descriptografar.

## [0.3.0] - 2026-07-08

### Adicionado

- endpoint `GET /api/v1/integrations/devbase/targets/{target_id}`;
- resposta resumida com status, latência, HTTP, contadores e incidente aberto;
- testes de autenticação e contrato da integração;
- compatibilidade com a integração de leitura do DevBase 4.1.0.

### Segurança

- endpoint protegido pela chave administrativa existente;
- nenhuma credencial ou corpo de resposta é exposto ao DevBase.

## [0.2.0] - 2026-07-07

### Adicionado

- notificações no Discord ao abrir e resolver incidentes;
- tabela `notification_events` para rastrear envios e falhas;
- endpoint administrativo `GET /api/v1/notifications`;
- migration `20260707_0002`;
- testes de envio e falha do webhook;
- execução automática das migrations no início do container.

### Corrigido

- esquemas de autenticação do Swagger separados entre chave administrativa e chave do Cron;
- comparação das chaves usando `compare_digest`.

### Segurança

- URL do webhook tratada como segredo;
- erros de notificação não expõem o token do Discord;
- indisponibilidade do Discord não desfaz checks nem incidentes.

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
