# /app.py

import os
# from sqlalchemy import or_, func  <- REMOVIDO
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import User, ItemEstoque, Movimentacao, EstoqueDetalhe, ConsumivelEstoque, MovimentacaoConsumivel, ModelWrapper
from database_helpers import * # Importa todas as funções helper do Supabase
from functools import wraps
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
# Importa o modelo de suavização exponencial para previsão
# from statsmodels.tsa.api import ExponentialSmoothing  # REMOVIDO POR LIMITE DE TAMANHO VERCEL
import io
from flask_socketio import SocketIO
import unicodedata

# --- INICIALIZAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv('.env.supabase')  # Carrega configurações do arquivo .env.supabase

def configure_app(app_instance):
    """Configura a aplicação Flask."""
    # Chave secreta para sessões e mensagens flash
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-super-segura')
    
    # REMOVIDO: Configuração do SQLAlchemy (não é mais necessária)
    # app_instance.config['SQLALCHEMY_DATABASE_URI'] ...
    
    # Inicializa as extensões com a aplicação
    bcrypt.init_app(app_instance)
    socketio.init_app(app_instance)
    login_manager.init_app(app_instance)

# Inicializa as extensões sem a aplicação para serem configuradas depois
bcrypt = Bcrypt()
login_manager = LoginManager()
socketio = SocketIO()
login_manager.login_view = 'login'  # Rota para redirecionar usuários não logados
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = 'info'

configure_app(app)

def check_admin_user():
    """Garante que o usuário admin exista."""
    try:
        admin_user = get_user_by_username('admin')
        if not admin_user:
            print("🔧 Usuário 'admin' não encontrado. Criando agora...")
            hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
            create_user(username='admin', password_hash=hashed_password, role='admin')
            print("✅ Usuário 'admin' criado com a senha 'admin'.")
        else:
             print("✅ Sistema inicializado. Conexão Supabase OK.")
    except Exception as e:
        print(f"⚠️ Erro ao verificar admin: {e}")

with app.app_context():
    check_admin_user()

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    if user_data:
        return User(user_data) # Retorna objeto User (ModelWrapper)
    return None

# --- FUNÇÕES AUXILIARES E CONTEXT PROCESSORS ---

def calculate_validity_status(validade_date):
    """Calcula o status de validade e retorna uma tupla (texto, classe_css)."""
    if not validade_date:
        return ("Sem validade", "text-muted")

    today = datetime.today().date()
    delta = (validade_date - today).days

    if delta < 0:
        return (f"Vencido há {-delta} dia(s)", "text-danger fw-bold")
    elif delta == 0:
        return ("Vence hoje!", "text-danger fw-bold")
    elif delta <= 30:
        return (f"Vence em {delta} dia(s)", "text-warning fw-bold")
    elif delta <= 90:
        return (f"Vence em {delta} dia(s)", "text-info")
    else:
        return (f"Vence em {delta} dia(s)", "text-success")

@app.context_processor
def utility_processor():
    """Disponibiliza a função para todos os templates."""
    return dict(calculate_status=calculate_validity_status)

# --- DECORADOR PARA ROTAS DE ADMIN ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Esta área é restrita a administradores.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- DECORADOR PARA ROTAS DE ADMIN ONLY (Nega acesso a usuários padrão) ---
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Esta ação é permitida apenas para administradores.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# --- ROTAS DA APLICAÇÃO ---

@app.route('/relatorio/movimentacoes')
@admin_only
@login_required
def relatorio_movimentacoes():
    """Exibe o relatório de movimentações com filtros de data."""
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    search_query = request.args.get('q', '')

    # Busca dados via helper (já faz os joins e filtros básicos)
    movimentacoes_data = get_movimentacoes_report(
        data_inicio=data_inicio_str,
        data_fim=data_fim_str,
        search_term=search_query
    )
    
    # Envolve em objetos para compatibilidade com template (acesso .item.codigo)
    movimentacoes = [Movimentacao(m) for m in movimentacoes_data]

    # --- Lógica para o Gráfico de Pizza ---
    # Conta o número de ocorrências de cada tipo de movimentação na lista filtrada
    entradas_count = sum(1 for mov in movimentacoes if 'ENTRADA' in mov.tipo and 'AJUSTE' not in mov.tipo)
    saidas_count = sum(1 for mov in movimentacoes if 'SAIDA' in mov.tipo and 'AJUSTE' not in mov.tipo)
    ajustes_count = sum(1 for mov in movimentacoes if 'AJUSTE' in mov.tipo)

    pie_chart_data = {
        'labels': ['Entradas', 'Saídas', 'Ajustes'],
        'counts': [entradas_count, saidas_count, ajustes_count]
    }

    return render_template('relatorio_movimentacoes.html', 
                           movimentacoes=movimentacoes, 
                           title="Relatório de Movimentações", 
                           data_inicio=data_inicio_str, data_fim=data_fim_str, 
                           search_query=search_query,
                           pie_chart_data=pie_chart_data)

@app.route('/dashboard')
@login_required
def dashboard():
    """Renderiza o dashboard com dados reais do banco de dados (Supabase REST)."""
    hoje = date.today()

    # --- KPIs e Métricas Gerais (via helper otimizado) ---
    metrics = get_dashboard_metrics()
    
    # Lotes críticos
    critical_lotes_data = get_critical_lotes(days=30)
    critical_lotes = [EstoqueDetalhe(l) for l in critical_lotes_data]

    # --- Dados para o Gráfico de Movimentações (Últimos 15 dias) ---
    # Como isso requer agregação diária complexa, simplificamos ou mantemos via Python
    # Para manter "sem alterar regras", buscamos movimentos dos ultimos 15 dias e agregamos aqui
    labels_mov = [(hoje - timedelta(days=i)).strftime('%d/%m') for i in range(14, -1, -1)]
    
    # Busca movimentações dos últimos 15 dias para agregar
    data_inicio_grafico = (hoje - timedelta(days=15)).strftime('%Y-%m-%d')
    recent_moves_raw = get_movimentacoes_report(data_inicio=data_inicio_grafico)
    
    entradas_map = {}
    saidas_map = {}
    
    for mov in recent_moves_raw:
        dt = datetime.fromisoformat(mov['data_movimentacao']).strftime('%d/%m')
        qtd = mov.get('quantidade', 0)
        tipo = mov.get('tipo', '')
        
        if 'ENTRADA' in tipo:
            entradas_map[dt] = entradas_map.get(dt, 0) + qtd
        elif 'SAIDA' in tipo:
            saidas_map[dt] = saidas_map.get(dt, 0) + qtd
            
    entradas = [entradas_map.get(lbl, 0) for lbl in labels_mov]
    saidas = [saidas_map.get(lbl, 0) for lbl in labels_mov]

    movimentacoes_chart_data = {
        'labels': labels_mov, 'entradas': entradas, 'saidas': saidas
    }

    # --- Listas Top 5 ---
    # Top stocked
    top_items_data = get_top_items(limit=5, order_by='qtd_estoque', desc=True)
    top_stocked_items = [ItemEstoque(i) for i in top_items_data]
    
    # Low stocked (precisa de lógica especial pois API não filtra col <= col)
    low_items_data = get_low_stock_items(limit=5)
    low_stocked_items = [ItemEstoque(i) for i in low_items_data]

    # --- Atividade Recente ---
    recent_mov_data = get_recent_movimentacoes(limit=5)
    recent_movimentacoes = [Movimentacao(m) for m in recent_mov_data]

    # --- Dados para Alertas de Validade ---
    # Lotes vencendo hoje / proximos
    lotes_hoje_data = get_expiring_lots(days=0, today_only=True)
    lotes_vencendo_hoje = [EstoqueDetalhe(l) for l in lotes_hoje_data]
    
    lotes_prox_data = get_expiring_lots(days=40, today_only=False)
    lotes_proximo_vencimento = [EstoqueDetalhe(l) for l in lotes_prox_data]

    # --- DADOS DE CONSUMÍVEIS ---
    # Simplificação: Buscamos todos consumíveis (se forem poucos) ou criamos helpers
    # Assumindo quantity moderate, fetch all simples
    todos_consumiveis = get_all_consumiveis()
    total_consumiveis = len(todos_consumiveis)
    consumiveis_zerados = sum(1 for c in todos_consumiveis if c.get('quantidade_atual', 0) == 0)
    consumiveis_baixo_estoque = sum(1 for c in todos_consumiveis if c.get('quantidade_atual', 0) > 0 and c.get('quantidade_atual', 0) <= c.get('estoque_minimo', 0))
    
    # Ordenar para pegar top 5 low
    low_consumiveis_data = sorted(todos_consumiveis, key=lambda x: x.get('quantidade_atual', 0))[:5]
    low_consumiveis = [ConsumivelEstoque(c) for c in low_consumiveis_data]
    
    # Recent moves consumiveis
    recent_cons_moves_data = get_movimentacoes_consumivel(limit=5)
    recent_consumivel_moves = [MovimentacaoConsumivel(m) for m in recent_cons_moves_data]

    return render_template('dashboard.html', 
                           total_items_distintos=metrics['total_items_distintos'],
                           total_unidades=metrics['total_unidades'],
                           itens_zerados=metrics['itens_zerados'],
                           critical_lotes=critical_lotes,
                           movimentacoes_chart_data=movimentacoes_chart_data,
                           tipos_chart_data=metrics['tipos_chart_data'],
                           top_stocked_items=top_stocked_items,
                           low_stocked_items=low_stocked_items,
                           recent_movimentacoes=recent_movimentacoes,
                           lotes_vencendo_hoje=lotes_vencendo_hoje,
                           lotes_proximo_vencimento=lotes_proximo_vencimento,
                           today_date=hoje,
                           total_consumiveis=total_consumiveis,
                           consumiveis_zerados=consumiveis_zerados,
                           consumiveis_baixo_estoque=consumiveis_baixo_estoque,
                           low_consumiveis=low_consumiveis,
                           recent_consumivel_moves=recent_consumivel_moves)

@app.route('/api/kpis')
@login_required
def api_kpis():
    """Retorna os dados dos KPIs principais em formato JSON."""
    metrics = get_dashboard_metrics()
    
    # Busca lotes críticos via helper
    critical_lotes_data = get_critical_lotes(days=30)
    
    kpis = {
        'total_items_distintos': metrics['total_items_distintos'],
        'total_unidades': metrics['total_unidades'],
        'itens_zerados': metrics['itens_zerados'],
        'critical_lotes': critical_lotes_data # Retorna lista de dicts
    }
    return jsonify(kpis)

