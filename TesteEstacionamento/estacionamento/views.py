from datetime import date, datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import now
from django.db import models

from .billing import CobrancaError, calcular_cobranca
from .forms import (
    ConfigurarVagasForm,
    CriarEstacionamentoForm,
    EntradaVeiculoForm,
    SaidaVeiculoForm,
)
from .models import Estacionamento, Movimentacao, Vaga, UserProfile
from .utils import definir_estacionamento_atual, get_estacionamento_atual


def home(request):
    if request.method == 'POST' and 'estacionamento_id' in request.POST:
        estacionamento = Estacionamento.objects.filter(
            pk=request.POST.get('estacionamento_id'),
            ativo=True,
        ).first()
        if estacionamento:
            definir_estacionamento_atual(request, estacionamento)
        return redirect('home')

    estacionamento = get_estacionamento_atual(request)
    estacionamentos = Estacionamento.objects.filter(ativo=True)

    vagas = Vaga.objects.none()
    if estacionamento:
        vagas = estacionamento.vagas.all().order_by('numero')

    vagas_livres = vagas.filter(ocupada=False).count()
    vagas_ocupadas = vagas.filter(ocupada=True).count()

    return render(request, 'home.html', {
        'vagas': vagas,
        'estacionamento': estacionamento,
        'estacionamentos': estacionamentos,
        'vagas_livres': vagas_livres,
        'vagas_ocupadas': vagas_ocupadas,
    })


@login_required
def configurar_vagas(request):
    # Check if user has permission to manage parking
    if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
        return redirect('login')
    
    if not request.user.profile.can_manage_parking():
        return redirect('home')

    estacionamentos = Estacionamento.objects.filter(ativo=True)
    criar_form = CriarEstacionamentoForm()
    configurar_form = None

    if estacionamentos.exists():
        configurar_form = ConfigurarVagasForm(
            initial={'estacionamento': get_estacionamento_atual(request)},
        )

    if request.method == 'POST':
        acao = request.POST.get('acao', 'criar')

        if acao == 'criar':
            criar_form = CriarEstacionamentoForm(request.POST)
            if criar_form.is_valid():
                estacionamento = criar_form.save()
                quantidade = criar_form.cleaned_data['quantidade_vagas']
                for i in range(1, quantidade + 1):
                    Vaga.objects.create(estacionamento=estacionamento, numero=i)
                definir_estacionamento_atual(request, estacionamento)
                return redirect('home')

        elif acao == 'vagas' and configurar_form is not None:
            configurar_form = ConfigurarVagasForm(request.POST)
            if configurar_form.is_valid():
                estacionamento = configurar_form.cleaned_data['estacionamento']
                quantidade = configurar_form.cleaned_data['quantidade']
                estacionamento.vagas.all().delete()
                for i in range(1, quantidade + 1):
                    Vaga.objects.create(estacionamento=estacionamento, numero=i)
                definir_estacionamento_atual(request, estacionamento)
                return redirect('home')

    return render(request, 'configurar.html', {
        'criar_form': criar_form,
        'configurar_form': configurar_form,
        'estacionamentos': estacionamentos,
    })


def entrada_veiculo(request):
    estacionamento = get_estacionamento_atual(request)
    if not estacionamento:
        if not (
            request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.can_manage_parking()
        ):
            return redirect('home')
        return redirect('configurar_vagas')

    if request.method == 'POST':
        form = EntradaVeiculoForm(estacionamento, request.POST)
        if form.is_valid():
            vaga = form.cleaned_data['vaga']
            placa = form.cleaned_data['placa']
            tempo_pago = form.cleaned_data.get('tempo_pago_minutos')

            Movimentacao.objects.create(
                vaga=vaga,
                placa=placa.upper(),
                horario_entrada=now(),
                tempo_pago_minutos=tempo_pago,
                ativa=True,
            )
            vaga.ocupada = True
            vaga.save()
            return redirect('home')
    else:
        form = EntradaVeiculoForm(estacionamento)

    return render(request, 'entrada.html', {
        'form': form,
        'estacionamento': estacionamento,
    })


