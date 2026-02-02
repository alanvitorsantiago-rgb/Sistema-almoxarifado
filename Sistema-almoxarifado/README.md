# Gerenciamento de Almoxarifado

Sistema web completo para gerenciamento de estoque e consumíveis, construído com Flask e SQLite.

## ✨ Funcionalidades

### 📦 Estoque Principal

- Cadastro de itens de estoque
- Listagem com busca avançada
- Movimentações (entrada/saída) com rastreamento
- Controle de lotes/NF
- Histórico de movimentações
- Exportação para Excel
- Importação em lote

### 🛒 Estoque de Consumíveis (NOVO!)

- Gerenciar consumíveis (caixa, pincel, lixa, fresa, fita, etc)
- Importação de planilha Excel
- Registrar entradas e saídas
- Histórico de movimentações
- Edição de dados
- Status visual em cores

### 📊 Relatórios

- Relatório de movimentações
- Relatórios por etapa
- Detalhes de lotes
- KPIs e alertas

### 👥 Administração

- Gerenciar usuários
- Controle de acesso (Admin/Usuário)
- Auditoria completa

## 🚀 Novo: Módulo de Consumíveis

Agora você pode gerenciar **estoque de consumíveis** com importação de Excel!

→ **[Ver Documentação de Consumíveis](INDICE_DOCUMENTACAO.md)**

Funcionalidades:

- ✅ Importar planilha com até 13 campos
- ✅ Listar consumíveis com busca
- ✅ Registrar entrada/saída
- ✅ Ver histórico completo
- ✅ Editar dados (Admin)
- ✅ Status visual em cores

## Tecnologias Utilizadas

- **Backend:** Python 3, Flask, SQLAlchemy
- **Frontend:** HTML, Jinja2, Bootstrap 5
- **Banco de Dados:** SQLite
- **Importação:** Pandas (Excel)
- **Autenticação:** Flask-Login, Bcrypt

## Como Executar o Projeto

Siga os passos abaixo para configurar e executar a aplicação em seu ambiente local.

### 1. Pré-requisitos

- Python 3.10+ instalado.
- `pip` (gerenciador de pacotes do Python).

### 2. Crie um Ambiente Virtual (venv)

É uma boa prática criar um ambiente virtual para isolar as dependências do projeto.

```bash
# Crie a pasta do ambiente virtual (ex: .venv)
python -m venv .venv

# Ative o ambiente virtual
# No Windows:
.\.venv\Scripts\activate
# No macOS/Linux:
source .venv/bin/activate
```

### 3. Instale as Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias a partir do arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Execute a Aplicação

Execute o script principal `app.py`. O Flask iniciará um servidor de desenvolvimento.

```bash
python app.py
```

O sistema irá automaticamente criar o arquivo de banco de dados `database.db` na primeira vez que for executado.

### 5. Acesse o Sistema

Abra seu navegador e acesse a seguinte URL:

http://127.0.0.1:5000/

Você verá a página inicial do sistema e poderá navegar para cadastrar e listar os itens.
