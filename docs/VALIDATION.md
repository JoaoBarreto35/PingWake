# Relatório de validação

Data: 8 de julho de 2026

## Verificações executadas

- compilação e instalação editável pelo `pyproject.toml`;
- Ruff em todo o repositório;
- formatação Ruff;
- Mypy em todo o pacote `app`;
- testes automatizados com banco SQLite isolado;
- criptografia e descriptografia dos dados de request;
- confirmação de que valores secretos não aparecem nas respostas;
- envio simulado de `POST` com header e body JSON;
- upgrade, downgrade e novo upgrade da migration em SQLite;
- geração offline de todo o SQL para PostgreSQL.

## Resultado

```text
Ruff: aprovado
Ruff format: aprovado
Mypy: aprovado
Pytest: 18 testes aprovados
Alembic SQLite upgrade/downgrade: aprovado
Alembic PostgreSQL offline: aprovado
```

## Limite da validação

A migration não foi executada diretamente no Neon desta sessão porque a URL privada do
projeto não foi incluída. O container do Render executará `alembic upgrade head` antes de
iniciar a API.
