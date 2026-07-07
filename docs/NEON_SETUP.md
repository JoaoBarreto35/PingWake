# Configuração do Neon PostgreSQL

O PingWake usa o Neon somente como banco PostgreSQL gerenciado. O backend continua
independente e poderá ser hospedado em outro provedor.

## 1. Criar o projeto

No painel do Neon, crie um projeto com:

- **Project name:** `pingwake`
- **PostgreSQL version:** versão estável sugerida pelo Neon
- **Region:** a mais próxima do local onde o backend será publicado

Um único projeto e um único banco são suficientes para o MVP.

## 2. Copiar a conexão direta

Abra **Connect**, desative a opção de pooling e copie a **Direct connection string**.
Para este MVP, a conexão direta evita limitações do PgBouncer durante as migrations do
Alembic. A carga do PingWake é pequena e não exige pooling inicialmente.

A URL normalmente terá este formato:

```text
postgresql://USUARIO:SENHA@HOST/NOME_DO_BANCO?sslmode=require&channel_binding=require
```

O PingWake faz automaticamente os ajustes necessários para o `asyncpg`:

- troca `postgresql://` por `postgresql+asyncpg://` internamente;
- troca `sslmode=require` por `ssl=require`;
- remove `channel_binding=require`.

## 3. Preencher o `.env`

```env
DATABASE_URL=postgresql://USUARIO:SENHA@HOST/NOME_DO_BANCO?sslmode=require&channel_binding=require
PINGWAKE_API_KEY=uma-chave-administrativa-longa-e-aleatoria
PINGWAKE_CRON_KEY=outra-chave-longa-e-diferente
```

Para gerar chaves no PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Execute o comando duas vezes e use valores diferentes.

## 4. Criar as tabelas

Com o ambiente virtual ativado:

```bash
alembic upgrade head
```

O Alembic criará:

- `monitoring_targets`;
- `check_runs`;
- `incidents`;
- `alembic_version`.

## 5. Validar

Inicie a API:

```bash
uvicorn app.main:app --reload
```

Acesse:

```text
http://localhost:8000/health/ready
```

A resposta esperada é:

```json
{
  "status": "ok",
  "service": "PingWake",
  "version": "0.1.0",
  "dependencies": {
    "database": "ok"
  }
}
```

## Observação sobre pooling

Caso o projeto cresça, poderemos usar uma conexão pooled na aplicação e manter uma
conexão direta separada para migrations. Isso continua representando o mesmo banco de
dados, apenas com dois caminhos de conexão.
