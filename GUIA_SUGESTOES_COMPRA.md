# Guia: Sugestões de Compra Inteligente - Personalização

## 📋 Visão Geral

A funcionalidade **Sugestões de Compra Inteligente** foi melhorada para permitir que você configure **exatamente quanto comprar** quando um item chegar ao estoque mínimo.

## ✨ Mudanças Implementadas

### 1. Novo Campo: "Quantidade Ideal para Comprar"

Cada item agora possui um campo opcional chamado **"Quantidade Ideal para Comprar"** que controla a quantidade exata sugerida quando o estoque cai para o mínimo.

### 2. Dois Modos de Funcionamento

#### Modo Automático (Padrão)

- Se você **não preencher** o campo "Quantidade Ideal para Comprar"
- O sistema calcula automaticamente: `(Estoque Mínimo × 2) - Estoque Projetado`
- Exemplo: Se o mínimo é 10, ele sugere comprar para chegar a 20 unidades

#### Modo Manual (Configurado)

- Se você **preencher** o campo "Quantidade Ideal para Comprar"
- O sistema **sempre sugere exatamente essa quantidade** quando atingir o mínimo
- Exemplo: Se você coloca 150, o sistema sempre sugere comprar 150 unidades

## 🎯 Como Usar

### Para Cadastrar um Novo Item com Quantidade Ideal

1. Acesse **Cadastro de Item**
2. Preencha os campos normalmente
3. No final do formulário, você verá:

   - **Estoque Mínimo** (obrigatório)
   - **Quantidade Ideal para Comprar** (opcional)
   - **Tempo de Reposição** (em dias)

4. Exemplo:
   ```
   Estoque Mínimo: 10
   Quantidade Ideal para Comprar: 100
   Tempo de Reposição: 7 dias
   ```

### Para Editar um Item Existente

1. Acesse **Estoque** e clique em um item
2. Clique em **Editar**
3. Procure pelos campos:

   - **Estoque Mínimo**
   - **Quantidade Ideal para Comprar**
   - **Tempo de Reposição**

4. Modifique conforme necessário:

   - Deixe em branco = usa cálculo automático
   - Preencha com um valor = sempre sugere aquele valor

5. Salve as alterações

## 💡 Exemplos de Uso

### Exemplo 1: Parafusos (uso frequente)

```
Estoque Mínimo: 50 unidades
Quantidade Ideal para Comprar: 500 unidades (meio pacote)
Tempo de Reposição: 7 dias
```

Quando chegar a 50, o sistema sugere: **Comprar 500 unidades**

### Exemplo 2: Tinta Especial (uso esporádico)

```
Estoque Mínimo: 2 latas
Quantidade Ideal para Compra: (deixar em branco)
Tempo de Reposição: 14 dias
```

Quando chegar a 2 latas, o sistema sugere: **Comprar para chegar a 4 latas** (cálculo automático)

### Exemplo 3: Consumível Premium

```
Estoque Mínimo: 5 caixas
Quantidade Ideal para Comprar: 50 caixas (compra em lote)
Tempo de Reposição: 30 dias
```

Quando chegar a 5 caixas, o sistema sugere: **Comprar 50 caixas**

## 🔧 Campos Relacionados

| Campo                             | Descrição                                                | Exemplo |
| --------------------------------- | -------------------------------------------------------- | ------- |
| **Estoque Mínimo**                | Quantidade mínima que o item deve ter                    | 10      |
| **Quantidade Ideal para Comprar** | Quantidade exata a comprar (deixe vazio para automático) | 100     |
| **Tempo de Reposição**            | Dias que leva para o fornecedor entregar                 | 7       |

## 📊 Onde Ver as Sugestões

As sugestões aparecem em:

1. **Dashboard** - Seção "Sugestões de Compra Inteligente"
2. A lista mostra:
   - Nome do item
   - Quantidade sugerida (a que você configurou ou a calculada)
   - Prazo até quando comprar

## 🚀 Dicas Práticas

### Dica 1: Configure Só o Necessário

- Deixe em branco para itens com consumo variável
- Preencha para itens que você sempre compra em quantidade fixa

### Dica 2: Considere Fornecedores

- Se o fornecedor vende em caixas de 50, configure 50 como ideal
- Evita compras fracionadas ou desperdício

### Dica 3: Revise Periodicamente

- Ajuste as quantidades ideais conforme o consumo muda
- Use o histórico de movimentações como referência

## ⚠️ Importante

- O campo "Quantidade Ideal para Comprar" é **completamente opcional**
- Se deixado em branco, o sistema usa cálculo automático
- Pode ser alterado a qualquer momento sem afetar itens antigos
- Apareça nas sugestões quando: `Estoque Projetado < Estoque Mínimo`

---

**Versão:** 1.0 | **Data:** Janeiro 2026