def saida_veiculo(request):
    estacionamento = get_estacionamento_atual(request)
    if not estacionamento:
        if not (
            request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.can_manage_parking()
        ):
            return redirect('home')
        return redirect('configurar_vagas')

    cobranca = None
    movimentacao_finalizada = None

    if request.method == 'POST':
        form = SaidaVeiculoForm(estacionamento, request.POST)
        if form.is_valid():
            movimentacao = form.cleaned_data['movimentacao']
            forma_pagamento = form.cleaned_data['forma_pagamento']
            horario_saida = now()

            try:
                resultado = calcular_cobranca(
                    entrada=movimentacao.horario_entrada,
                    saida=horario_saida,
                    valor_unitario=estacionamento.valor,
                    tipo_cobranca=estacionamento.tipo_cobranca,
                    tempo_pago_minutos=movimentacao.tempo_pago_minutos,
                )
            except CobrancaError as exc:
                form.add_error(None, str(exc))
            else:
                movimentacao.horario_saida = horario_saida
                movimentacao.tempo_total_minutos = resultado.tempo_total_minutos
                movimentacao.tempo_cobrado = resultado.tempo_cobrado
                movimentacao.unidade_cobranca = resultado.unidade_cobranca
                movimentacao.valor_base = resultado.valor_base
                movimentacao.valor_multa = resultado.multa
                movimentacao.valor_pago = resultado.valor_final
                movimentacao.forma_pagamento = forma_pagamento
                movimentacao.ativa = False
                movimentacao.save()

                vaga = movimentacao.vaga
                vaga.ocupada = False
                vaga.save()

                cobranca = resultado
                movimentacao_finalizada = movimentacao
                form = SaidaVeiculoForm(estacionamento)
    else:
        form = SaidaVeiculoForm(estacionamento)

    return render(request, 'saida.html', {
        'form': form,
        'estacionamento': estacionamento,
        'cobranca': cobranca,
        'movimentacao': movimentacao_finalizada,
    })


def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.can_manage_parking():
            return redirect('painel')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not hasattr(user, 'profile') or not user.profile.can_manage_parking():
                return render(request, 'login.html', {
                    'error': 'Acesso permitido apenas para gestores e administradores.',
                })
            login(request, user)
            return redirect('painel')
        return render(request, 'login.html', {
            'error': 'Usuário ou senha inválidos.',
        })

    return render(request, 'login.html')


@login_required
def painel(request):
    # Check if user has permission to manage parking
    if not hasattr(request.user, 'profile') or not request.user.profile.can_manage_parking():
        return redirect('home')

    estacionamentos = Estacionamento.objects.filter(ativo=True)
    movimentacoes_ativas = Movimentacao.objects.filter(ativa=True).select_related('vaga', 'vaga__estacionamento')
    
    total_movimentacoes = Movimentacao.objects.count()
    total_receita = Movimentacao.objects.filter(valor_pago__isnull=False).aggregate(
        total=models.Sum('valor_pago')
    )['total'] or 0

    return render(request, 'painel.html', {
        'estacionamentos': estacionamentos,
        'movimentacoes_ativas': movimentacoes_ativas,
        'total_movimentacoes': total_movimentacoes,
        'total_receita': total_receita,
    })


def _get_periodo_relatorio(request):
    periodo = request.GET.get('periodo', 'dia')
    if periodo not in {'dia', 'semana', 'mes'}:
        periodo = 'dia'

    data_base = timezone.localdate()
    data_param = request.GET.get('data')
    if data_param:
        try:
            data_base = datetime.strptime(data_param, '%Y-%m-%d').date()
        except ValueError:
            data_base = timezone.localdate()

    if periodo == 'semana':
        data_inicio = data_base - timedelta(days=data_base.weekday())
        data_fim = data_inicio + timedelta(days=7)
        label = (
            f"Semana de {data_inicio.strftime('%d/%m/%Y')} "
            f"a {(data_fim - timedelta(days=1)).strftime('%d/%m/%Y')}"
        )
    elif periodo == 'mes':
        data_inicio = date(data_base.year, data_base.month, 1)
        if data_base.month == 12:
            data_fim = date(data_base.year + 1, 1, 1)
        else:
            data_fim = date(data_base.year, data_base.month + 1, 1)
        label = data_inicio.strftime('%m/%Y')
    else:
        data_inicio = data_base
        data_fim = data_inicio + timedelta(days=1)
        label = data_inicio.strftime('%d/%m/%Y')

    inicio = timezone.make_aware(
        datetime.combine(data_inicio, datetime.min.time()),
        timezone.get_current_timezone(),
    )
    fim = timezone.make_aware(
        datetime.combine(data_fim, datetime.min.time()),
        timezone.get_current_timezone(),
    )

    return periodo, data_base, inicio, fim, label


