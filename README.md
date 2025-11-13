# Gerenciamento de Almoxarifado

Este é um sistema web para gerenciamento de estoque, construído com Flask, SQLite e com acesso externo facilitado via ngrok.

## Funcionalidades

- Cadastro de itens de estoque.
- Listagem de todos os itens cadastrados.
- Movimentação de entrada e saída de itens por lote.
- Geração de relatórios e exportação para Excel.
- Dashboard com KPIs e gráficos.
- Interface web responsiva com Bootstrap 5.
- Acesso externo simplificado com `ngrok`, sem necessidade de configuração de firewall ou permissões de administrador.

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
