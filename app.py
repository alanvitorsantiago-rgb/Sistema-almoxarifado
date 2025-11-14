# /app.py

import os
from sqlalchemy import or_, func
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, ItemEstoque, Movimentacao, EstoqueDetalhe
from functools import wraps 
from zoneinfo import ZoneInfo # Importa a biblioteca para trabalhar com fusos horários
from datetime import datetime, date, timedelta
import pandas as pd
import io
from flask_migrate import Migrate # Importa o Flask-Migrate

# --- INICIALIZAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Inicializa as extensões para serem usadas em toda a aplicação
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()

def configure_app(app_instance):
    """Configura a aplicação Flask."""
    # Chave secreta para sessões e mensagens flash
    app_instance.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-padrao-para-desenvolvimento') 
    
    # Configuração do banco de dados: usa DATABASE_URL (PostgreSQL no Render) se disponível, senão usa SQLite local.
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # A URL do Render vem como 'postgres://...', mas SQLAlchemy prefere 'postgresql://...'
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app_instance.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app_instance.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
        
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app_instance)
    bcrypt.init_app(app_instance)
    migrate.init_app(app_instance, db) # Inicializa o Flask-Migrate
    login_manager.init_app(app_instance)
    login_manager.login_view = 'login'  # Rota para redirecionar usuários não logados
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = 'info'

