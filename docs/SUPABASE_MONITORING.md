# Monitoramento de projetos Supabase

O PingWake 0.4.0 pode chamar a Data API do Supabase com headers e body JSON criptografados.
A configuração recomendada usa uma função RPC mínima, sem ler dados reais da aplicação.

## 1. Criar a função no SQL Editor

```sql
create or replace function public.ping_health()
returns jsonb
language sql
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'status', 'ok',
    'database', 'ok',
    'timestamp', now()
  );
$$;

revoke all on function public.ping_health() from public;
grant execute on function public.ping_health() to anon;
grant execute on function public.ping_health() to authenticated;
```

A função não recebe parâmetros, não retorna dados da aplicação e executa somente uma
consulta pequena no PostgreSQL.

## 2. Obter a publishable key

No Dashboard do Supabase, abra **Settings → API Keys** e copie a **Publishable key**.
Para esse health check, não use `service_role` nem uma secret key.

## 3. Gerar a chave do PingWake

No projeto PingWake:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Cadastre o valor no `.env` e no Render:

```env
PINGWAKE_ENCRYPTION_KEY=VALOR_GERADO
```

Essa chave precisa permanecer estável. Trocar ou perder o valor impede a leitura dos
headers e bodies já criptografados.

## 4. Criar o target no Swagger

Use `POST /api/v1/targets`:

```json
{
  "name": "Projeto — Supabase Database",
  "description": "Health check da Data API e do PostgreSQL",
  "project_name": "Projeto",
  "target_type": "database",
  "monitoring_mode": "database_activity",
  "environment": "production",
  "provider": "Supabase",
  "url": "https://SEU_PROJECT_REF.supabase.co/rest/v1/rpc/ping_health",
  "http_method": "POST",
  "expected_status_code": 200,
  "interval_minutes": 720,
  "timeout_seconds": 20,
  "enabled": true,
  "request_headers": {
    "apikey": "sb_publishable_..."
  },
  "request_body": {}
}
```

Para as chaves modernas `sb_publishable_...`, o header necessário é `apikey`. Não use a
publishable key como `Authorization: Bearer`, pois ela não é um JWT.

## 5. Executar e validar

Execute:

```http
POST /api/v1/targets/{target_id}/check
```

Resultado esperado:

```json
{
  "status": "healthy",
  "http_status_code": 200
}
```

A resposta do target não devolve a publishable key nem o body. Ela informa apenas:

```json
{
  "has_custom_headers": true,
  "has_request_body": true
}
```

## Atualizações

Ao usar `PATCH /api/v1/targets/{target_id}`:

- omita `request_headers` e `request_body` para preservar a configuração atual;
- envie `request_headers: null` para apagar os headers;
- envie `request_body: null` para apagar o body;
- envie novos valores para substituí-los integralmente.

## Intervalo recomendado

Para apenas confirmar atividade e saúde do banco, use 12 ou 24 horas. Não há necessidade
de consultar um projeto Supabase a cada cinco minutos.
