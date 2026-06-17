from .models import Estacionamento


def get_estacionamento_atual(request):
    """Retorna o estacionamento em uso na sessão ou o primeiro ativo."""
    pk = request.session.get('estacionamento_id')
    if pk:
        estacionamento = Estacionamento.objects.filter(pk=pk, ativo=True).first()
        if estacionamento:
            return estacionamento

    estacionamento = Estacionamento.objects.filter(ativo=True).first()
    if estacionamento:
        request.session['estacionamento_id'] = estacionamento.pk
    return estacionamento


def definir_estacionamento_atual(request, estacionamento):
    request.session['estacionamento_id'] = estacionamento.pk