configure_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- FUNÇÃO PARA CRIAR O BANCO DE DADOS ---
def criar_banco_de_dados(app_context):
    """Cria as tabelas do banco de dados se não existirem."""
    with app_context:
        db.create_all()
        print("Banco de dados verificado e tabelas criadas com sucesso.")
        # Adiciona um usuário admin padrão se não houver nenhum
        if not User.query.first():
            hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
            admin_user = User(username='admin', password_hash=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário 'admin' padrão criado com a senha 'admin'.")

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


# --- ROTAS DA APLICAÇÃO ---

@app.route('/dashboard')
@login_required
def dashboard():
    """Renderiza o dashboard com dados reais do banco de dados."""
    hoje = date.today()

    # --- KPIs (Key Performance Indicators) ---
    total_items_distintos = ItemEstoque.query.count()
    total_unidades = db.session.query(func.sum(ItemEstoque.qtd_estoque)).scalar() or 0
    itens_zerados = ItemEstoque.query.filter(ItemEstoque.qtd_estoque == 0).count()
    
    # Lotes críticos (vencem nos próximos 30 dias ou já venceram)
    data_limite_criticos = hoje + timedelta(days=30)
    critical_lotes = EstoqueDetalhe.query.filter(
        EstoqueDetalhe.validade.isnot(None),
        EstoqueDetalhe.validade <= data_limite_criticos,
        EstoqueDetalhe.quantidade > 0
    ).all()

    # --- Dados para o Gráfico de Movimentações (Últimos 15 dias) ---
    labels_mov = [(hoje - timedelta(days=i)).strftime('%d/%m') for i in range(14, -1, -1)]
    entradas = []
    saidas = []
    for i in range(14, -1, -1):
        dia = hoje - timedelta(days=i)
        entradas.append(db.session.query(func.sum(Movimentacao.quantidade)).filter(Movimentacao.tipo=='ENTRADA', func.date(Movimentacao.data_movimentacao)==dia).scalar() or 0)
        saidas.append(db.session.query(func.sum(Movimentacao.quantidade)).filter(Movimentacao.tipo=='SAIDA', func.date(Movimentacao.data_movimentacao)==dia).scalar() or 0)

    movimentacoes_chart_data = {
        'labels': labels_mov, 'entradas': entradas, 'saidas': saidas
    }

    # --- Dados para o Gráfico de Tipos (Pizza) ---
    tipos_data = db.session.query(ItemEstoque.tipo, func.count(ItemEstoque.id)).group_by(ItemEstoque.tipo).order_by(func.count(ItemEstoque.id).desc()).all()
    tipos_chart_data = {
        'labels': [tipo if tipo else 'Não categorizado' for tipo, count in tipos_data],
        'counts': [count for tipo, count in tipos_data]
    }

    # --- Listas Top 5 ---
    top_stocked_items = ItemEstoque.query.order_by(ItemEstoque.qtd_estoque.desc()).limit(5).all()
    low_stocked_items = ItemEstoque.query.filter(
        ItemEstoque.qtd_estoque > 0, 
        ItemEstoque.qtd_estoque <= ItemEstoque.estoque_minimo
    ).order_by(ItemEstoque.qtd_estoque.asc()).limit(5).all()

    # --- Atividade Recente ---
    recent_movimentacoes = Movimentacao.query.order_by(Movimentacao.data_movimentacao.desc()).limit(5).all()

    # --- Dados para o Gráfico de Movimentações por Etapa ---
    movimentacoes_por_etapa = db.session.query(
        Movimentacao.etapa,
        func.sum(Movimentacao.quantidade).label('total_quantidade')
    ).group_by(Movimentacao.etapa).order_by(func.sum(Movimentacao.quantidade).desc()).all()

    etapas_chart_data = {
        'labels': [etapa if etapa else 'Não Especificada' for etapa, total_quantidade in movimentacoes_por_etapa],
        'quantities': [total_quantidade for etapa, total_quantidade in movimentacoes_por_etapa]
    }

    # --- Dados para Alertas de Validade ---
    data_limite_proximos = hoje + timedelta(days=40)

    # Lotes que vencem exatamente hoje e têm quantidade
    lotes_vencendo_hoje = EstoqueDetalhe.query.filter(
        EstoqueDetalhe.validade == hoje,
        EstoqueDetalhe.quantidade > 0
    ).order_by(EstoqueDetalhe.item_estoque_id).all()

    # Lotes que vencem nos próximos 40 dias (excluindo hoje) e têm quantidade
    lotes_proximo_vencimento = EstoqueDetalhe.query.filter(
        EstoqueDetalhe.validade > hoje,
        EstoqueDetalhe.validade <= data_limite_proximos,
        EstoqueDetalhe.quantidade > 0
    ).order_by(EstoqueDetalhe.validade.asc()).all()

    return render_template('dashboard.html', 
                           total_items_distintos=total_items_distintos,
                           total_unidades=total_unidades,
                           itens_zerados=itens_zerados,
                           critical_lotes=critical_lotes,
                           movimentacoes_chart_data=movimentacoes_chart_data,
                           tipos_chart_data=tipos_chart_data,
                           top_stocked_items=top_stocked_items,
                           low_stocked_items=low_stocked_items,
                           recent_movimentacoes=recent_movimentacoes,
                           lotes_vencendo_hoje=lotes_vencendo_hoje,
                           lotes_proximo_vencimento=lotes_proximo_vencimento, 
                           etapas_chart_data=etapas_chart_data, # Novo dado para o template
                           today_date=hoje)

@app.route('/')
@login_required
def index():
    """Redireciona a rota raiz para o novo dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/cadastro', methods=['GET', 'POST'])
@admin_required
@login_required
def cadastro():
    """Página para cadastrar um novo item no estoque."""
    if request.method == 'POST':
        # Coleta os dados do formulário para ItemEstoque
        codigo = request.form['codigo']
        descricao = request.form['descricao']
        
        # Coleta os dados do formulário para EstoqueDetalhe (primeiro lote)
        qtd_entrada = request.form.get('qtd_estoque') # Renomeado para clareza
        lote = request.form.get('lote')
        item_nf = request.form.get('item_nf')
        nf = request.form.get('nf')
        validade_str = request.form.get('validade')
        estacao = request.form.get('estacao')

        # Validação para campos obrigatórios do ItemEstoque
        if not codigo or not descricao:
            flash('Código e Descrição são campos obrigatórios para o item!', 'danger')
            return redirect(url_for('cadastro'))
        
        # Validação para campos obrigatórios do EstoqueDetalhe inicial
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

        # Verifica se o item já existe pelo código
        if ItemEstoque.query.filter_by(codigo=codigo).first():
            flash(f'Item com o código "{codigo}" já existe no estoque. Use a tela de movimentação para adicionar mais lotes.', 'warning')
            return redirect(url_for('cadastro'))

        # Converte validade
        validade = datetime.strptime(validade_str, '%Y-%m-%d').date() if validade_str else None

        # Cria um novo objeto ItemEstoque
        novo_item = ItemEstoque(
            codigo=codigo,
            endereco=request.form.get('endereco'),
            codigo_opcional=request.form.get('codigo_opcional'),
            tipo=request.form.get('tipo'),
            descricao=descricao,
            un=request.form.get('un'),
            dimensao=request.form.get('dimensao'),
            estoque_minimo=float(request.form.get('estoque_minimo', 5)), # Adiciona o estoque mínimo
            cliente=request.form.get('cliente'),
            qtd_estoque=0 # Começa com 0, será atualizado pelo EstoqueDetalhe
        )

        # Adiciona e salva no banco de dados
        try:
            db.session.add(novo_item)
            db.session.flush() # Para obter o ID do novo_item antes de commitar
            
            # Cria o primeiro detalhe de estoque para este item
            novo_detalhe = EstoqueDetalhe(
                item_estoque_id=novo_item.id,
                lote=lote,
                item_nf=item_nf,
                nf=nf,
                validade=validade,
                estacao=estacao,
                quantidade=qtd_entrada,
                data_entrada=datetime.utcnow() # Garante que a data de entrada seja registrada
            )
            db.session.add(novo_detalhe)

            # Atualiza a quantidade total do ItemEstoque
            novo_item.qtd_estoque += qtd_entrada

            db.session.commit()
            flash('Item e seu primeiro lote cadastrados com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar o item e lote: {e}', 'danger')
        
        return redirect(url_for('estoque'))

    return render_template('cadastro.html')

@app.route('/estoque')
@login_required
def estoque():
    """Página para listar todos os itens do estoque."""
    search_query = request.args.get('q', '') # Pega o parâmetro de busca 'q' da URL
    
    query = ItemEstoque.query

    if search_query:
        # Cria um termo de busca para usar com 'ilike' (case-insensitive)
        search_term = f"%{search_query}%"
        # Filtra por código, descrição ou endereço
        query = query.filter(
            or_(
                ItemEstoque.codigo.ilike(search_term),
                ItemEstoque.descricao.ilike(search_term),
                ItemEstoque.endereco.ilike(search_term)
            )
        )

    # Implementação da Paginação
    page = request.args.get('page', 1, type=int)
    per_page = 25 # Itens por página
    pagination = query.order_by(ItemEstoque.data_cadastro.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    itens = pagination.items
    return render_template('estoque.html', 
                           itens=itens, 
                           search_query=search_query, 
                           pagination=pagination,
                           today_date=date.today(),
                           timedelta=timedelta,
                           EstoqueDetalhe=EstoqueDetalhe) # Passa a classe para o template

@app.route('/item/editar/<int:item_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def editar_item(item_id):
    """Página para editar um item existente."""
    item = ItemEstoque.query.get_or_404(item_id)

    if request.method == 'POST':
        # Coleta os dados do formulário
        codigo = request.form['codigo']
        descricao = request.form['descricao']

        # Validação para campos obrigatórios
        if not codigo or not descricao:
            flash('Código e Descrição são campos obrigatórios!', 'danger')
            return render_template('editar_item.html', item=item)

        # Verifica se o novo código já existe em outro item
        item_existente = ItemEstoque.query.filter(ItemEstoque.codigo == codigo, ItemEstoque.id != item_id).first()
        if item_existente:
            flash(f'O código "{codigo}" já está em uso por outro item.', 'warning')
            return render_template('editar_item.html', item=item)

        # Atualiza os campos do objeto item
        item.codigo = codigo
        item.descricao = descricao
        item.endereco = request.form.get('endereco')
        item.codigo_opcional = request.form.get('codigo_opcional')
        item.tipo = request.form.get('tipo')
        item.un = request.form.get('un')
        item.dimensao = request.form.get('dimensao')
        item.estoque_minimo = float(request.form.get('estoque_minimo', 5)) # Atualiza o estoque mínimo
        item.cliente = request.form.get('cliente')
        # Os campos de lote, NF, validade, estacao, status_validade e qtd_estoque
        # NÃO são mais parte direta do ItemEstoque e não devem ser atualizados aqui.
        # Eles pertencem ao EstoqueDetalhe.
        try:
            db.session.commit()
            flash('Item atualizado com sucesso!', 'success')
            return redirect(url_for('estoque'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar o item: {e}', 'danger')

    return render_template('editar_item.html', item=item)

@app.route('/item/excluir/<int:item_id>')
@admin_required
@login_required
def excluir_item(item_id):
    """Rota para excluir um item do estoque."""
    item = ItemEstoque.query.get_or_404(item_id)
    # Adicionar verificação se o item tem movimentações? (Opcional)
    db.session.delete(item)
    db.session.commit()
    flash(f'Item "{item.descricao}" e todo o seu histórico foram excluídos com sucesso.', 'success')
    return redirect(url_for('estoque'))

@app.route('/movimentacao', methods=['GET', 'POST'])
@admin_required
@login_required
def movimentacao():
    """Página para registrar uma nova movimentação de estoque."""
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        tipo = request.form.get('tipo')
        etapa = request.form.get('etapa') # Captura a etapa
        observacao = request.form.get('observacao') # Captura a observação
        
        if not item_id or not tipo:
            flash('Item ou tipo de movimentação inválido.', 'danger')
            return redirect(url_for('movimentacao'))

        item = ItemEstoque.query.get_or_404(item_id)

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

        # --- LÓGICA DE ENTRADA ---
        if tipo == 'ENTRADA':
            lote = request.form.get('lote')
            item_nf = request.form.get('item_nf')
            nf = request.form.get('nf')
            if not lote or not item_nf:
                flash('Lote e Item NF são obrigatórios para entrada.', 'danger')
                return redirect(url_for('movimentacao'))

            # Verifica se já existe um detalhe com a mesma combinação de Lote, Item NF e NF
            detalhe_existente = item.detalhes_estoque.filter_by(lote=lote, item_nf=item_nf, nf=nf).first()
            
            if detalhe_existente:            
                # Se existe, apenas soma a quantidade
                detalhe_existente.quantidade += quantidade
            else:
                # Se não existe, cria um novo registro de EstoqueDetalhe
                validade_str = request.form.get('validade')
                novo_detalhe = EstoqueDetalhe(
                    item_estoque_id=item.id,
                    lote=lote,
                    item_nf=item_nf,
                    nf=nf,
                    validade=datetime.strptime(validade_str, '%Y-%m-%d').date() if validade_str else None,
                    estacao=request.form.get('estacao'),
                    quantidade=quantidade
                )
                db.session.add(novo_detalhe)

            # Define o fuso horário correto e captura a hora local
            fuso_horario_sp = ZoneInfo("America/Sao_Paulo")
            hora_local_correta = datetime.now(fuso_horario_sp)
            # Atualiza o total e registra a movimentação
            item.qtd_estoque += quantidade
            nova_movimentacao = Movimentacao(
                item_id=item.id, 
                tipo='ENTRADA', 
                quantidade=quantidade, 
                lote=lote, 
                item_nf=item_nf, 
                usuario=current_user.username,
                etapa=etapa,
                observacao=observacao,
                data_movimentacao=hora_local_correta) # Usa a hora local correta
            db.session.add(nova_movimentacao)            
            db.session.commit()
            flash('Entrada registrada com sucesso!', 'success')

        # --- LÓGICA DE SAÍDA ---
        elif tipo == 'SAIDA':
            detalhe_id = request.form.get('detalhe_id')
            if not detalhe_id:
                flash('É necessário selecionar um Lote/Item NF para a saída.', 'danger')
                return redirect(url_for('movimentacao'))

            detalhe_estoque = EstoqueDetalhe.query.get(detalhe_id)

            if not detalhe_estoque or detalhe_estoque.item_estoque_id != item.id:
                flash('Lote/Item NF inválido para este item.', 'danger')
                return redirect(url_for('movimentacao'))

            if detalhe_estoque.quantidade < quantidade:
                flash(f'Quantidade insuficiente no lote selecionado. Disponível: {detalhe_estoque.quantidade}', 'danger')
                return redirect(url_for('movimentacao'))

            # Subtrai a quantidade do lote específico e do total
            detalhe_estoque.quantidade -= quantidade
            item.qtd_estoque -= quantidade

            # Define o fuso horário correto e captura a hora local
            fuso_horario_sp = ZoneInfo("America/Sao_Paulo")
            hora_local_correta = datetime.now(fuso_horario_sp)
            # Registra a movimentação
            nova_movimentacao = Movimentacao(
                item_id=item.id, 
                tipo='SAIDA', 
                quantidade=quantidade, 
                lote=detalhe_estoque.lote, 
                item_nf=detalhe_estoque.item_nf, 
                usuario=current_user.username,
                etapa=etapa,
                observacao=observacao,
                data_movimentacao=hora_local_correta) # Usa a hora local correta
            db.session.add(nova_movimentacao)            
            db.session.commit()
            flash('Saída registrada com sucesso!', 'success')

        return redirect(url_for('movimentacao'))

    # Para o método GET (carregamento da página)
    return render_template('movimentacao.html')

@app.route('/historico/<int:item_id>')
@login_required
def historico(item_id):
    """Página para exibir o histórico de movimentações de um item."""
    item = ItemEstoque.query.get_or_404(item_id)
    # Ordena as movimentações da mais recente para a mais antiga
    movimentacoes = item.movimentacoes.order_by(Movimentacao.data_movimentacao.desc()).all()
    return render_template('historico.html', item=item, movimentacoes=movimentacoes)

@app.route('/item/<int:item_id>/lotes-detalhes')
@login_required
def detalhes_lotes(item_id):
    """Página para exibir todos os detalhes de lote de um item."""
    filtro_ativo = request.args.get('filtro')
    item = ItemEstoque.query.get_or_404(item_id)
    
    query = item.detalhes_estoque

    if filtro_ativo == 'critico':
        # Define a data limite: hoje + 30 dias
        data_limite = date.today() + timedelta(days=30)
        # Filtra lotes que têm validade e que vencem até a data limite
        query = query.filter(
            EstoqueDetalhe.validade.isnot(None),
            EstoqueDetalhe.validade <= data_limite
        )

    # Ordena os resultados por data de validade (mais próximos de vencer primeiro)
    detalhes = query.order_by(EstoqueDetalhe.validade.asc()).all()
    return render_template('detalhes_lotes.html', item=item, detalhes=detalhes, filtro_ativo=filtro_ativo)

@app.route('/lote/excluir/<int:detalhe_id>')
@admin_required
@login_required
def excluir_lote(detalhe_id):
    """Rota para excluir um lote do estoque."""
    detalhe = EstoqueDetalhe.query.get_or_404(detalhe_id)
    item_id = detalhe.item_estoque_id  # Salva o item_id antes de excluir o detalhe

    try:
        # 1. Atualiza a quantidade total do ItemEstoque subtraindo a quantidade do lote
        item = ItemEstoque.query.get(detalhe.item_estoque_id)
        if item:
            item.qtd_estoque -= detalhe.quantidade

        # 2. Remove o EstoqueDetalhe (lote)
        db.session.delete(detalhe)
        db.session.commit()

        flash(f'Lote "{detalhe.lote}" excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o lote: {e}', 'danger')

    # Redireciona para a página de detalhes do item
    return redirect(url_for('detalhes_lotes', item_id=item_id))




@app.route('/ajuste/lote/<int:detalhe_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def ajustar_lote(detalhe_id):
    """Página para ajustar a quantidade de um lote específico."""
    detalhe = EstoqueDetalhe.query.get_or_404(detalhe_id)
    item = detalhe.item_estoque

    if request.method == 'POST':
        nova_quantidade_str = request.form.get('nova_quantidade')
        novo_lote = request.form.get('lote')
        novo_item_nf = request.form.get('item_nf')
        nova_nf = request.form.get('nf')
        observacao = request.form.get('observacao')

        if not all([nova_quantidade_str, observacao, novo_lote, novo_item_nf]):
            flash('Os campos Lote, Item NF, Nova Quantidade e Observação são obrigatórios.', 'danger')
            return render_template('ajustar_lote.html', detalhe=detalhe, item=item)

        # Verifica se a nova combinação de Lote, Item NF e NF já existe em outro lote do mesmo item
        outro_detalhe = EstoqueDetalhe.query.filter(EstoqueDetalhe.item_estoque_id == item.id, EstoqueDetalhe.id != detalhe_id, EstoqueDetalhe.lote == novo_lote, EstoqueDetalhe.item_nf == novo_item_nf, EstoqueDetalhe.nf == nova_nf).first()
        if outro_detalhe:
            flash(f'Já existe outro lote para este item com a mesma combinação de Lote ({novo_lote}), Item NF ({novo_item_nf}) e NF ({nova_nf}). A combinação deve ser única.', 'danger')
            return render_template('ajustar_lote.html', detalhe=detalhe, item=item)
        try:
            nova_quantidade = float(nova_quantidade_str)
            if nova_quantidade < 0:
                flash('A quantidade não pode ser negativa.', 'danger')
                return render_template('ajustar_lote.html', detalhe=detalhe, item=item)
        except (ValueError, TypeError):
            flash('A quantidade informada é inválida.', 'danger')
            return render_template('ajustar_lote.html', detalhe=detalhe, item=item)

        quantidade_antiga = detalhe.quantidade
        diferenca = nova_quantidade - quantidade_antiga
        
        dados_alterados = (
            detalhe.lote != novo_lote or
            detalhe.item_nf != novo_item_nf or
            detalhe.nf != nova_nf or
            diferenca != 0
        )

        if not dados_alterados:
            flash('Nenhum dado foi alterado. Nenhuma ação foi realizada.', 'info')
            return redirect(url_for('detalhes_lotes', item_id=item.id))

        try:
            # 1. Atualiza os dados do lote
            detalhe.quantidade = nova_quantidade
            detalhe.lote = novo_lote
            detalhe.item_nf = novo_item_nf
            detalhe.nf = nova_nf

            # 2. Atualiza a quantidade total do item (se houver diferença)
            item.qtd_estoque += diferenca

            # 3. Cria a movimentação de ajuste
            mov_ajuste = Movimentacao(
                item_id=item.id,
                tipo='AJUSTE',
                quantidade=abs(diferenca),
                observacao=f"Ajuste de estoque: {observacao}",
                usuario=current_user.username,
                lote=novo_lote, # Usa o novo lote no histórico
                item_nf=novo_item_nf # Usa o novo item_nf no histórico
            )
            db.session.add(mov_ajuste)
            db.session.commit()
            flash(f'Estoque do lote {detalhe.lote} ajustado com sucesso!', 'success')
            return redirect(url_for('detalhes_lotes', item_id=item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao ajustar o estoque: {e}', 'danger')

    return render_template('ajustar_lote.html', detalhe=detalhe, item=item)

# --- ROTAS DE API INTERNA (para JavaScript) ---

@app.route('/api/item/by-code/<string:codigo>')
@login_required
def api_get_item_by_code(codigo):
    """Retorna os dados de um item pelo seu código em formato JSON."""
    item = ItemEstoque.query.filter_by(codigo=codigo).first()
    if not item:
        # Se o item não for encontrado, retorna um erro 404 claro.
        return jsonify({'error': 'Item não encontrado'}), 404
    
    # Reutiliza a função api_get_item para não duplicar o código de formatação do JSON.
    return api_get_item(item.id)

@app.route('/api/item/<int:item_id>')
@login_required
def api_get_item(item_id):
    """Retorna os dados de um item em formato JSON."""
    item = ItemEstoque.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'codigo': item.codigo,
        'descricao': item.descricao,
        'un': item.un,
        'dimensao': item.dimensao,
        'cliente': item.cliente
    })

@app.route('/api/item/<int:item_id>/lotes')
@login_required
def api_get_lotes(item_id):
    """
    Retorna os lotes disponíveis para um item em formato JSON, ordenados por FEFO ou FIFO.
    - FEFO (First-Expired, First-Out): Para itens perecíveis, ordena por data de validade.
    - FIFO (First-In, First-Out): Para 'Hardware' e 'Painel', ordena por data de entrada.
    """
    item = ItemEstoque.query.get_or_404(item_id)
    
    query = item.detalhes_estoque.filter(EstoqueDetalhe.quantidade > 0)

    # Verifica o tipo do item para decidir a estratégia de ordenação
    if item.tipo and item.tipo.lower() in ['hardware', 'painel']:
        # FIFO: Primeiro que Entra, Primeiro que Sai (ordena pela data de entrada mais antiga)
        detalhes = query.order_by(EstoqueDetalhe.data_entrada.asc()).all()
    else:
        # FEFO: Primeiro que Vence, Primeiro que Sai (ordena pela data de validade mais próxima)
        # Lotes sem validade ou com validade nula são colocados no final da lista.
        detalhes = query.order_by(EstoqueDetalhe.validade.asc().nullslast(), EstoqueDetalhe.data_entrada.asc()).all()

    lotes = [{'id': d.id, 'lote': d.lote, 'item_nf': d.item_nf, 'quantidade': d.quantidade, 'validade': d.validade.strftime('%d/%m/%Y') if d.validade else 'N/A'} for d in detalhes]
    return jsonify(lotes)

@app.route('/importar', methods=['GET', 'POST'])
@admin_required
@login_required
def importar():
    """Página e lógica para importar dados de uma planilha Excel."""
    if request.method == 'POST':
        # Verifica se o arquivo foi enviado
        if 'arquivo_excel' not in request.files:
            flash('Nenhum arquivo selecionado!', 'danger')
            return redirect(request.url)
        
        file = request.files['arquivo_excel']

        # Verifica se o nome do arquivo está vazio
        if file.filename == '':
            flash('Nenhum arquivo selecionado!', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
                
                # Validação de colunas obrigatórias
                required_columns = ['CÓDIGO', 'DESCRIÇÃO', 'LOTE', 'ITEM NF', 'QTD ESTOQUE']
                if not all(col in df.columns for col in required_columns):
                    flash(f'A planilha deve conter as colunas obrigatórias: {", ".join(required_columns)}', 'danger')
                    return redirect(request.url)

                sucesso_count = 0
                erro_count = 0
                
                for index, row in df.iterrows():
                    # Pega os dados da linha, tratando valores nulos (NaN) do pandas
                    codigo = str(row['CÓDIGO']) if pd.notna(row['CÓDIGO']) else None
                    descricao = str(row['DESCRIÇÃO']) if pd.notna(row['DESCRIÇÃO']) else 'Sem Descrição'
                    # Se LOTE, ITEM NF ou NF estiverem vazios, usa 'N/A' ou '' como padrão
                    lote = str(row['LOTE']) if pd.notna(row['LOTE']) else 'N/A'
                    item_nf = str(row['ITEM NF']) if pd.notna(row['ITEM NF']) else 'N/A'
                    nf = str(row.get('NF', '')) if pd.notna(row.get('NF')) else ''
                    qtd_entrada = float(row['QTD ESTOQUE']) if pd.notna(row['QTD ESTOQUE']) else 0

                    # Pula a linha APENAS se o CÓDIGO estiver faltando.
                    # Permite a importação de itens com quantidade zero, se necessário.
                    if not codigo:
                        erro_count += 1
                        continue

                    # Procura ou cria o ItemEstoque (item principal)
                    item = ItemEstoque.query.filter_by(codigo=codigo).first()
                    if not item:
                        item = ItemEstoque(
                            codigo=codigo,
                            descricao=descricao,
                            endereco=str(row.get('LOCAL', '')) if pd.notna(row.get('LOCAL')) else '',
                            codigo_opcional=str(row.get('CÓDIGO OPCIONAL', '')) if pd.notna(row.get('CÓDIGO OPCIONAL')) else '',
                            tipo=str(row.get('TIPO', '')) if pd.notna(row.get('TIPO')) else '',
                            un=str(row.get('UN.', '')) if pd.notna(row.get('UN.')) else '',
                            dimensao=str(row.get('DIMENSÃO', '')) if pd.notna(row.get('DIMENSÃO')) else '',
                            cliente=str(row.get('CLIENTE', '')) if pd.notna(row.get('CLIENTE')) else '',
                            qtd_estoque=0
                        )
                        db.session.add(item)
                        db.session.flush() # Para obter o ID do item

                    # Procura o EstoqueDetalhe pela combinação de lote, item_nf e nf
                    detalhe_existente = item.detalhes_estoque.filter_by(lote=lote, item_nf=item_nf, nf=nf).first()
                    if detalhe_existente:
                        detalhe_existente.quantidade += qtd_entrada
                    else:
                        validade = pd.to_datetime(row.get('VALIDADE')).date() if 'VALIDADE' in row and pd.notna(row.get('VALIDADE')) else None
                        novo_detalhe = EstoqueDetalhe(
                            item_estoque_id=item.id,
                            lote=lote,
                            item_nf=item_nf,
                            nf=nf,
                            validade=pd.to_datetime(row.get('VALIDADE')).date() if pd.notna(row.get('VALIDADE')) else None,
                            estacao=str(row.get('ESTAÇÃO', '')) if pd.notna(row.get('ESTAÇÃO')) else '',
                            quantidade=qtd_entrada
                        )
                        db.session.add(novo_detalhe)
                    
                    # Atualiza o total e registra a movimentação
                    item.qtd_estoque += qtd_entrada
                    nova_movimentacao = Movimentacao(item_id=item.id, tipo='ENTRADA', quantidade=qtd_entrada, lote=lote, item_nf=item_nf, usuario=current_user.username)
                    db.session.add(nova_movimentacao)
                    sucesso_count += 1

                db.session.commit()
                flash(f'Importação concluída! {sucesso_count} registros processados com sucesso. {erro_count} linhas ignoradas por falta de dados.', 'success')

            except Exception as e:
                db.session.rollback()
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
    """Exporta um relatório detalhado do estoque para um arquivo Excel."""
    try:
        # Busca todos os detalhes de lote, juntando com a informação do item principal
        query = db.session.query(EstoqueDetalhe).join(ItemEstoque).order_by(ItemEstoque.codigo, EstoqueDetalhe.data_entrada).all()

        # Prepara os dados para o DataFrame
        dados_para_exportar = []
        for detalhe in query:
            dados_para_exportar.append({
                'CÓDIGO': detalhe.item_estoque.codigo,
                'CÓDIGO OPCIONAL': detalhe.item_estoque.codigo_opcional,
                'TIPO': detalhe.item_estoque.tipo,
                'DESCRIÇÃO': detalhe.item_estoque.descricao,
                'LOCAL': detalhe.item_estoque.endereco,
                'UN.': detalhe.item_estoque.un,
                'DIMENSÃO': detalhe.item_estoque.dimensao,
                'CLIENTE': detalhe.item_estoque.cliente,
                'LOTE': detalhe.lote,
                'ITEM NF': detalhe.item_nf,
                'NF': detalhe.nf,
                'VALIDADE': detalhe.validade,
                'ESTAÇÃO': detalhe.estacao,
                'QTD ESTOQUE': detalhe.quantidade,
                'DATA ENTRADA': detalhe.data_entrada,
            })

        # Cria o DataFrame com o pandas
        df = pd.DataFrame(dados_para_exportar)

        # Cria um buffer de bytes em memória para salvar o arquivo Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Estoque_Detalhado')
        
        output.seek(0)

        # Cria a resposta HTTP para enviar o arquivo
        response = make_response(output.read())
        response.headers["Content-Disposition"] = f"attachment; filename=relatorio_estoque_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        return response

    except Exception as e:
        flash(f'Erro ao gerar o relatório: {e}', 'danger')
        return redirect(url_for('estoque'))

@app.route('/autorizacao/limpar', methods=['GET', 'POST'])
@admin_required
@login_required
def autorizacao_limpar():
    """
    Exibe uma página de autorização (GET) e, após validação de credenciais
    específicas (POST), apaga todos os registros de estoque.
    Apenas o usuário 'ALAN OLIVEIRA' pode realizar esta ação.
    """
    if request.method == 'POST':
        auth_user = request.form.get('auth_user')
        auth_password = request.form.get('auth_password')

        # Credencial de senha do ambiente
        CLEAN_PASS = os.environ.get('CLEAN_STOCK_PASSWORD')

        # Validação: usuário deve ser 'ALAN OLIVEIRA' e a senha deve corresponder à variável de ambiente
        if auth_user == 'ALAN OLIVEIRA' and auth_password == CLEAN_PASS:
            try:
                # A ordem é importante para respeitar as chaves estrangeiras
                db.session.query(Movimentacao).delete()
                db.session.query(EstoqueDetalhe).delete()
                db.session.query(ItemEstoque).delete()
                db.session.commit()
                flash('AUTORIZAÇÃO CONCEDIDA! TODO O ESTOQUE FOI APAGADO COM SUCESSO!', 'success')
                return redirect(url_for('estoque'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ocorreu um erro ao tentar limpar o estoque: {e}', 'danger')
                return redirect(url_for('estoque'))
        else:
            flash('Autorização negada. Usuário ou senha incorretos.', 'danger')
            return redirect(url_for('autorizacao_limpar'))

    # Para o método GET, renderiza a página de confirmação
    return render_template('confirmar_limpar_estoque.html')

@app.route('/relatorio/etapas')
@login_required
def relatorio_etapas():
    """Página para visualizar um resumo das movimentações agrupadas por etapa."""
    try:
        resumo_por_etapa = db.session.query(
            Movimentacao.etapa,
            func.count(Movimentacao.id).label('total_movimentacoes'),
            func.sum(Movimentacao.quantidade).label('quantidade_total')
        ).group_by(Movimentacao.etapa).order_by(Movimentacao.etapa).all()

        return render_template('relatorio_etapas.html', resumo=resumo_por_etapa)

    except Exception as e:
        flash(f'Erro ao gerar o relatório por etapas: {e}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/relatorio/etapa/<path:etapa_nome>')
@login_required
def relatorio_etapa_detalhe(etapa_nome):
    """Página para exibir os detalhes das movimentações de uma etapa específica."""
    try:
        # Se a etapa for 'Não Especificada', busca por valores nulos ou vazios
        if etapa_nome == 'Não Especificada':
            movimentacoes = Movimentacao.query.filter(or_(Movimentacao.etapa == None, Movimentacao.etapa == '')).order_by(Movimentacao.data_movimentacao.desc()).all()
        else:
            movimentacoes = Movimentacao.query.filter_by(etapa=etapa_nome).order_by(Movimentacao.data_movimentacao.desc()).all()
        
        return render_template('relatorio_etapa_detalhe.html', movimentacoes=movimentacoes, etapa_nome=etapa_nome)
    except Exception as e:
        flash(f'Erro ao carregar detalhes da etapa: {e}', 'danger')
        return redirect(url_for('relatorio_etapas'))

# --- ROTAS DE GERENCIAMENTO DE USUÁRIOS (ADMIN) ---

@app.route('/admin/usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Página para listar e gerenciar todos os usuários."""
    users = User.query.order_by(User.username).all()
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

        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'danger')
            return redirect(url_for('criar_usuario'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Usuário "{username}" criado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))

    return render_template('form_usuario.html', title="Criar Novo Usuário", action_url=url_for('criar_usuario'))

@app.route('/admin/usuario/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(user_id):
    """Página para editar um usuário existente."""
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.role = request.form.get('role')
        password = request.form.get('password')

        if password: # Só atualiza a senha se uma nova for fornecida
            user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            flash('Senha atualizada com sucesso.', 'info')

        db.session.commit()
        flash(f'Usuário "{user.username}" atualizado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))

    return render_template('form_usuario.html', title="Editar Usuário", user=user, action_url=url_for('editar_usuario', user_id=user_id))

@app.route('/admin/usuario/excluir/<int:user_id>')
@login_required
@admin_required
def excluir_usuario(user_id):
    """Rota para excluir um usuário."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode excluir a si mesmo.', 'danger')
        return redirect(url_for('gerenciar_usuarios'))
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário "{user.username}" excluído com sucesso.', 'success')
    return redirect(url_for('gerenciar_usuarios'))

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
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
       