@app.route('/api/items/search')
@login_required
def api_items_search():
    """API para buscar itens por código ou descrição para autocompletar."""
    search_query = request.args.get('q', '')
    query = ItemEstoque.query
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(or_(
            ItemEstoque.codigo.ilike(search_term),
            ItemEstoque.descricao.ilike(search_term)
        ))
    
    items = query.limit(10).all()
    results = [{'id': item.id, 'text': f"{item.codigo} - {item.descricao}"} for item in items]
    return jsonify(results)

@app.route('/api/item/<int:item_id>/historico-chart')
@login_required
def api_item_historico_chart(item_id):
    """Retorna o histórico de movimentações de um item para o gráfico."""
    hoje = date.today()
    labels_mov = [(hoje - timedelta(days=i)).strftime('%d/%m') for i in range(14, -1, -1)]
    entradas = []
    saidas = []
    for i in range(14, -1, -1):
        dia = hoje - timedelta(days=i)
        entradas.append(db.session.query(func.sum(Movimentacao.quantidade)).filter(Movimentacao.item_id==item_id, Movimentacao.tipo=='ENTRADA', func.date(Movimentacao.data_movimentacao)==dia).scalar() or 0)
        saidas.append(db.session.query(func.sum(Movimentacao.quantidade)).filter(Movimentacao.item_id==item_id, Movimentacao.tipo=='SAIDA', func.date(Movimentacao.data_movimentacao)==dia).scalar() or 0)

    historico_data = {
        'labels': labels_mov,
        'entradas': entradas,
        'saidas': saidas
    }
    return jsonify(historico_data)

@app.route('/api/item/<int:item_id>/previsao')
@login_required
def api_item_previsao(item_id):
    """
    Gera e retorna uma previsão de consumo (saídas) para um item específico.
    Utiliza um modelo de Suavização Exponencial.
    """
    item_data = get_item_estoque_by_id(item_id)
    if not item_data:
        abort(404)
    item = ItemEstoque(item_data)
    
    # 1. Coletar dados históricos de SAÍDA para o item (Via Supabase Helper)
    historico_saidas_data = get_item_movements_in_period(item_id, days=90, tipo='SAIDA')
    
    if not historico_saidas_data:
        return jsonify({'error': 'Dados históricos de saída insuficientes para previsão.', 'previsao': []}), 404

    # 2. Preparar os dados para o modelo (série temporal diária)
    data_saidas = []
    for mov_dict in historico_saidas_data:
        # Supabase retorna datas como strings ISO
        dt_mov = datetime.fromisoformat(mov_dict.get('data_movimentacao'))
        data_saidas.append({
            'data': dt_mov.date(),
            'quantidade': mov_dict.get('quantidade')
        })
    
    df_saidas = pd.DataFrame(data_saidas)
    df_saidas['data'] = pd.to_datetime(df_saidas['data'])
    
    # Agrupar por dia e somar as quantidades
    df_diario = df_saidas.groupby('data')['quantidade'].sum().reset_index()
    df_diario = df_diario.set_index('data')
    
    # Preencher datas ausentes com 0 para ter uma série temporal contínua
    idx = pd.date_range(df_diario.index.min(), df_diario.index.max())
    df_diario = df_diario.reindex(idx, fill_value=0)
    
    # 3. Gerar previsão usando Regressão Linear Simples (Leve)
    try:
        # Calcular tendência (x: dias, y: quantidades)
        n = len(df_diario)
        if n < 2:
            return jsonify({'item_id': item_id, 'item_descricao': item.descricao, 'previsao': []})

        x = np.arange(n)
        y = df_diario['quantidade'].values
        
        # Coeficientes da regressão linear: y = mx + b
        m, b = np.polyfit(x, y, 1)
        
        # 4. Gerar a previsão para os próximos 15 dias
        dias_para_prever = 15
        ultimo_dia = df_diario.index.max()
        previsao_data = []
        
        for i in range(1, dias_para_prever + 1):
            valor_previsto = m * (n + i - 1) + b
            forecast_date = ultimo_dia + timedelta(days=i)
            previsao_data.append({
                'data': forecast_date.strftime('%Y-%m-%d'),
                'quantidade_prevista': max(0, round(float(valor_previsto), 2))
            })
        
        return jsonify({'item_id': item_id, 'item_descricao': item.descricao, 'previsao': previsao_data})
    except Exception as e:
        print(f"Erro na previsão linear: {e}")
        return jsonify({'error': f'Erro ao gerar previsão: {e}', 'previsao': []}), 500

def _gerar_previsao_para_item(item_id, dias_para_prever):
    """
    Função auxiliar interna para gerar previsão. Não é uma rota.
    Retorna um dicionário com a previsão ou um erro.
    """
    item_data = get_item_estoque_by_id(item_id)
    if not item_data:
        return {'error': 'Item não encontrado.'}

    historico_saidas_data = get_item_movements_in_period(item_id, days=90, tipo='SAIDA')

    if not historico_saidas_data:
        return {'error': 'Dados históricos insuficientes.', 'previsao': []}

    data_saidas = []
    for mov_dict in historico_saidas_data:
        dt_mov = datetime.fromisoformat(mov_dict.get('data_movimentacao'))
        data_saidas.append({'data': dt_mov.date(), 'quantidade': mov_dict.get('quantidade')})

    df_saidas = pd.DataFrame(data_saidas)
    df_saidas['data'] = pd.to_datetime(df_saidas['data'])
    
    df_diario = df_saidas.groupby('data')['quantidade'].sum().reset_index().set_index('data')
    
    idx = pd.date_range(df_diario.index.min(), df_diario.index.max())
    df_diario = df_diario.reindex(idx, fill_value=0)
    
    try:
        n = len(df_diario)
        if n < 2:
            return {'previsao': []}

        x = np.arange(n)
        y = df_diario['quantidade'].values
        m, b = np.polyfit(x, y, 1)
        
        ultimo_dia = df_diario.index.max()
        previsao_data = []
        for i in range(1, dias_para_prever + 1):
            valor_previsto = m * (n + i - 1) + b
            forecast_date = ultimo_dia + timedelta(days=i)
            previsao_data.append({
                'data': forecast_date.strftime('%Y-%m-%d'),
                'quantidade_prevista': max(0, round(float(valor_previsto), 2))
            })
        
        return {'previsao': previsao_data}
    except Exception as e:
        print(f"Erro no modelo de previsão linear interna: {e}")
        return {'error': f'Erro no modelo de previsão: {e}', 'previsao': []}

@app.route('/api/sugestoes-compra')
@login_required
def api_sugestoes_compra():
    """Gera sugestões de compra inteligentes."""
    try:
        sugestoes = []
        # Analisa apenas itens com estoque > 0 para evitar queries em itens abandonados
        # Supabase filter gt
        items_data = select_many('item_estoque', limit=100) # Simplificado, ideal filtrar gt qtd_estoque > 0 no server se fosse muitos
        # Filtro python pq select_many basico nao expoe gt facilmente (podemos usar supabase direto se precisar)
        itens = [ItemEstoque(i) for i in items_data if i.get('qtd_estoque', 0) > 0]

        for item in itens:
            try:
                dias_para_prever = item.tempo_reposicao or 7
                resultado_previsao = _gerar_previsao_para_item(int(item.id), dias_para_prever)
                
                if 'error' in resultado_previsao:
                    continue

                previsao_data = resultado_previsao
                consumo_previsto_total = sum(p['quantidade_prevista'] for p in previsao_data.get('previsao', []))

                estoque_projetado = (item.qtd_estoque or 0) - consumo_previsto_total

                if estoque_projetado < (item.estoque_minimo or 0):
                    if item.estoque_ideal_compra and item.estoque_ideal_compra > 0:
                        quantidade_sugerida = item.estoque_ideal_compra
                    else:
                        quantidade_sugerida = (item.estoque_minimo * 2) - estoque_projetado
                    
                    dias_ate_critico = (item.qtd_estoque - item.estoque_minimo) / (consumo_previsto_total / dias_para_prever) if consumo_previsto_total > 0 else float('inf')
                    data_limite_pedido = date.today() + timedelta(days=max(0, dias_ate_critico))

                    sugestoes.append({
                        'item_id': item.id,
                        'item_descricao': item.descricao,
                        'item_codigo': item.codigo,
                        'quantidade_sugerida': round(quantidade_sugerida, 2),
                        'data_limite_pedido': data_limite_pedido.strftime('%d/%m/%Y')
                    })
            except Exception as e:
                print(f"Erro ao processar item {item.id}: {str(e)}")
                continue

        sugestoes_ordenadas = sorted(sugestoes, key=lambda x: datetime.strptime(x['data_limite_pedido'], '%d/%m/%Y'))
        return jsonify(sugestoes_ordenadas)
    
    except Exception as e:
        print(f"Erro geral em api_sugestoes_compra: {str(e)}")
        return jsonify([])

@app.route('/api/stock-turnover-data')
@login_required
def api_stock_turnover_data():
    """Giro de estoque."""
    items_data = select_many('item_estoque', limit=200) # Limite aumentado
    itens = [ItemEstoque(i) for i in items_data if i.get('qtd_estoque', 0) > 0]
    
    itens_com_giro = []
    
    for item in itens:
        # Busca saídas nos últimos 90 dias
        moves = get_item_movements_in_period(int(item.id), days=90, tipo='SAIDA')
        total_saidas_periodo = sum(m.get('quantidade', 0) for m in moves)

        giro_estoque = 0
        if item.qtd_estoque > 0: # Evita divisão por zero
            giro_estoque = total_saidas_periodo / item.qtd_estoque
        
        itens_com_giro.append({
            'id': item.id,
            'descricao': item.descricao,
            'codigo': item.codigo,
            'giro_estoque': round(giro_estoque, 2),
            'qtd_estoque': item.qtd_estoque,
            'total_saidas': total_saidas_periodo
        })
    
    itens_com_giro_ordenado = sorted(itens_com_giro, key=lambda x: x['giro_estoque'])
    return jsonify(itens_com_giro_ordenado[:10])

