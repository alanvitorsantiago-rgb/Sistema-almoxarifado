# 🔑 Como Obter a SUPABASE_SERVICE_KEY

## Passo a Passo

1. **Acesse o Dashboard do Supabase**
   - URL: https://supabase.com/dashboard/project/twydlslxhtoqsqnixcmz

2. **Navegue para Settings → API**
   - No menu lateral esquerdo, clique em ⚙️ **Settings**
   - Depois clique em **API**

3. **Localize a Service Role Key**
   - Na seção **Project API keys**
   - Procure por **`service_role` key** (não confundir com `anon` key)
   - A key começa com: `eyJhbGci...` (é um JWT token bem longo)

4. **Copie a Key**
   - Clique no ícone de copiar ao lado da key
   - **⚠️ IMPORTANTE**: Esta é uma chave SECRETA (server-side only)
   - Nunca exponha ela public no frontend!

5. **Cole no arquivo `.env.supabase`**
   - Substitua `your-service-role-key-here` pela key copiada
   - Deve ficar algo como:
   ```bash
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
   ```

## Verificação

Após adicionar a key, teste a conexão:

```bash
python supabase_client.py
```

Você deve ver:
```
✅ Cliente Supabase inicializado com sucesso (HTTPS/443)
🧪 Testando conexão com Supabase...
✅ Conexão OK - X usuários encontrados
✅ Cliente Supabase funcionando corretamente!
```

## 🔐 Segurança

- ✅ A Service Role Key **bypassa RLS** (Row Level Security)
- ✅ Deve ser usada **APENAS no backend** (nunca no frontend)
- ✅ Está no `.gitignore` (não será commitada)
- ✅ Em produção (Vercel), será configurada como variável de ambiente
