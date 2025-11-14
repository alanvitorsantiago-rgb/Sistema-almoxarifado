from datetime import datetime, date

def calculate_validity_status(validade_date):
    """Calcula o status de validade e retorna uma tupla (texto, classe_css)."""
    if not validade_date:
        return ("Sem validade", "text-muted")

    today = date.today()
    if isinstance(validade_date, datetime):
        validade_date = validade_date.date()
        
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

def utility_processor():
    """Disponibiliza a função para todos os templates."""
    return dict(calculate_status=calculate_validity_status)
