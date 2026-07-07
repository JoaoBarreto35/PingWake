# Relatório de validação

Data: 7 de julho de 2026

## Verificações executadas

- compilação de todos os arquivos Python;
- instalação do projeto pelo `pyproject.toml`;
- Ruff em todo o repositório;
- Mypy em todo o pacote `app`;
- testes automatizados com banco SQLite isolado;
- execução da migration inicial em SQLite de teste;
- geração offline do SQL PostgreSQL da migration inicial.

## Resultado

```text
Ruff: aprovado
Mypy: aprovado
Pytest: 6 testes aprovados
Alembic SQLite: aprovado
Alembic PostgreSQL offline: aprovado
```

## Limite da validação

A conexão real com o Neon não foi executada porque depende da URL e das credenciais do
projeto que serão criadas pelo proprietário. O código está preparado para receber a URL
fornecida pelo Neon no arquivo `.env`.
