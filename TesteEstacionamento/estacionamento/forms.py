from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Estacionamento, Movimentacao, Vaga


class CriarEstacionamentoForm(forms.ModelForm):
    quantidade_vagas = forms.IntegerField(
        min_value=1,
        label='Quantidade de vagas',
        initial=10,
    )

    class Meta:
        model = Estacionamento
        fields = ['nome', 'valor', 'tipo_cobranca']
        labels = {
            'nome': 'Nome do estacionamento',
            'valor': 'Valor da cobrança (R$)',
            'tipo_cobranca': 'Tipo de cobrança',
        }
        widgets = {
            'valor': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'tipo_cobranca': forms.Select(),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is None or valor <= 0:
            raise ValidationError('O valor deve ser maior que zero.')
        return valor

    def clean_tipo_cobranca(self):
        tipo = self.cleaned_data.get('tipo_cobranca')
        if tipo not in (Estacionamento.POR_MINUTO, Estacionamento.POR_HORA):
            raise ValidationError('Selecione por minuto ou por hora.')
        return tipo


class ConfigurarVagasForm(forms.Form):
    estacionamento = forms.ModelChoiceField(
        queryset=Estacionamento.objects.filter(ativo=True),
        label='Estacionamento',
    )
    quantidade = forms.IntegerField(
        min_value=1,
        label='Quantidade de vagas',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Estacionamento.objects.filter(ativo=True).exists():
            self.fields['estacionamento'].queryset = Estacionamento.objects.none()


class EntradaVeiculoForm(forms.Form):
    vaga = forms.ModelChoiceField(
        queryset=Vaga.objects.none(),
        label='Vaga',
    )
    placa = forms.CharField(max_length=10, label='Placa')
    tempo_pago_minutos = forms.IntegerField(
        required=False,
        min_value=1,
        label='Tempo pago antecipado (minutos, opcional)',
        help_text='Se informado, minutos além desse período geram multa de 50% no excedente.',
    )

    def __init__(self, estacionamento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Vaga.objects.filter(ocupada=False)
        if estacionamento:
            qs = qs.filter(estacionamento=estacionamento)
        self.fields['vaga'].queryset = qs.order_by('numero')


class SaidaVeiculoForm(forms.Form):
    movimentacao = forms.ModelChoiceField(
        queryset=Movimentacao.objects.none(),
        label='Veículo',
    )
    forma_pagamento = forms.ChoiceField(
        choices=Movimentacao.PAGAMENTOS,
        label='Forma de pagamento',
    )

    def __init__(self, estacionamento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Movimentacao.objects.filter(ativa=True).select_related(
            'vaga', 'vaga__estacionamento'
        )
        if estacionamento:
            qs = qs.filter(vaga__estacionamento=estacionamento)
        self.fields['movimentacao'].queryset = qs
