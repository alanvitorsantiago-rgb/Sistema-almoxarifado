# Sistema de Gerenciamento de Consumíveis

## 📋 Descrição

Nova funcionalidade adicionada ao Sistema de Almoxarifado para gerenciar **estoque de consumíveis** como caixas de papelão, pincéis, lixas, fresas, fitas, tintas, etc.

## ✨ Recursos Principais

### 1. **Aba de Consumíveis**

- Visualizar todos os consumíveis cadastrados
- Buscar por código, descrição ou categoria
- Ver quantidade atual e estoque mínimo
- Status visual de estoque (em estoque, baixo, zerado)

### 2. **Importação de Planilha Excel**

- Importar múltiplos consumíveis de uma vez
- Atualizar consumíveis existentes automaticamente
- Suporta colunas obrigatórias e opcionais

### 3. **Movimentação de Consumíveis**

- Registrar entradas e saídas de consumíveis
- Auto-preenchimento de setor de destino para entradas
- Histórico completo de movimentações

### 4. **Edição e Exclusão**

- Editar informações de consumíveis
- Excluir consumíveis (apenas admins)
- Visualizar histórico de movimentações

## 📊 Estrutura da Planilha de Importação

### Colunas Obrigatórias:

| Campo                    | Descrição                 | Exemplo                  |
| ------------------------ | ------------------------- | ------------------------ |
| **Nº PRODUTO**           | Número único do produto   | 001, 002, 003            |
| **CÓDIGO PRODUTO**       | Código identificador      | CX-001, PIN-001          |
| **DESCRIÇÃO DO PRODUTO** | Nome/descrição do produto | Caixa de Papelão, Pincel |
| **UNIDADE MEDIDA**       | Unidade (UN, CX, KG, L)   | CX, UN, KG, L            |

### Colunas Opcionais:

| Campo                        | Descrição               | Padrão     |
| ---------------------------- | ----------------------- | ---------- |
| STATUS ESTOQUE               | Ativo ou Inativo        | Ativo      |
| STATUS CONSUMO               | Tipo de consumo         | Consumível |
| CATEGORIA                    | Categoria do produto    | (vazio)    |
| FORNECEDOR                   | Fornecedor principal    | (vazio)    |
| FORNECEDOR 2                 | Fornecedor alternativo  | (vazio)    |
| VALOR UNITÁRIO               | Valor em R$             | 0          |
| LEAD TIME                    | Dias para reposição     | 7          |
| % ESTOQUE DE SEGURANÇA       | Percentual de segurança | 0          |
| ESTOQUE MÍNIMO POR ATUALIZAR | Quantidade mínima       | 0          |
| ESTOQUE ATUAL                | Quantidade em estoque   | 0          |

## 📁 Exemplo de Planilha

Um arquivo de exemplo está disponível em: `exemplo_consumiveis.csv`

### Como criar sua planilha:

1. Copie o exemplo fornecido ou crie um arquivo Excel novo
2. Certifique-se que os nomes das colunas são **exatamente** os nomes listados acima
3. Preencha as linhas com os dados dos consumíveis
4. Salve como arquivo `.xlsx` (Excel 2007+)
5. Importe via "Importar Planilha" na aba de consumíveis

## 🔄 Fluxo de Uso

### 1. Primeira Vez - Importação de Dados

```
Consumíveis → Importar Planilha → Selecionar arquivo Excel → Importar
```

### 2. Registrar Movimentação

```
Consumíveis → Movimentação → Selecionar consumível → Tipo (Entrada/Saída) → Quantidade → Salvar
```

### 3. Editar Consumível (Admin)

```
Consumíveis → Clicar em Editar → Alterar dados → Salvar
```

### 4. Ver Histórico

```
Consumíveis → Clicar em Histórico → Ver todas as movimentações
```

## 🗂️ Novos Arquivos Criados

### Modelos (models.py):

- `ConsumivelEstoque` - Tabela principal de consumíveis
- `MovimentacaoConsumivel` - Histórico de movimentações

### Rotas (app.py):

- `/consumivel` - Listagem de consumíveis
- `/consumivel/importar` - Importação de planilha
- `/consumivel/movimentacao` - Registrar movimentação
- `/consumivel/editar/<id>` - Editar consumível
- `/consumivel/excluir/<id>` - Excluir consumível
- `/consumivel/historico/<id>` - Ver histórico

### Templates:

- `consumivel.html` - Listagem principal
- `importar_consumivel.html` - Importação
- `movimentacao_consumivel.html` - Registrar movimentação
- `editar_consumivel.html` - Editar item
- `historico_consumivel.html` - Histórico de movimentações

## 📝 Campos de Dados

### ConsumivelEstoque:

- `n_produto` - Número único
- `status_estoque` - Status (Ativo/Inativo)
- `status_consumo` - Tipo de consumo
- `codigo_produto` - Código do produto (único)
- `descricao` - Descrição
- `unidade_medida` - Unidade (UN, CX, KG, L, etc)
- `categoria` - Categoria
- `fornecedor` - Fornecedor principal
- `fornecedor2` - Fornecedor alternativo
- `valor_unitario` - Valor em R$
- `lead_time` - Tempo de reposição em dias
- `estoque_seguranca` - Percentual de segurança
- `estoque_minimo` - Quantidade mínima
- `quantidade_atual` - Quantidade em estoque
- `data_cadastro` - Data de criação
- `data_atualizacao` - Última atualização

### MovimentacaoConsumivel:

- `consumivel_id` - ID do consumível
- `tipo` - ENTRADA ou SAÍDA
- `quantidade` - Quantidade movimentada
- `data_movimentacao` - Data/hora da movimentação
- `observacao` - Observação
- `usuario` - Usuário que fez a movimentação
- `setor_destino` - Setor de destino

## 🔐 Permissões

| Ação                   | Usuário Normal | Admin |
| ---------------------- | -------------- | ----- |
| Visualizar consumíveis | ✅             | ✅    |
| Registrar movimentação | ✅             | ✅    |
| Importar planilha      | ❌             | ✅    |
| Editar consumível      | ❌             | ✅    |
| Excluir consumível     | ❌             | ✅    |

## 💡 Dicas

1. **Importação em Lote**: Você pode importar a planilha múltiplas vezes. Se o código do produto já existe, os dados serão atualizados.

2. **Status de Estoque**: A cor da célula de quantidade indica:

   - 🟢 Verde: Quantidade acima do mínimo
   - 🟡 Amarelo: Quantidade no mínimo ou abaixo
   - 🔴 Vermelho: Sem estoque (quantidade = 0)

3. **Setor de Destino**: Na entrada, é auto-preenchido com "Almoxarifado". Na saída, você especifica para qual setor vai.

4. **Histórico Completo**: Todas as movimentações ficam registradas no histórico para rastreabilidade.

## 🐛 Troubleshooting

### Erro ao importar planilha

- Verificar se o arquivo é `.xlsx`
- Confirmar se os nomes das colunas estão **exatamente** como especificado
- Garantir que as colunas obrigatórias têm dados

### Consumível não aparece na lista

- Verificar se foi importado corretamente
- Clicar em "Limpar" no filtro de busca

### Problema ao registrar movimentação

- Selecionar um consumível válido
- Informar quantidade e tipo de movimentação
- Verificar se há quantidade suficiente para saída