@login_required
def relatorios(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.can_manage_parking():
        return redirect('home')

    periodo, data_base, inicio, fim, periodo_label = _get_periodo_relatorio(request)

    entradas_periodo = Movimentacao.objects.filter(
        horario_entrada__gte=inicio,
        horario_entrada__lt=fim,
    )
    saidas_pagas_periodo = Movimentacao.objects.filter(
        horario_saida__gte=inicio,
        horario_saida__lt=fim,
        valor_pago__isnull=False,
    )
    canceladas_periodo = Movimentacao.objects.filter(
        ativa=False,
        horario_saida__gte=inicio,
        horario_saida__lt=fim,
        valor_pago__isnull=True,
    )

    total_recebido = saidas_pagas_periodo.aggregate(total=Sum('valor_pago'))['total'] or 0
    movimentacoes = Movimentacao.objects.filter(
        Q(horario_entrada__gte=inicio, horario_entrada__lt=fim)
        | Q(horario_saida__gte=inicio, horario_saida__lt=fim)
    ).select_related('vaga', 'vaga__estacionamento').order_by('-horario_entrada')

    entradas_por_estacionamento = dict(
        entradas_periodo.values_list('vaga__estacionamento_id')
        .annotate(total=models.Count('id'))
    )
    canceladas_por_estacionamento = dict(
        canceladas_periodo.values_list('vaga__estacionamento_id')
        .annotate(total=models.Count('id'))
    )
    recebidos_por_estacionamento = {
        item['vaga__estacionamento_id']: item['total'] or 0
        for item in saidas_pagas_periodo.values('vaga__estacionamento_id')
        .annotate(total=Sum('valor_pago'))
    }

    resumo_estacionamentos = []
    for estacionamento in Estacionamento.objects.filter(ativo=True):
        resumo_estacionamentos.append({
            'estacionamento': estacionamento,
            'entradas': entradas_por_estacionamento.get(estacionamento.id, 0),
            'canceladas': canceladas_por_estacionamento.get(estacionamento.id, 0),
            'recebido': recebidos_por_estacionamento.get(estacionamento.id, 0),
        })

    return render(request, 'relatorios.html', {
        'periodo': periodo,
        'data_base': data_base,
        'periodo_label': periodo_label,
        'periodos': [
            {'valor': 'dia', 'rotulo': 'Dia'},
            {'valor': 'semana', 'rotulo': 'Semana'},
            {'valor': 'mes', 'rotulo': 'Mês'},
        ],
        'total_entradas': entradas_periodo.count(),
        'total_recebido': total_recebido,
        'total_canceladas': canceladas_periodo.count(),
        'veiculos_ativos': Movimentacao.objects.filter(ativa=True).count(),
        'resumo_estacionamentos': resumo_estacionamentos,
        'movimentacoes': movimentacoes,
    })


@login_required
def gerenciar_usuarios(request):
    # Only admins can manage users
    if not hasattr(request.user, 'profile') or not request.user.profile.can_manage_users():
        return redirect('painel')

    usuarios = User.objects.select_related('profile').all()

    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'criar_usuario':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            
            if User.objects.filter(username=username).exists():
                return render(request, 'gerenciar_usuarios.html', {
                    'usuarios': usuarios,
                    'error': 'Nome de usuário já existe.',
                })
            
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, role=role)
            return redirect('gerenciar_usuarios')
        
        elif acao == 'alterar_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('role')
            
            user = User.objects.get(pk=user_id)
            if user.profile:
                user.profile.role = new_role
                user.profile.save()
            
            return redirect('gerenciar_usuarios')

    return render(request, 'gerenciar_usuarios.html', {
        'usuarios': usuarios,
    })


@login_required
def editar_estacionamento(request, estacionamento_id):
    # Check if user has permission to manage parking
    if not hasattr(request.user, 'profile') or not request.user.profile.can_manage_parking():
        return redirect('home')

    estacionamento = Estacionamento.objects.get(pk=estacionamento_id)
    
    if request.method == 'POST':
        estacionamento.nome = request.POST.get('nome')
        estacionamento.valor = request.POST.get('valor')
        estacionamento.tipo_cobranca = request.POST.get('tipo_cobranca')
        estacionamento.save()
        return redirect('painel')

    return render(request, 'editar_estacionamento.html', {
        'estacionamento': estacionamento,
    })


def logout_view(request):
    logout(request)
    return redirect('/')
