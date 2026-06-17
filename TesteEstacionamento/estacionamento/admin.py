from django.contrib import admin

from .models import Estacionamento, Movimentacao, Vaga


@admin.register(Estacionamento)
class EstacionamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor', 'tipo_cobranca', 'ativo', 'criado_em')
    list_filter = ('tipo_cobranca', 'ativo')


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ('estacionamento', 'numero', 'ocupada')
    list_filter = ('estacionamento', 'ocupada')


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        'placa', 'vaga', 'horario_entrada', 'horario_saida',
        'valor_pago', 'ativa',
    )
    list_filter = ('ativa', 'vaga__estacionamento')