@app.route('/')
@login_required
def index():
    """Redireciona a rota raiz para o novo dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/cadastro', methods=['GET', 'POST'])
@admin_only
@login_required
def cadastro():
    """Página para cadastrar um novo item no estoque."""
    if request.method == 'POST':
        # Coleta os dados do formulário
        codigo = request.form['codigo']
        descricao = request.form['descricao']
        
        qtd_entrada = request.form.get('qtd_estoque')
        lote = request.form.get('lote')
        item_nf = request.form.get('item_nf')
        nf = request.form.get('nf')
        validade_str = request.form.get('validade')
        
        if not codigo or not descricao:
            flash('Código e Descrição são campos obrigatórios para o item!', 'danger')
            return redirect(url_for('cadastro'))
        
        if not qtd_entrada or not lote or not item_nf:
            flash('Quantidade, Lote e Item NF são campos obrigatórios para a entrada inicial!', 'danger')
            return redirect(url_for('cadastro'))

        try:
            qtd_entrada = float(qtd_entrada)
            if qtd_entrada <= 0:
                flash('A quantidade de entrada deve ser um número inteiro positivo.', 'danger')
                return redirect(url_for('cadastro'))
        except (ValueError, TypeError):
            flash('A quantidade de entrada deve ser um número válido.', 'danger')
            return redirect(url_for('cadastro'))

        # Verifica duplicidade
        if get_item_estoque_by_codigo(codigo):
            flash(f'Item com o código "{codigo}" já existe no estoque.', 'warning')
            return redirect(url_for('cadastro'))

        validade = validade_str if validade_str else None

        # --- INÍCIO TRANSAÇÃO MANUAL ---
        created_item = None
        
        try:
            # 1. Cria ItemEstoque
            item_data = {
                'codigo': codigo,
                'endereco': request.form.get('endereco'),
                'codigo_opcional': request.form.get('codigo_opcional'),
                'tipo': request.form.get('tipo'),
                'descricao': descricao,
                'un': request.form.get('un'),
                'dimensao': request.form.get('dimensao'),
                'estoque_minimo': float(request.form.get('estoque_minimo', 5)),
                'estoque_ideal_compra': float(request.form.get('estoque_ideal_compra', 0)) if request.form.get('estoque_ideal_compra') else None,
                'cliente': request.form.get('cliente'),
                'qtd_estoque': qtd_entrada, # Já inicializa com a qtd
                'tempo_reposicao': int(request.form.get('tempo_reposicao', 7))
            }
            
            created_item = create_item_estoque(item_data)
            if not created_item:
                 raise Exception("Falha ao criar ItemEstoque")
                 
            item_id = created_item['id']

            # 2. Cria EstoqueDetalhe
            detalhe_data = {
                'item_estoque_id': item_id,
                'lote': lote,
                'item_nf': item_nf,
                'nf': nf,
                'validade': validade,
                'estacao': 'Almoxarifado',
                'quantidade': qtd_entrada
            }
            if not create_estoque_detalhe(detalhe_data):
                raise Exception("Falha ao criar EstoqueDetalhe")

            # 3. Cria Movimentacao
            mov_data = {
                'item_id': item_id,
                'tipo': 'ENTRADA',
                'quantidade': qtd_entrada,
                'lote': lote,
                'item_nf': item_nf,
                'nf': nf,
                'usuario': current_user.username if hasattr(current_user, 'username') else 'admin',
                'etapa': 'CADASTRO',
                'observacao': 'Entrada inicial via cadastro de novo item.'
            }
            create_movimentacao(mov_data)

            flash('Item e seu primeiro lote cadastrados com sucesso!', 'success')
            
        except Exception as e:
            # Rollback Manual (compensating transaction)
            if created_item:
                print(f"⚠️ Rolling back item {created_item['id']} due to error: {e}")
                delete_item_estoque(created_item['id'])
                
            flash(f'Erro ao cadastrar o item e lote: {e}', 'danger')
        
        return redirect(url_for('estoque'))

    return render_template('cadastro.html')

@app.route('/controle_validade')
@login_required
def controle_validade():
    """Etiqueta Vermelha: Itens vencendo nos próximos 40 dias."""
    hoje = date.today()
    
    # helper: busca PENDENTES ou NULL, com qtd > 0
    lotes_data = get_etiqueta_vermelha_items(days=40)
    lotes_criticos = [EstoqueDetalhe(l) for l in lotes_data]
    
    return render_template('controle_validade.html', 
                           lotes=lotes_criticos, 
                           today_date=hoje, 
                           title="Controle de Validade")

@app.route('/controle_validade/marcar_concluido/<int:lote_id>', methods=['POST'])
@login_required
def marcar_validade_concluido(lote_id):
    """Marca um item como 'CONCLUÍDO'."""
    try:
        # Verifica existência (opcional, update retornaria erro ou nada)
        detalhe = get_estoque_detalhe_by_id(lote_id)
        if not detalhe:
            return jsonify({'success': False, 'message': 'Lote não encontrado'}), 404

        update_data = {
            'status_etiqueta': 'CONCLUÍDO',
            'data_etiqueta': datetime.now().isoformat(),
            'usuario_etiqueta': current_user.username
        }
        update_estoque_detalhe(lote_id, update_data)
        
        return jsonify({'success': True, 'message': 'Item marcado como concluído!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/controle_validade/historico')
@login_required
def historico_validade():
    """Histórico de itens já etiquetados."""
    hoje = date.today()
    
    lotes_data = get_historico_etiquetas(limit=500)
    lotes_concluidos = [EstoqueDetalhe(l) for l in lotes_data]
    
    return render_template('controle_validade_historico.html', 
                           lotes=lotes_concluidos, 
                           today_date=hoje, 
                           title="Histórico de Etiquetas")

@app.route('/controle_validade/reabrir/<int:lote_id>', methods=['POST'])
@admin_only
@login_required
def reabrir_validade(lote_id):
    """Reabre um item concluído."""
    try:
        update_data = {
            'status_etiqueta': 'PENDENTE',
            'data_etiqueta': None,
            'usuario_etiqueta': None
        }
        update_estoque_detalhe(lote_id, update_data)
        flash('Item reaberto com sucesso. Ele voltou para a lista de pendências.', 'success')
    except Exception as e:
        flash(f'Erro ao reabrir item: {e}', 'danger')
        
    return redirect(url_for('historico_validade'))

@app.route('/controle_validade/exportar')
@admin_only
@login_required
def exportar_validade():
    """Exporta lista para Excel."""
    tipo = request.args.get('tipo', 'pendente')
    hoje = date.today()
    output = io.BytesIO()
    
    if tipo == 'historico':
        lotes_data = get_historico_etiquetas(limit=1000)
        filename = f"Historico_Etiquetas_{hoje.strftime('%Y-%m-%d')}.xlsx"
    else:
        lotes_data = get_etiqueta_vermelha_items(days=40)
        filename = f"Pendencias_Etiquetas_{hoje.strftime('%Y-%m-%d')}.xlsx"
        
    lotes = [EstoqueDetalhe(l) for l in lotes_data]
    
    data = []
    for lote in lotes:
        validade_dt = datetime.strptime(lote.validade, '%Y-%m-%d').date() if lote.validade else None
        dias_para_vencer = (validade_dt - hoje).days if validade_dt else 0
        
        # Acessa item_estoque via property wrapper
        item = lote.item_estoque # Garante acesso a .codigo, .descricao
        
        row = {
            'Código': item.codigo if item else '-',
            'Descrição': item.descricao if item else '-',
            'Lote': lote.lote,
            'Local': f"{item.endereco or '-' if item else '-'} / {lote.estacao or '-'}",
            'Validade': validade_dt.strftime('%d/%m/%Y') if validade_dt else '-',
            'Dias Vencimento': dias_para_vencer,
            'Quantidade': lote.quantidade,
            'Status Etiqueta': lote.status_etiqueta or 'PENDENTE'
        }
        
        if tipo == 'historico':
            row['Data Etiqueta'] = datetime.fromisoformat(lote.data_etiqueta).strftime('%d/%m/%Y %H:%M') if lote.data_etiqueta else '-'
            row['Resp. Etiqueta'] = lote.usuario_etiqueta or '-'
            
        data.append(row)
        
    df = pd.DataFrame(data)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Controle Validade')
        workbook = writer.book
        worksheet = writer.sheets['Controle Validade']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 20)
            worksheet.write(0, i, col, header_format)
            
    output.seek(0)
    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

@app.route('/controle_validade/imprimir')
@admin_only
@login_required
def imprimir_validade():
    """Versão de impressão (PENDENTES)."""
    hoje = date.today()
    lotes_data = get_etiqueta_vermelha_items(days=40)
    lotes_criticos = [EstoqueDetalhe(l) for l in lotes_data]
    
    return render_template('print_validade.html', 
                           lotes=lotes_criticos, 
                           today_date=hoje)

@app.route('/estoque')
@login_required
def estoque():
    """
    Página para listar todos os lotes detalhados do estoque.
    """
    search_query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    items, total = get_estoque_detalhado(page=page, per_page=per_page, search_term=search_query)
    
    # Envolve em objetos EstoqueDetalhe
    lotes_detalhados = [EstoqueDetalhe(i) for i in items]
    
    # Cria objeto de paginação compatível com a template (classe Pagination definida em models.py)
    pagination = Pagination(lotes_detalhados, page, per_page, total)
    
    # Como a classe Pagination popula .items, podemos passar pagination.items ou a lista direta
    # O template 'estoque.html' provavelmente itera sobre `lotes_detalhados` ou `pagination.items`?
    # No código original: lotes_detalhados = pagination.items -> template recebe lotes_detalhados
    # E pagination recebe pagination.
    
    return render_template('estoque.html',
                           lotes_detalhados=lotes_detalhados,
                           search_query=search_query,
                           pagination=pagination,
                           today_date=date.today(),
                           timedelta=timedelta)

@app.route('/item/editar/<int:item_id>', methods=['GET', 'POST'])
@admin_only
@login_required
def editar_item(item_id):
    """Página para editar um item existente."""
    item_data = get_item_estoque_by_id(item_id)
    if not item_data:
        abort(404)
    item = ItemEstoque(item_data)

    if request.method == 'POST':
        # Coleta os dados validações
        codigo = request.form['codigo']
        descricao = request.form['descricao']

        if not codigo or not descricao:
            flash('Código e Descrição são campos obrigatórios!', 'danger')
            return render_template('editar_item.html', item=item)

        # Verifica duplicidade
        existing = get_item_estoque_by_codigo(codigo)
        if existing and str(existing['id']) != str(item_id):
            flash(f'O código "{codigo}" já está em uso por outro item.', 'warning')
            return render_template('editar_item.html', item=item)

        update_data = {
            'codigo': codigo,
            'descricao': descricao,
            'endereco': request.form.get('endereco'),
            'codigo_opcional': request.form.get('codigo_opcional'),
            'tipo': request.form.get('tipo'),
            'un': request.form.get('un'),
            'dimensao': request.form.get('dimensao'),
            'estoque_minimo': float(request.form.get('estoque_minimo', 5)),
            'estoque_ideal_compra': float(request.form.get('estoque_ideal_compra', 0)) if request.form.get('estoque_ideal_compra') else None,
            'tempo_reposicao': int(request.form.get('tempo_reposicao', 7)),
            'cliente': request.form.get('cliente')
        }

        try:
            update_item_estoque(item_id, update_data)
            flash('Item atualizado com sucesso!', 'success')
            return redirect(url_for('estoque'))
        except Exception as e:
            flash(f'Erro ao atualizar o item: {e}', 'danger')

    return render_template('editar_item.html', item=item)

@app.route('/item/excluir/<int:item_id>')
@admin_required
@login_required
def excluir_item(item_id):
    """Rota para excluir um item do estoque."""
    # Supabase faz cascade se configurado, ou precisamos deletar related?
    # Vamos assumir que o banco tem FK on delete cascade ou deletar manual.
    # Safe delete manual: deleta movimentacoes, detalhes, depois item.
    # Mas se tabela tiver on delete cascade é auto.
    # Vamos tentar deletar direto.
    item_data = get_item_estoque_by_id(item_id)
    if not item_data:
        abort(404)
        
    try:
        # Tenta deletar item (cascade deve tratar o resto se configurado, se não, vai dar erro FK)
        # Se der erro, implementamos delete manual dos filhos.
        # Supabase helpers geralmente não retornam status se vazio, mas lançam exceção se erro.
        success = delete_item_estoque(item_id)
        if hasattr(success, 'error') and success.error:
             raise Exception(success.error.message)
             
        flash(f'Item "{item_data.get("descricao")}" excluído com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao excluir item: {str(e)}. Verifique dependências.', 'danger')
        
    return redirect(url_for('estoque'))

@app.route('/movimentacao', methods=['GET', 'POST'])
@admin_only
@login_required
def movimentacao():
    """Página para registrar uma nova movimentação de estoque."""
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        tipo = request.form.get('tipo')
        etapa = request.form.get('etapa')
        observacao = request.form.get('observacao')
        
        if not item_id or not tipo:
            flash('Item ou tipo de movimentação inválido.', 'danger')
            return redirect(url_for('movimentacao'))

        item_data = get_item_estoque_by_id(item_id)
        if not item_data:
            abort(404)
        item = ItemEstoque(item_data)

        if not etapa:
            flash('O campo Etapa de Destino é obrigatório.', 'danger')
            return redirect(url_for('movimentacao'))

        try:
            quantidade = float(request.form.get('quantidade'))
            if quantidade <= 0:
                flash('A quantidade deve ser um número positivo.', 'danger')
                return redirect(url_for('movimentacao'))
        except (ValueError, TypeError):
            flash('A quantidade deve ser um número válido.', 'danger')
            return redirect(url_for('movimentacao'))

        try:
            # --- LÓGICA DE ENTRADA ---
            if tipo == 'ENTRADA':
                lote = request.form.get('lote')
                item_nf = request.form.get('item_nf')
                nf = request.form.get('nf')
                if not lote or not item_nf:
                    flash('Lote e Item NF são obrigatórios para entrada.', 'danger')
                    return redirect(url_for('movimentacao'))

                # Verifica se já existe um detalhe com a mesma combinação de lote, item_nf e nf
                # Usando select_many com filtros
                filters = {'item_estoque_id': item.id, 'lote': lote, 'item_nf': item_nf, 'nf': nf}
                existing_details = select_many('estoque_detalhe', filters=filters)
                detalhe_existente = existing_details[0] if existing_details else None
                
                if detalhe_existente:
                    # Se existe, apenas soma a quantidade
                    nova_qtd = float(detalhe_existente['quantidade']) + quantidade
                    update_estoque_detalhe(detalhe_existente['id'], {'quantidade': nova_qtd})
                else:
                    # Se não existe, cria um novo
                    validade_str = request.form.get('validade')

                    # Lógica para determinar a estação automaticamente
                    # Busca último detalhe do item order by entrada desc
                    last_details = select_many('estoque_detalhe', filters={'item_estoque_id': item.id}, order_by='-data_entrada', limit=1)
                    
                    ultimo_detalhe = last_details[0] if last_details else None
                    estacao_automatica = ultimo_detalhe.get('estacao') if ultimo_detalhe and ultimo_detalhe.get('estacao') else 'Almoxarifado'

                    novo_detalhe = {
                        'item_estoque_id': item.id,
                        'lote': lote,
                        'item_nf': item_nf,
                        'nf': nf,
                        'validade': validade_str if validade_str else None,
                        'estacao': estacao_automatica,
                        'quantidade': quantidade
                    }
                    create_estoque_detalhe(novo_detalhe)

                # Atualiza o total
                nova_qtd_total = float(item.qtd_estoque or 0) + quantidade
                update_item_estoque(item.id, {'qtd_estoque': nova_qtd_total})

                mov_data = {
                    'item_id': item.id, 
                    'tipo': 'ENTRADA', 
                    'quantidade': quantidade, 
                    'lote': lote, 
                    'item_nf': item_nf,
                    'nf': nf,
                    'usuario': current_user.username,
                    'etapa': etapa,
                    'observacao': observacao
                }
                create_movimentacao(mov_data)
                
                socketio.emit('dashboard_update', {'message': 'Nova entrada registrada!'})
                flash('Entrada registrada com sucesso!', 'success')

            # --- LÓGICA DE SAÍDA ---
            elif tipo == 'SAIDA':
                detalhe_id = request.form.get('detalhe_id')
                if not detalhe_id:
                    flash('É necessário selecionar um Lote/Item NF para a saída.', 'danger')
                    return redirect(url_for('movimentacao'))

                detalhe_estoque = get_estoque_detalhe_by_id(detalhe_id)

                if not detalhe_estoque or detalhe_estoque.get('item_estoque_id') != item.id:
                    flash('Lote/Item NF inválido para este item.', 'danger')
                    return redirect(url_for('movimentacao'))
                
                qtd_disponivel = float(detalhe_estoque['quantidade'])
                if qtd_disponivel < quantidade:
                    flash(f'Quantidade insuficiente no lote selecionado. Disponível: {qtd_disponivel}', 'danger')
                    return redirect(url_for('movimentacao'))

                # Subtrai a quantidade
                update_estoque_detalhe(detalhe_id, {'quantidade': qtd_disponivel - quantidade})
                new_total = float(item.qtd_estoque or 0) - quantidade
                update_item_estoque(item.id, {'qtd_estoque': new_total})

                mov_data = {
                    'item_id': item.id, 
                    'tipo': 'SAIDA', 
                    'quantidade': quantidade, 
                    'lote': detalhe_estoque.get('lote'), 
                    'item_nf': detalhe_estoque.get('item_nf'),
                    'nf': detalhe_estoque.get('nf'),
                    'usuario': current_user.username,
                    'etapa': etapa,
                    'observacao': observacao
                }
                create_movimentacao(mov_data)
                
                socketio.emit('dashboard_update', {'message': 'Nova saída registrada!'})
                flash('Saída registrada com sucesso!', 'success')
                
        except Exception as e:
             flash(f'Erro ao registrar movimentação: {e}', 'danger')

        return redirect(url_for('movimentacao'))

    # Para o método GET (carregamento da página)
    return render_template('movimentacao.html')

@app.route('/historico/<int:item_id>')
@admin_only
@login_required
def historico(item_id):
    """Página para exibir o histórico de movimentações de um item."""
    item_data = get_item_estoque_by_id(item_id)
    if not item_data:
        abort(404)
    item = ItemEstoque(item_data)
    
    # helper order by desc
    movs_data = get_item_movements_by_item_id(item_id)
    movimentacoes = [Movimentacao(m) for m in movs_data]
    
    return render_template('historico.html', item=item, movimentacoes=movimentacoes)

@app.route('/item/<int:item_id>/lotes-detalhes')
@login_required
def detalhes_lotes(item_id):
    """Página para exibir todos os detalhes de lote de um item."""
    filtro_ativo = request.args.get('filtro')
    
    item_data = get_item_estoque_by_id(item_id)
    if not item_data:
        abort(404)
    item = ItemEstoque(item_data)

    is_critico = (filtro_ativo == 'critico')
    detalhes_data = get_detalhes_by_item(item_id, filtro_critico=is_critico)
    
    detalhes_query = [EstoqueDetalhe(d) for d in detalhes_data]

    return render_template('detalhes_lotes.html',
                          item=item,
                          detalhes=detalhes_query,
                          filtro_ativo=filtro_ativo)
 
@app.route('/lote/editar/<int:detalhe_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def editar_lote(detalhe_id):
    """Página para editar os dados de um lote específico."""
    detalhe_data = get_estoque_detalhe_by_id(detalhe_id)
    if not detalhe_data:
        abort(404)
    detalhe = EstoqueDetalhe(detalhe_data)
    
    # Fetch item associated
    item_data = get_item_estoque_by_id(detalhe.item_estoque_id)
    item = ItemEstoque(item_data) if item_data else None

    if request.method == 'POST':
        try:
            # --- Coleta e Validação ---
            nova_quantidade_str = request.form.get('quantidade')
            observacao = request.form.get('observacao')
            novo_endereco = request.form.get('endereco')

            if not nova_quantidade_str or not observacao:
                flash('A Nova Quantidade e o Motivo da Edição são obrigatórios.', 'danger')
                return render_template('editar_lote.html', detalhe=detalhe)

            try:
                nova_quantidade = float(nova_quantidade_str)
            except ValueError:
                flash('Quantidade inválida.', 'danger')
                return render_template('editar_lote.html', detalhe=detalhe)

            if nova_quantidade < 0:
                flash('A quantidade não pode ser negativa.', 'danger')
                return render_template('editar_lote.html', detalhe=detalhe)

            # --- Cálculo do Ajuste ---
            quantidade_antiga = float(detalhe.quantidade or 0)
            diferenca_qtd = nova_quantidade - quantidade_antiga

            # --- Prepare updates ---
            validade_str = request.form.get('validade')
            update_detalhe_data = {
                'lote': request.form.get('lote'),
                'nf': request.form.get('nf'),
                'item_nf': request.form.get('item_nf'),
                'validade': validade_str if validade_str else None,
                'estacao': request.form.get('estacao'),
                'quantidade': nova_quantidade
            }
            
            # Atualiza o detalhe
            update_estoque_detalhe(detalhe_id, update_detalhe_data)
            
            # Atualiza o item: endereço e total
            # Total += diferenca
            novo_total_item = float(item.qtd_estoque or 0) + diferenca_qtd
            update_item_data = {
                'endereco': novo_endereco,
                'qtd_estoque': novo_total_item
            }
            update_item_estoque(item.id, update_item_data)

            # --- Registro da Movimentação de Ajuste ---
            tipo_ajuste = 'AJUSTE-ENTRADA' if diferenca_qtd > 0 else 'AJUSTE-SAIDA'
            qtd_movimentacao = abs(diferenca_qtd)

            if qtd_movimentacao > 0:
                mov_data = {
                    'item_id': item.id,
                    'tipo': tipo_ajuste,
                    'quantidade': qtd_movimentacao,
                    'lote': request.form.get('lote'),
                    'item_nf': request.form.get('item_nf'),
                    'nf': request.form.get('nf'),
                    'usuario': current_user.username,
                    'etapa': 'AJUSTE',
                    'observacao': f"Ajuste manual. Motivo: {observacao}. Qtd anterior: {quantidade_antiga}, Qtd nova: {nova_quantidade}."
                }
                create_movimentacao(mov_data)

            flash('Lote editado com sucesso! O histórico de movimentação foi atualizado.', 'success')
            return redirect(url_for('detalhes_lotes', item_id=item.id))

        except Exception as e:
            flash(f'Ocorreu um erro ao tentar editar o lote: {e}', 'danger')

    return render_template('editar_lote.html', detalhe=detalhe)

def _calcular_quantidade_recebida(detalhe_lote):
    """
    Calcula a quantidade total recebida para um lote específico (detalhe).
    Soma todas as movimentações de ENTRADA e AJUSTE-ENTRADA.
    """
    total_recebido = db.session.query(func.sum(Movimentacao.quantidade)).filter(
        Movimentacao.item_id == detalhe_lote.item_estoque_id,
        Movimentacao.lote == detalhe_lote.lote,
        Movimentacao.nf == detalhe_lote.nf, # Adicionado para garantir a unicidade
        or_(
            Movimentacao.tipo == 'ENTRADA',
            Movimentacao.tipo == 'AJUSTE-ENTRADA'
        )
    ).scalar()

    return total_recebido or 0

@app.route('/lote/excluir/<int:detalhe_id>')
@admin_required
@login_required
def excluir_lote(detalhe_id):
    """
    Exclui um lote e remove movimentações (Safe Delete Manual).
    """
    detalhe_data = get_estoque_detalhe_by_id(detalhe_id)
    if not detalhe_data:
        abort(404)
    item_id = detalhe_data['item_estoque_id']
    item_data = get_item_estoque_by_id(item_id)
    
    try:
        qtd_lote = float(detalhe_data['quantidade'] or 0)
        
        # 1. Remove movimentações (se possível filtrar pelo lote/nf/item_nf/item_id)
        # Filtro: item_id, lote, item_nf, nf
        supabase.table('movimentacao').delete().match({
            'item_id': item_id,
            'lote': detalhe_data['lote'],
            'nf': detalhe_data['nf'], # Importante
            # item_nf as vezes é vazio, supabase match pode falhar se vazio?
        }).execute()
        # Se item_nf for relevante:
        # Mas vamos simplificar: o ideal é remover tudo que bate com o lote.
        
        # 2. Ajusta estoque do item
        # Só se o item ainda existir
        if item_data:
            current_total = float(item_data.get('qtd_estoque') or 0)
            new_total = max(0, current_total - qtd_lote)
            update_item_estoque(item_id, {'qtd_estoque': new_total})
            
        # 3. Remove o detalhe
        delete_estoque_detalhe(detalhe_id)
        
        flash('Lote excluído com sucesso.', 'success')
        
    except Exception as e:
        flash(f'Erro ao excluir o lote: {e}', 'danger')
    
    return redirect(url_for('detalhes_lotes', item_id=item_id))

@app.route('/movimentacao/excluir/<int:mov_id>')
@admin_required
@login_required
def excluir_movimentacao(mov_id):
    """
    Exclui (reverte) uma movimentação de estoque.
    """
    try:
        mov_response = supabase.table('movimentacao').select('*, item_estoque(*)').eq('id', mov_id).execute()
        mov = mov_response.data[0] if mov_response.data else None
        
        if not mov:
            abort(404)
            
        item_id = mov['item_id'] # ou item_estoque.id
        quantidade_mov = float(mov['quantidade'])
        
        # Encontra lote
        filters = {'item_estoque_id': item_id, 'lote': mov['lote'], 'nf': mov['nf']}
        detalhes = select_many('estoque_detalhe', filters=filters, limit=1)
        detalhe_lote = detalhes[0] if detalhes else None
        
        # Item total
        item_data = mov['item_estoque'] # joined data
        current_item_qtd = float(item_data['qtd_estoque'] or 0)
        
        if 'ENTRADA' in mov['tipo']:
            # Reverte ENTRADA -> Subtrai
            novo_total = max(0, current_item_qtd - quantidade_mov)
            update_item_estoque(item_id, {'qtd_estoque': novo_total})
            
            if detalhe_lote:
                old_qtd = float(detalhe_lote['quantidade'])
                update_estoque_detalhe(detalhe_lote['id'], {'quantidade': max(0, old_qtd - quantidade_mov)})
                
        elif 'SAIDA' in mov['tipo']:
             # Reverte SAIDA -> Soma
            novo_total = current_item_qtd + quantidade_mov
            update_item_estoque(item_id, {'qtd_estoque': novo_total})
            
            if detalhe_lote:
                old_qtd = float(detalhe_lote['quantidade'])
                update_estoque_detalhe(detalhe_lote['id'], {'quantidade': old_qtd + quantidade_mov})
            else:
                flash('Aviso: O lote original não foi encontrado. O estoque total foi ajustado.', 'warning')
        
        # Delete mov
        delete_movimentacao(mov_id)
        flash(f'Movimentação ID {mov_id} revertida com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao reverter movimentação: {e}', 'danger')

    return redirect(request.referrer or url_for('relatorio_movimentacoes'))


@app.route('/movimentacao/apagar/<int:mov_id>')
@admin_required
@login_required
def apagar_movimentacao(mov_id):
    """
    Apaga um registro de movimentação SEM afetar o estoque.
    """
    try:
        delete_movimentacao(mov_id)
        flash(f'Linha de movimentação ID {mov_id} apagada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao apagar a movimentação: {e}', 'danger')

    return redirect(request.referrer or url_for('relatorio_movimentacoes'))

# --- ROTAS DE API INTERNA (para JavaScript) ---

@app.route('/api/item/by-code/<string:codigo>')
@login_required
def api_get_item_by_code(codigo):
    """Retorna os dados de um item pelo seu código em formato JSON."""
    item = get_item_estoque_by_codigo(codigo)
    if not item:
        return jsonify({'error': 'Item não encontrado'}), 404
    return api_get_item(item['id'])

@app.route('/api/item/<int:item_id>')
@login_required
def api_get_item(item_id):
    """Retorna os dados de um item em formato JSON."""
    item = get_item_estoque_by_id(item_id)
    if not item:
        abort(404)
        
    # Compatibilidade com campos esperados
    return jsonify({
        'id': item['id'],
        'codigo': item['codigo'],
        'descricao': item['descricao'],
        'un': item.get('un'),
        'dimensao': item.get('dimensao'),
        'cliente': item.get('cliente')
    })

@app.route('/api/item/<int:item_id>/lotes')
@login_required
def api_get_lotes(item_id):
    """
    Retorna JSON de lotes (FEFO/FIFO).
    """
    item = get_item_estoque_by_id(item_id)
    if not item:
        abort(404)
        
    detalhes_data = get_detalhes_by_item(item_id) # Ordenado por data_entrada desc
    
    # Sorting logic in Python
    # Hardware/Painel -> FIFO (Order by Data Entrada ASC)
    # Others -> FEFO (Order by Validade ASC, nulls last)
    
    tipo_item = (item.get('tipo') or '').lower()
    
    if tipo_item in ['hardware', 'painel']:
        # Sort by data_entrada ASC (oldest first)
        detalhes_data.sort(key=lambda x: x.get('data_entrada') or '9999-12-31')
    else:
        # Validates ASC. Handle None.
        def validade_key(x):
            v = x.get('validade')
            return v if v else '9999-12-31'
        
        # Sort by validade, then data_entrada
        detalhes_data.sort(key=lambda x: (validade_key(x), x.get('data_entrada') or ''))

    lotes = []
    for d in detalhes_data:
        val_str = 'N/A'
        if d.get('validade'):
             val_str = datetime.strptime(d['validade'], '%Y-%m-%d').strftime('%d/%m/%Y')
             
        lotes.append({
            'id': d['id'], 
            'lote': d['lote'], 
            'item_nf': d['item_nf'], 
            'quantidade': d['quantidade'], 
            'validade': val_str
        })
        
    return jsonify(lotes)

@app.route('/importar', methods=['GET', 'POST'])
@admin_required
@login_required
def importar():
    """Página e lógica para importar dados de uma planilha Excel."""
    if request.method == 'POST':
        if 'arquivo_excel' not in request.files:
            flash('Nenhum arquivo selecionado!', 'danger')
            return redirect(request.url)
        
        file = request.files['arquivo_excel']
        if file.filename == '':
            flash('Nenhum arquivo selecionado!', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
                
                required_columns = ['CÓDIGO', 'DESCRIÇÃO', 'LOTE', 'NF', 'QTD ESTOQUE']
                if not all(col in df.columns for col in required_columns):
                    flash(f'A planilha deve conter as colunas obrigatórias: {", ".join(required_columns)}', 'danger')
                    return redirect(request.url)

                sucesso_count = 0
                erro_count = 0
                
                for index, row in df.iterrows():
                    codigo = str(row['CÓDIGO']) if pd.notna(row['CÓDIGO']) else None
                    if not codigo:
                        erro_count += 1
                        continue

                    descricao = str(row['DESCRIÇÃO']) if pd.notna(row['DESCRIÇÃO']) else 'Sem Descrição'
                    lote = str(row['LOTE']) if pd.notna(row['LOTE']) else 'N/A'
                    nf = str(row.get('NF')) if pd.notna(row.get('NF')) else 'N/A'
                    qtd_entrada = float(row['QTD ESTOQUE']) if pd.notna(row['QTD ESTOQUE']) else 0

                    # 1. Busca ou Cria Item
                    item = get_item_estoque_by_codigo(codigo)
                    if not item:
                        # Cria novo item
                        new_item_data = {
                            'codigo': codigo,
                            'descricao': descricao,
                            'endereco': str(row.get('LOCAL', '')) if pd.notna(row.get('LOCAL')) else '',
                            'codigo_opcional': str(row.get('CÓDIGO OPCIONAL', '')) if pd.notna(row.get('CÓDIGO OPCIONAL')) else '',
                            'tipo': str(row.get('TIPO', '')) if pd.notna(row.get('TIPO')) else '',
                            'un': str(row.get('UN.', '')) if pd.notna(row.get('UN.')) else '',
                            'dimensao': str(row.get('DIMENSÃO', '')) if pd.notna(row.get('DIMENSÃO')) else '',
                            'cliente': str(row.get('CLIENTE', '')) if pd.notna(row.get('CLIENTE')) else '',
                            'qtd_estoque': 0
                        }
                        # response.data[0]
                        res = create_item_estoque(new_item_data)
                        if res and hasattr(res, 'data') and res.data:
                             item = res.data[0]
                        else:
                             # Fallback check if created
                             item = get_item_estoque_by_codigo(codigo)

                    if not item:
                         erro_count += 1
                         continue
                         
                    item_id = item['id']
                    
                    # 2. Busca ou Cria Detalhe (Lote)
                    item_nf = str(row.get('ITEM NF')) if pd.notna(row.get('ITEM NF')) else 'N/A'
                    
                    filters = {'item_estoque_id': item_id, 'lote': lote, 'item_nf': item_nf, 'nf': nf}
                    existing_details = select_many('estoque_detalhe', filters=filters, limit=1)
                    detalhe_existente = existing_details[0] if existing_details else None
                    
                    if detalhe_existente:
                        novo_qtd_lote = float(detalhe_existente['quantidade']) + qtd_entrada
                        update_estoque_detalhe(detalhe_existente['id'], {'quantidade': novo_qtd_lote})
                    else:
                        validade_val = row.get('VALIDADE')
                        validade_dt = None
                        if pd.notna(validade_val):
                             try:
                                 validade_dt = pd.to_datetime(validade_val).strftime('%Y-%m-%d')
                             except:
                                 validade_dt = None
                                 
                        novo_detalhe = {
                            'item_estoque_id': item_id,
                            'lote': lote,
                            'item_nf': item_nf,
                            'nf': nf,
                            'validade': validade_dt,
                            'estacao': str(row.get('ESTAÇÃO', '')) if pd.notna(row.get('ESTAÇÃO')) else '',
                            'quantidade': qtd_entrada
                        }
                        create_estoque_detalhe(novo_detalhe)
                    
                    # 3. Atualiza Item Total
                    current_total = float(item.get('qtd_estoque') or 0)
                    update_item_estoque(item_id, {'qtd_estoque': current_total + qtd_entrada})
                    
                    # 4. Cria Movimentacao
                    mov_data = {
                        'item_id': item_id, 
                        'tipo': 'ENTRADA', 
                        'quantidade': qtd_entrada, 
                        'lote': lote, 
                        'nf': nf,
                        'item_nf': str(row.get('ITEM NF', 'N/A')), 
                        'usuario': current_user.username,
                        'etapa': 'IMPORTACAO',
                        'observacao': 'Importação via Excel'
                    }
                    create_movimentacao(mov_data)
                    sucesso_count += 1

                flash(f'Importação concluída! {sucesso_count} registros processados com sucesso. {erro_count} linhas ignoradas.', 'success')

            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
                return redirect(request.url)

            return redirect(url_for('estoque'))

        else:
            flash('Formato de arquivo inválido. Por favor, envie um arquivo .xlsx', 'danger')
            return redirect(request.url)

    return render_template('importar.html')

@app.route('/exportar/excel')
@login_required
def exportar_excel():
    """
    Exporta um relatório detalhado do estoque para Excel.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Font, Alignment
        from openpyxl.utils import get_column_letter
        
        colunas_ordem = [
            'CÓDIGO', 'CÓDIGO OPCIONAL', 'TIPO', 'DESCRIÇÃO',
            'LOCAL', 'UN', 'DIMENSÃO', 'CLIENTE',
            'LOTE', 'ITEM NF', 'NF',
            'VALIDADE', 'ESTAÇÃO', 'QTD ESTOQUE', 'DATA ENTRADA'
        ]
        
        # Busca dados do Supabase (join detalhe -> item)
        # Atenção: Fetching all could be slow if huge.
        response = supabase.table('estoque_detalhe') \
            .select('*, item_estoque(*)') \
            .order('data_entrada', desc=False) \
            .execute()
        
        detalhes = response.data if response.data else []
        
        # Ordenação secundária no Python se necessário (CÓDIGO, DATA)
        # Mas 'item_estoque.codigo' não é campo direto para orderby no supabase (requires relational sort syntax sometimes complex).
        # Vamos ordenar em Python.
        detalhes.sort(key=lambda x: (
            (x.get('item_estoque') or {}).get('codigo', ''), 
            x.get('data_entrada', '')
        ))

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = 'Estoque_Detalhado'
        
        # Cabeçalho
        for num_coluna, nome_coluna in enumerate(colunas_ordem, start=1):
            célula = worksheet.cell(row=1, column=num_coluna)
            célula.value = nome_coluna
            célula.fill = PatternFill(start_color='00D4FF', end_color='00D4FF', fill_type='solid')
            célula.font = Font(bold=True, color='FFFFFF', size=11)
            célula.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Dados
        for num_linha, detalhe in enumerate(detalhes, start=2):
            item = detalhe.get('item_estoque') or {}
            
            validade_str = ''
            if detalhe.get('validade'):
                try:
                    validade_str = datetime.strptime(detalhe['validade'], '%Y-%m-%d').strftime('%d/%m/%Y')
                except:
                    validade_str = detalhe['validade']
            
            data_entrada_str = ''
            if detalhe.get('data_entrada'):
                 try:
                     # Supabase returns iso format usually
                     dt_obj = datetime.fromisoformat(detalhe['data_entrada'].replace('Z', '+00:00'))
                     data_entrada_str = dt_obj.strftime('%d/%m/%Y %H:%M:%S')
                 except:
                     data_entrada_str = detalhe['data_entrada']

            dados_linha = {
                'CÓDIGO': str(item.get('codigo', '')).strip(),
                'CÓDIGO OPCIONAL': str(item.get('codigo_opcional', '') or '').strip(),
                'TIPO': str(item.get('tipo', '') or '').strip(),
                'DESCRIÇÃO': str(item.get('descricao', '') or '').strip(),
                'LOCAL': str(item.get('endereco', '') or '').strip(),
                'UN': str(item.get('un', '') or 'UN').strip(),
                'DIMENSÃO': str(item.get('dimensao', '') or '').strip(),
                'CLIENTE': str(item.get('cliente', '') or '').strip(),
                'LOTE': str(detalhe.get('lote', '') or '').strip(),
                'ITEM NF': str(detalhe.get('item_nf', '') or '').strip(),
                'NF': str(detalhe.get('nf', '') or '').strip(),
                'VALIDADE': validade_str,
                'ESTAÇÃO': str(detalhe.get('estacao', '') or '').strip(),
                'QTD ESTOQUE': round(float(detalhe.get('quantidade', 0)), 2),
                'DATA ENTRADA': data_entrada_str
            }
            
            for num_coluna, nome_coluna in enumerate(colunas_ordem, start=1):
                worksheet.cell(row=num_linha, column=num_coluna, value=dados_linha.get(nome_coluna, '')).alignment = Alignment(horizontal='left', vertical='center')
        
        # Ajuste largura
        for num_coluna, nome_coluna in enumerate(colunas_ordem, start=1):
            letra = get_column_letter(num_coluna)
            worksheet.column_dimensions[letra].width = 40 if nome_coluna == 'DESCRIÇÃO' else 20

        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)

        response = make_response(output.read())
        response.headers["Content-Disposition"] = f"attachment; filename=relatorio_estoque_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response

    except Exception as e:
        flash(f'Erro ao gerar o relatório: {str(e)}', 'danger')
        return redirect(url_for('estoque'))

