# Atualização para PingWake 0.4.0

## Alterações

- método `POST` nos targets;
- headers personalizados criptografados;
- body JSON criptografado;
- suporte a RPC do Supabase;
- migration `20260708_0003`.

## 1. Atualizar o código

Substitua os arquivos pela versão 0.4.0 e instale novamente as dependências:

```powershell
pip install -e ".[dev]"
```

## 2. Gerar a chave de criptografia

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Adicione o mesmo valor no `.env` e no Render:

```env
APP_VERSION=0.4.0
PINGWAKE_ENCRYPTION_KEY=VALOR_GERADO
```

Não reutilize a API key nem a chave do Cron como chave de criptografia.

## 3. Executar a migration local

```powershell
alembic upgrade head
```

No Render, o Dockerfile já executa `alembic upgrade head` antes de iniciar a API.

## 4. Publicar

```powershell
git add .
git commit -m "feat: add encrypted request headers and body"
git push
```

## 5. Validar

Abra `/docs`, crie um target de teste com `request_headers` e confirme que a resposta
contém apenas `has_custom_headers: true`, sem devolver os valores.
