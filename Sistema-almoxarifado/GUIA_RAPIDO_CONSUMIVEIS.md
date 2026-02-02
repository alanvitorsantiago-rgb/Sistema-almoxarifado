# 🚀 GUIA RÁPIDO - CONSUMÍVEIS

## 📍 ONDE ENCONTRAR?

Na barra de navegação do seu sistema, você verá uma nova aba:

```
Dashboard | Estoque | Movimentação | Consumíveis ← AQUI! | Relatório | Importar | Usuários
```

---

## 🎯 PRIMEIROS PASSOS (5 minutos)

### PASSO 1: Preparar Planilha Excel

```
Abra o arquivo: exemplo_consumiveis.csv

Pode abrir em:
- Excel (save como .xlsx)
- Google Sheets (download como .xlsx)
- Qualquer outro programa de planilha

Colunas que DEVE ter:
✓ Nº PRODUTO
✓ CÓDIGO PRODUTO
✓ DESCRIÇÃO DO PRODUTO
✓ UNIDADE MEDIDA

Exemplo de linha:
001 | CX-001 | Caixa de Papelão | CX
```

### PASSO 2: Importar Primeira Vez

```
1. Clique em "Consumíveis" (🛒)
2. Clique em "Importar Planilha" (botão verde)
3. Selecione seu arquivo .xlsx
4. Clique em "Importar Planilha"
5. Pronto! Aparecer mensagem de sucesso
```

### PASSO 3: Usar o Sistema

```
Agora na aba Consumíveis você pode:

📋 LISTAR
  - Ver todos os consumíveis
  - Buscar por código, descrição ou categoria
  - Ver quantidade atual e mínima

📊 STATUS VISUAL
  - 🟢 Estoque OK (verde)
  - 🟡 Estoque Baixo (amarelo)
  - 🔴 Sem Estoque (vermelho)

🔄 MOVIMENTAÇÃO
  - Registrar entrada (recebimento)
  - Registrar saída (uso/entrega)
  - Quantidade atualiza automática

📈 HISTÓRICO
  - Clique no ícone de relógio
  - Veja todas as movimentações
  - Quem, quando, quanto, para onde

✏️ EDITAR (Admin apenas)
  - Clique no ícone de lápis
  - Altere qualquer campo
  - Salve as mudanças

🗑️ EXCLUIR (Admin apenas)
  - Clique no ícone de lixeira
  - Confirme a exclusão
  - Remove o consumível e histórico
```

---

## 📊 EXEMPLO: REGISTRAR UMA MOVIMENTAÇÃO

### Cenário: Recebeu caixa de papelão

```
1. Clique em "Consumíveis" → "Movimentação"

2. Selecione o consumível:
   "CX-001 - Caixa de Papelão Pequena"

3. Vê as informações atualizar:
   Descrição: Caixa de Papelão Pequena
   Unidade: CX
   Categoria: Embalagem
   Qtd em Estoque: 120

4. Escolha tipo: "Entrada" (já marca automaticamente)

5. Preencha os dados:
   Quantidade: 50
   Setor/Destino: Almoxarifado (auto-preenchido)
   Observação: Recebida da fornecedora X

6. Clique em "Registrar Movimentação"

7. Pronto! Quantidade agora é 170 (120 + 50)
   E fica registrado no histórico
```

### Cenário: Entregou pincel para produção

```
1. Clique em "Consumíveis" → "Movimentação"

2. Selecione: "PIN-001 - Pincel Redondo Nº 8"

3. Informações aparecem:
   Descrição: Pincel Redondo Nº 8
   Unidade: UN
   Categoria: Ferramentas
   Qtd em Estoque: 85

4. Escolha tipo: "Saída"

5. Preencha:
   Quantidade: 10
   Setor/Destino: Produção (você digita)
   Observação: Entrega para setor de pintura

6. Clique em "Registrar Movimentação"

7. Pronto! Quantidade agora é 75 (85 - 10)
   Registrado com setor de destino "Produção"
```

---

## 📋 CAMPOS DA PLANILHA (RESUMO)

| Campo                        | Obrigório | Exemplo          |
| ---------------------------- | --------- | ---------------- |
| Nº PRODUTO                   | ✅ SIM    | 001              |
| CÓDIGO PRODUTO               | ✅ SIM    | CX-001           |
| DESCRIÇÃO DO PRODUTO         | ✅ SIM    | Caixa de Papelão |
| UNIDADE MEDIDA               | ✅ SIM    | CX               |
| STATUS ESTOQUE               | ❌ não    | Ativo            |
| STATUS CONSUMO               | ❌ não    | Consumível       |
| CATEGORIA                    | ❌ não    | Embalagem        |
| FORNECEDOR                   | ❌ não    | Fornecedor A     |
| FORNECEDOR 2                 | ❌ não    | Fornecedor B     |
| VALOR UNITÁRIO               | ❌ não    | 5.50             |
| LEAD TIME                    | ❌ não    | 7                |
| % ESTOQUE DE SEGURANÇA       | ❌ não    | 10               |
| ESTOQUE MÍNIMO POR ATUALIZAR | ❌ não    | 50               |
| ESTOQUE ATUAL                | ❌ não    | 120              |