@app.route('/estoque/apagar-tudo')
@admin_required
@login_required
def limpar_estoque_completo():
    """Apaga todos os registros de estoque."""
    try:
        # Apaga movimentacao
        supabase.table('movimentacao').delete().neq('id', 0).execute()
        # Apaga detalhes
        supabase.table('estoque_detalhe').delete().neq('id', 0).execute()
        # Apaga itens
        supabase.table('item_estoque').delete().neq('id', 0).execute()
        
        flash('TODO O ESTOQUE FOI APAGADO COM SUCESSO!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro ao tentar limpar o estoque: {e}', 'danger')
    
    return redirect(url_for('estoque'))

# --- ROTAS DE GERENCIAMENTO DE CONSUMÍVEIS ---

@app.route('/consumivel')
@login_required
def consumivel():
    """Página para listar todos os itens consumíveis do estoque."""
    search_query = request.args.get('q', '')
    
    # Helper already implements search
    consumiveis_data = get_consumiveis(search_term=search_query) 
    
    # Convert dicts to objects if template expects object attributes (e.g. .codigo)
    # ModelWrapper can handle it if I had a wrapper for Consumivel.
    # But for now, lets look at template usage. Usually it's `c.codigo`.
    # I'll create a simple wrapper or just pass dicts if template uses dict access.
    # Flask templates often need object access for dot notation unless passed as dict.
    # My previous wrappers handle `__getitem__` and `__getattr__`.
    # Let's simple use a generic class or passed dicts.
    # Jinja2 allows dot notation for dicts too? standard Jinja does.
    # But existing code might use `c.codigo`.
    # I'll define a simple ConsumivelWrapper inline or in models if needed.
    # Actually, `ModelWrapper` in `models.py` is generic. I can use it.
    
    consumiveis = [ModelWrapper(c) for c in consumiveis_data]

    # Carregar movimentações apenas para ADMIN
    movimentacoes = []
    if current_user.is_authenticated and current_user.role == 'admin':
        # Helper for movements
        movs_data = get_movimentacoes_consumivel()
        # Filter for recent ones? Route says order by desc.
        # Helper uses order desc.
        movimentacoes = [ModelWrapper(m) for m in movs_data]

    return render_template('consumivel.html', consumiveis=consumiveis, search_query=search_query, movimentacoes=movimentacoes)

@app.route('/consumivel/relatorio-movimentacoes')
@admin_only
@login_required
def relatorio_movimentacoes_consumivel_page():
    """Página do relatório de movimentações de consumíveis (apenas para admin)."""
    movs_data = get_movimentacoes_consumivel()
    
    # Format for JSON response same as original
    result = []
    for mov in movs_data:
        cons = mov.get('consumivel_estoque') or {}
        result.append({
            'id': mov['id'],
            'tipo': mov['tipo'],
            'quantidade': mov['quantidade'],
            'data_movimentacao': mov['data_movimentacao'], # ISO usually
            'observacao': mov['observacao'],
            'usuario': mov['usuario'],
            'setor_destino': mov['setor_destino'],
            'codigo_produto': cons.get('codigo_produto'),
            'descricao': cons.get('descricao'),
            'unidade_medida': cons.get('unidade_medida'),
            'categoria': cons.get('categoria')
        })
    return jsonify({'movimentacoes': result})

@app.route('/consumivel/importar', methods=['GET', 'POST'])
@admin_required
@login_required
def importar_consumivel():
    """Página e lógica para importar dados de consumíveis de uma planilha Excel."""
    if request.method == 'POST':
        if 'arquivo_excel' not in request.files:
            flash('Nenhum arquivo selecionado!', 'danger')
            return redirect(request.url)
        
        file = request.files['arquivo_excel']
        if file.filename == '':
            flash('Nenhum arquivo selecionado!', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
                
                # ...normalization logic same as before...
                def normalize_text(s):
                    if not isinstance(s, str):
                         s = '' if pd.isna(s) else str(s)
                    s = s.strip()
                    s = s.replace('º', '').replace('°', '').replace('ª', '')
                    s = unicodedata.normalize('NFKD', s)
                    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
                    s = s.upper()
                    s = ' '.join(s.split())
                    return s

                orig_cols = [str(c) for c in df.columns]
                norm_map = {normalize_text(c): c for c in orig_cols}

                def find_col_by_patterns(*patterns):
                    for ncol, orig in norm_map.items():
                        for pat in patterns:
                            if pat in ncol:
                                return orig
                    return None

                col_n_produto = find_col_by_patterns('N PRODUTO', 'NPRODUTO', 'NUM PRODUTO', 'NUMERO PRODUTO')
                col_codigo = find_col_by_patterns('CODIGO PRODUTO', 'CODIGOPRODUTO', 'CODIGO')
                col_descricao = find_col_by_patterns('DESCRICAO DO PRODUTO', 'DESCRICAODOPRODUTO', 'DESCRICAO')
                col_unidade = find_col_by_patterns('UNIDADE MEDIDA', 'UNIDADE')

                if not all([col_n_produto, col_codigo, col_descricao, col_unidade]):
                    flash(f'❌ Colunas obrigatórias faltando!\nColunas originais encontradas: {", ".join(orig_cols)}', 'danger')
                    return redirect(request.url)
                
                sucesso = 0
                erro = 0
                
                for idx, row in df.iterrows():
                    try:
                        n_produto = str(row.get(col_n_produto, '')).strip()
                        codigo = str(row.get(col_codigo, '')).strip()
                        desc = str(row.get(col_descricao, '')).strip()
                        unidade = str(row.get(col_unidade, '')).strip() or 'UN'
                        
                        if not n_produto or not codigo or not desc:
                            erro += 1
                            continue
                        
                        col_status_estoque = find_col_by_patterns('STATUS ESTOQUE', 'STATUSESTOQUE', 'STATUS')
                        col_status_consumo = find_col_by_patterns('STATUS CONSUMO', 'STATUSCONSUMO')
                        col_categoria = find_col_by_patterns('CATEGORIA')
                        col_fornecedor = find_col_by_patterns('FORNECEDOR', 'FORNECEDOR 2', 'FORNECEDOR2')
                        col_fornecedor2 = find_col_by_patterns('FORNECEDOR 2', 'FORNECEDOR2')
                        col_valor = find_col_by_patterns('VALOR UNITARIO', 'VALORUNITARIO', 'VALOR')
                        col_lead = find_col_by_patterns('LEAD TIME', 'LEADTIME', 'TEMPO REPOSICAO', 'DIAS')
                        col_seg = find_col_by_patterns('ESTOQUE DE SEGURANCA', 'ESTOQUESEGURANCA', 'PERCENTUAL ESTOQUE')
                        col_minimo = find_col_by_patterns('ESTOQUE MINIMO', 'ESTOQUE MINIMO POR CAIXA', 'ESTOQUEMINIMO')
                        col_atual = find_col_by_patterns('ESTOQUE ATUAL', 'ESTOQUEATUAL', 'QUANTIDADE ATUAL')

                        status_estoque = str(row.get(col_status_estoque, 'Ativo')).strip() or 'Ativo'
                        status_consumo = str(row.get(col_status_consumo, 'Consumível')).strip() or 'Consumível'
                        categoria = str(row.get(col_categoria, '')).strip()
                        fornecedor = str(row.get(col_fornecedor, '')).strip()
                        fornecedor2 = str(row.get(col_fornecedor2, '')).strip()
                        
                        # Helper for safe float/int conversion
                        def safe_float(v, default=0.0):
                            try: return float(v) if pd.notna(v) else default
                            except: return default
                        def safe_int(v, default=7):
                            try: return int(v) if pd.notna(v) else default
                            except: return default

                        valor = safe_float(row.get(col_valor))
                        lead = safe_int(row.get(col_lead))
                        seg = safe_float(row.get(col_seg))
                        minimo = safe_float(row.get(col_minimo))
                        atual = safe_float(row.get(col_atual))
                        
                        # Check exist
                        exist = supabase.table('consumivel_estoque').select('id').eq('codigo_produto', codigo).execute()
                        
                        data_payload = {
                            'n_produto': n_produto,
                            'codigo_produto': codigo,
                            'descricao': desc,
                            'unidade_medida': unidade,
                            'status_estoque': status_estoque,
                            'status_consumo': status_consumo,
                            'categoria': categoria,
                            'fornecedor': fornecedor,
                            'fornecedor2': fornecedor2,
                            'valor_unitario': valor,
                            'lead_time': lead,
                            'estoque_seguranca': seg,
                            'estoque_minimo': minimo,
                            'quantidade_atual': atual
                        }
                        
                        if exist.data:
                             supabase.table('consumivel_estoque').update(data_payload).eq('id', exist.data[0]['id']).execute()
                        else:
                             supabase.table('consumivel_estoque').insert(data_payload).execute()

                        sucesso += 1
                    
                    except Exception as e:
                        erro += 1
                        print(f"Erro linha {idx + 2}: {e}")
                
                flash(f'✅ {sucesso} consumível(is) importado(s)!', 'success')
                if erro > 0:
                    flash(f'⚠️ {erro} linha(s) ignorada(s).', 'warning')
                return redirect(url_for('consumivel'))
            
            except Exception as e:
                flash(f'❌ Erro: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('❌ Envie um arquivo .xlsx', 'danger')
            return redirect(request.url)
    
    return render_template('importar_consumivel.html')

@app.route('/consumivel/movimentacao', methods=['GET', 'POST'])
@admin_only
@login_required
def movimentacao_consumivel():
    """Página para registrar uma movimentação de consumível (entrada ou saída)."""
    if request.method == 'POST':
        consumivel_id = request.form.get('consumivel_id')
        tipo = request.form.get('tipo')
        quantidade = request.form.get('quantidade')
        setor_destino = request.form.get('setor_destino')
        observacao = request.form.get('observacao', '')

        if not consumivel_id or not tipo or not quantidade:
            flash('Consumível, tipo e quantidade são obrigatórios.', 'danger')
            return redirect(url_for('movimentacao_consumivel'))

        # Fetch cons
        res = supabase.table('consumivel_estoque').select('*').eq('id', consumivel_id).execute()
        consumivel = res.data[0] if res.data else None
        
        if not consumivel:
             abort(404)

        try:
            quantidade = float(quantidade)
            if quantidade <= 0:
                flash('A quantidade deve ser um número positivo.', 'danger')
                return redirect(url_for('movimentacao_consumivel'))
        except (ValueError, TypeError):
            flash('A quantidade deve ser um número válido.', 'danger')
            return redirect(url_for('movimentacao_consumivel'))
            
        current_qtd = float(consumivel['quantidade_atual'] or 0)

        # --- LÓGICA DE ENTRADA ---
        if tipo == 'ENTRADA':
            new_qtd = current_qtd + quantidade
            supabase.table('consumivel_estoque').update({'quantidade_atual': new_qtd}).eq('id', consumivel_id).execute()
            
            mov_data = {
                'consumivel_id': consumivel_id,
                'tipo': 'ENTRADA',
                'quantidade': quantidade,
                'usuario': current_user.username,
                'setor_destino': setor_destino or 'Almoxarifado',
                'observacao': observacao
            }
            supabase.table('movimentacao_consumivel').insert(mov_data).execute()
            flash('Entrada de consumível registrada com sucesso!', 'success')

        # --- LÓGICA DE SAÍDA ---
        elif tipo == 'SAIDA':
            if current_qtd < quantidade:
                flash(f'Quantidade insuficiente. Disponível: {current_qtd}', 'danger')
                return redirect(url_for('movimentacao_consumivel'))

            new_qtd = current_qtd - quantidade
            supabase.table('consumivel_estoque').update({'quantidade_atual': new_qtd}).eq('id', consumivel_id).execute()
            
            mov_data = {
                'consumivel_id': consumivel_id,
                'tipo': 'SAIDA',
                'quantidade': quantidade,
                'usuario': current_user.username,
                'setor_destino': setor_destino,
                'observacao': observacao
            }
            supabase.table('movimentacao_consumivel').insert(mov_data).execute()
            flash('Saída de consumível registrada com sucesso!', 'success')

        return redirect(url_for('movimentacao_consumivel'))

    # Para GET
    consumiveis_data = get_consumiveis()
    consumiveis = [ModelWrapper(c) for c in consumiveis_data]
    return render_template('movimentacao_consumivel.html', consumiveis=consumiveis)

@app.route('/consumivel/editar/<int:consumivel_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def editar_consumivel(consumivel_id):
    """Página para editar um consumível específico."""
    res = supabase.table('consumivel_estoque').select('*').eq('id', consumivel_id).execute()
    consumivel_data = res.data[0] if res.data else None
    
    if not consumivel_data:
        abort(404)
        
    consumivel = ModelWrapper(consumivel_data)

    if request.method == 'POST':
        try:
            update_data = {
                'n_produto': request.form.get('n_produto'),
                'status_estoque': request.form.get('status_estoque'),
                'status_consumo': request.form.get('status_consumo'),
                'descricao': request.form.get('descricao'),
                'unidade_medida': request.form.get('unidade_medida'),
                'categoria': request.form.get('categoria'),
                'fornecedor': request.form.get('fornecedor'),
                'fornecedor2': request.form.get('fornecedor2'),
                'valor_unitario': float(request.form.get('valor_unitario', 0)),
                'lead_time': int(request.form.get('lead_time', 0)),
                'estoque_seguranca': float(request.form.get('estoque_seguranca', 0)),
                'estoque_minimo': float(request.form.get('estoque_minimo', 0)),
                'quantidade_atual': float(request.form.get('quantidade_atual', 0))
            }

            supabase.table('consumivel_estoque').update(update_data).eq('id', consumivel_id).execute()
            flash('Consumível atualizado com sucesso!', 'success')
            return redirect(url_for('consumivel'))

        except Exception as e:
            flash(f'Erro ao atualizar o consumível: {e}', 'danger')

    return render_template('editar_consumivel.html', consumivel=consumivel)

@app.route('/consumivel/excluir/<int:consumivel_id>')
@admin_required
@login_required
def excluir_consumivel(consumivel_id):
    """Exclui um consumível do estoque."""
    try:
        # Remove também as movimentações relacionadas
        supabase.table('movimentacao_consumivel').delete().eq('consumivel_id', consumivel_id).execute()
        supabase.table('consumivel_estoque').delete().eq('id', consumivel_id).execute()
        flash('Consumível excluído com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao excluir o consumível: {e}', 'danger')

    return redirect(url_for('consumivel'))

@app.route('/consumivel/historico/<int:consumivel_id>')
@admin_only
@login_required
def historico_consumivel(consumivel_id):
    """Exibe o histórico de movimentações de um consumível."""
    res_cons = supabase.table('consumivel_estoque').select('*').eq('id', consumivel_id).execute()
    if not res_cons.data:
        abort(404)
    consumivel = ModelWrapper(res_cons.data[0])
    
    res_movs = supabase.table('movimentacao_consumivel').select('*').eq('consumivel_id', consumivel_id).order('data_movimentacao', desc=True).execute()
    movimentacoes = [ModelWrapper(m) for m in (res_movs.data or [])]
    
    return render_template('historico_consumivel.html', consumivel=consumivel, movimentacoes=movimentacoes)

@app.route('/api/consumivel/by-code/<string:codigo_produto>')
@login_required
def api_get_consumivel_by_code(codigo_produto):
    """Retorna os dados de um consumível pelo seu código."""
    # Case insensitive search
    res = supabase.table('consumivel_estoque').select('*').ilike('codigo_produto', codigo_produto).execute()
    consumivel = res.data[0] if res.data else None
    
    if not consumivel:
        return jsonify({'error': 'Consumível não encontrado'}), 404
    
    return jsonify({
        'id': consumivel['id'],
        'codigo_produto': consumivel['codigo_produto'],
        'descricao': consumivel['descricao'],
        'unidade_medida': consumivel['unidade_medida'],
        'categoria': consumivel['categoria'],
        'quantidade_atual': consumivel['quantidade_atual']
    })

@app.route('/api/relatorio/movimentacoes-consumivel')
@admin_only
@login_required
def api_relatorio_movimentacoes_consumivel():
    """Retorna todas as movimentações de consumíveis em formato JSON."""
    movs_data = get_movimentacoes_consumivel()
    
    dados = []
    for mov in movs_data:
        cons = mov.get('consumivel_estoque') or {}
        dados.append({
            'id': mov['id'],
            'tipo': mov['tipo'],
            'quantidade': mov['quantidade'],
            'data_movimentacao': mov['data_movimentacao'],
            'observacao': mov['observacao'],
            'usuario': mov['usuario'],
            'setor_destino': mov['setor_destino'],
            'codigo_produto': cons.get('codigo_produto'),
            'descricao': cons.get('descricao'),
            'unidade_medida': cons.get('unidade_medida'),
            'categoria': cons.get('categoria')
        })
    
    return jsonify(dados)


@app.route('/consumivel/exportar')
@login_required
def exportar_consumivel():
    """Exporta todos os consumíveis para Excel."""
    res = supabase.table('consumivel_estoque').select('*').order('codigo_produto').execute()
    consumiveis = res.data if res.data else []
    
    dados = []
    for consumivel in consumiveis:
        dados.append({
            'Nº PRODUTO': consumivel.get('n_produto'),
            'STATUS ESTOQUE': consumivel.get('status_estoque'),
            'STATUS CONSUMO': consumivel.get('status_consumo'),
            'CÓDIGO PRODUTO': consumivel.get('codigo_produto'),
            'DESCRIÇÃO DO PRODUTO': consumivel.get('descricao'),
            'UNIDADE MEDIDA': consumivel.get('unidade_medida'),
            'CATEGORIA': consumivel.get('categoria'),
            'FORNECEDOR': consumivel.get('fornecedor'),
            'FORNECEDOR 2': consumivel.get('fornecedor2'),
            'VALOR UNITÁRIO': consumivel.get('valor_unitario'),
            'LEAD TIME (DIAS ATRÁS)': consumivel.get('lead_time'),
            '% ESTOQUE DE SEGURANÇA': consumivel.get('estoque_seguranca'),
            'ESTOQUE MÍNIMO POR CAIXA': consumivel.get('estoque_minimo'),
            'ESTOQUE ATUAL': consumivel.get('quantidade_atual'),
        })
    
    df = pd.DataFrame(dados, columns=[
        'Nº PRODUTO', 'STATUS ESTOQUE', 'STATUS CONSUMO', 'CÓDIGO PRODUTO',
        'DESCRIÇÃO DO PRODUTO', 'UNIDADE MEDIDA', 'CATEGORIA', 'FORNECEDOR',
        'FORNECEDOR 2', 'VALOR UNITÁRIO', 'LEAD TIME (DIAS ATRÁS)',
        '% ESTOQUE DE SEGURANÇA', 'ESTOQUE MÍNIMO POR CAIXA', 'ESTOQUE ATUAL',
    ])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Consumíveis', index=False)
        worksheet = writer.sheets['Consumíveis']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return make_response(
        output.getvalue(),
        200,
        {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': f'attachment; filename="Consumiveis_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.xlsx"'
        }
    )

# --- ROTAS DE GERENCIAMENTO DE USUÁRIOS (ADMIN) ---

@app.route('/admin/usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Página para listar e gerenciar todos os usuários."""
    res = supabase.table('users').select('*').order('username').execute()
    users_data = res.data if res.data else []
    
    users = [User(u) for u in users_data]
    return render_template('admin_usuarios.html', users=users)

@app.route('/admin/usuario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def criar_usuario():
    """Página para criar um novo usuário."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not password or not role:
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('criar_usuario'))

        if get_user_by_username(username):
            flash('Este nome de usuário já está em uso.', 'danger')
            return redirect(url_for('criar_usuario'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        create_user(username=username, password_hash=hashed_password, role=role)
        
        flash(f'Usuário "{username}" criado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))

    return render_template('form_usuario.html', title="Criar Novo Usuário", action_url=url_for('criar_usuario'))

@app.route('/admin/usuario/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(user_id):
    """Página para editar um usuário existente."""
    user_data = get_user_by_id(user_id)
    if not user_data:
        abort(404)
    user = User(user_data)
    
    if request.method == 'POST':
        # Atualiza campos básicos
        update_data = {
            'username': request.form.get('username'),
            'role': request.form.get('role')
        }
        
        password = request.form.get('password')

        if password: # Só atualiza a senha se uma nova for fornecida
            update_data['password_hash'] = bcrypt.generate_password_hash(password).decode('utf-8')
            flash('Senha atualizada com sucesso.', 'info')

        update_user(user_id, update_data)
        
        # Helper returns void or data? Helpers usually don't return updated obj directly unless configured.
        # But we can assume success if no exception.
        
        flash(f'Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))

    return render_template('form_usuario.html', title="Editar Usuário", user=user, action_url=url_for('editar_usuario', user_id=user_id))

@app.route('/admin/usuario/excluir/<int:user_id>')
@login_required
@admin_required
def excluir_usuario(user_id):
    """Rota para excluir um usuário."""
    # current_user é um objeto User (ModelWrapper), então acesso via atributo funciona
    if user_id == int(current_user.id):
        flash('Você não pode excluir a si mesmo.', 'danger')
        return redirect(url_for('gerenciar_usuarios'))
        
    user_data = get_user_by_id(user_id)
    if not user_data:
        abort(404)
        
    delete_user(user_id)
    flash(f'Usuário "{user_data.get("username")}" excluído com sucesso.', 'success')
    return redirect(url_for('gerenciar_usuarios'))

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user_data = get_user_by_username(request.form.get('username'))
        
        if user_data and bcrypt.check_password_hash(user_data.get('password_hash'), request.form.get('password')):
            user_obj = User(user_data)
            login_user(user_obj)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login sem sucesso. Verifique o nome de usuário e a senha.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registrar um novo usuário. Redireciona se já estiver logado."""
    # Se o usuário já estiver logado, não faz sentido registrar uma nova conta.
    if current_user.is_authenticated:
        flash('Você já está logado no sistema.', 'info')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if get_user_by_username(username):
            flash('Este nome de usuário já existe. Por favor, escolha outro.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        create_user(username=username, password_hash=hashed_password)
        
        flash('Sua conta foi criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- ROTA TEMPORÁRIA PARA PROMOVER UM USUÁRIO A ADMIN ---
# DEPOIS de usar, é RECOMENDADO remover ou comentar este código por segurança.
@app.route('/promote_to_admin')
@login_required
def promote_to_admin():
    """
    Rota temporária para promover o usuário logado a administrador.
    Acesse http://127.0.0.1:5000/promote_to_admin uma vez para se promover.
    """
    if current_user.role != 'admin':
        update_user(int(current_user.id), {'role': 'admin'})
        # current_user é proxy local, não atualiza automaticamente, mas o DB atualizou
        flash('Parabéns! Sua conta foi promovida para Administrador (necessário relogar).', 'success')
        logout_user() # Força relogin para atualizar role na sessão
        return redirect(url_for('login'))
    else:
        flash('Sua conta já é de um Administrador.', 'info')
    
    # Redireciona para a página de gerenciamento de usuários, que agora estará visível
    return redirect(url_for('gerenciar_usuarios'))
# --- FIM DA ROTA TEMPORÁRIA ---

# --- INICIALIZAÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':

    
    app.run(debug=True)
       