---

## 🔐 QUEM PODE FAZER O QUÊ?

### Qualquer Usuário:

```
✅ Visualizar consumíveis
✅ Buscar consumíveis
✅ Registrar movimentação (entrada/saída)
✅ Ver histórico
```

### Admin (Você):

```
✅ Tudo acima, mais:
✅ Importar planilha
✅ Editar consumível
✅ Excluir consumível
```

---

## ⚠️ DICAS IMPORTANTES

### 1️⃣ Nomes de Coluna

```
❌ ERRADO: "Nº", "Código", "Produto"
✅ CERTO: "Nº PRODUTO", "CÓDIGO PRODUTO", "DESCRIÇÃO DO PRODUTO"

⚠️ Cuidado: Maiúsculas/minúsculas E espaços IMPORTAM!
Copie exatamente do exemplo.
```

### 2️⃣ Extensão do Arquivo

```
❌ ERRADO: meuarquivo.csv, meuarquivo.xls
✅ CERTO: meuarquivo.xlsx

💡 Excel 2007+ salva como XLSX por padrão
```

### 3️⃣ Importar Múltiplas Vezes

```
Você pode importar a mesma planilha várias vezes!

Se o código já existe → ATUALIZA os dados
Se o código é novo → CRIA novo consumível

Útil para atualizar preços, fornecedores, etc.
```

### 4️⃣ Quantidade Atual

```
Não precisa estar certo na primeira importação!

Você pode:
1. Importar com quantidade 0
2. Depois registrar movimentações (entrada)
3. Sistema atualiza automaticamente

Ou:
1. Importar com quantidade certa
2. Sistema usa essa quantidade inicial
```

### 5️⃣ Estoque Mínimo

```
O sistema NÃO bloqueia saída abaixo do mínimo
(para mais flexibilidade)

Mas mostra aviso visual em AMARELO
Você deve ficar atento e fazer reposição!
```

---

## 🎨 CORES DE STATUS

```
🟢 VERDE (bg-success-subtle)
   └─ Quantidade > Estoque Mínimo
   └─ Tudo normal, estoque OK

🟡 AMARELO (bg-warning)
   └─ Quantidade <= Estoque Mínimo
   └─ ⚠️ Alerta! Precisa repor em breve

🔴 VERMELHO (bg-danger)
   └─ Quantidade = 0
   └─ 🚨 Crítico! Sem estoque!
```

---

## 🔄 FLUXO COMPLETO (RESUMO)

```
IMPORTAR PLANILHA
     ↓
VISUALIZAR CONSUMÍVEIS NA LISTAGEM
     ↓
REGISTRAR MOVIMENTAÇÕES
  (Entrada) → Qtd aumenta
  (Saída)   → Qtd diminui
     ↓
CONSULTAR HISTÓRICO
(Quem moveu, quando, quanto)
     ↓
(ADMIN) EDITAR OU EXCLUIR CONFORME NECESSÁRIO
```

---

## 📞 CHECKLIST ANTES DE COMEÇAR

```
□ Arquivo Excel preparado com dados dos consumíveis
□ Arquivo tem extensão .xlsx
□ Arquivo tem as 4 colunas obrigatórias
□ Nomes das colunas estão EXATOS (maiúsculas/espaços)
□ Arquivo salvo e fechado (não aberto)
□ Você tem permissão de Admin (para importar)

Tudo certo? ✅ Pode começar!
```

---

## ❓ DÚVIDAS FREQUENTES

**P: Errei ao importar, como refazer?**
R: Você pode reimportar a mesma planilha corrigida. O sistema atualiza automaticamente.

**P: Posso editar depois de importar?**
R: Sim! Clique no ícone de lápis (Admin). Mas para muitos itens, é melhor reimportar.

**P: Como atualizar quantidade em lote?**
R: Registre movimentações. Ou reimporte planilha com quantidades corretas.

**P: Posso excluir um consumível?**
R: Sim, clique no lixeira. Vai deletar também o histórico.

**P: Onde vejo o histórico?**
R: Clique no ícone de relógio (⏱️) na listagem.

**P: Qual a senha padrão?**
R: Usuário: `admin` | Senha: `admin`

---

## 🚀 BOA SORTE!

Seu sistema de consumíveis está 100% funcional!

Qualquer dúvida, basta chamar! 📞
