from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal


class UserProfile(models.Model):
    CLIENTE = 'cliente'
    GESTOR = 'gestor'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (CLIENTE, 'Cliente'),
        (GESTOR, 'Gestor'),
        (ADMIN, 'Administrador'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CLIENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def is_cliente(self):
        return self.role == self.CLIENTE

    def is_gestor(self):
        return self.role == self.GESTOR

    def is_admin(self):
        return self.role == self.ADMIN

    def can_manage_parking(self):
        return self.role in [self.GESTOR, self.ADMIN]

    def can_manage_users(self):
        return self.role == self.ADMIN


class Estacionamento(models.Model):
    POR_MINUTO = 'por_minuto'
    POR_HORA = 'por_hora'

    TIPO_COBRANCA_CHOICES = [
        (POR_MINUTO, 'Por minuto'),
        (POR_HORA, 'Por hora'),
    ]

    nome = models.CharField(max_length=120)
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    tipo_cobranca = models.CharField(
        max_length=20,
        choices=TIPO_COBRANCA_CHOICES,
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.valor is None or self.valor <= 0:
            raise ValidationError({
                'valor': 'O valor deve ser maior que zero.',
            })
        if self.tipo_cobranca not in (self.POR_MINUTO, self.POR_HORA):
            raise ValidationError({
                'tipo_cobranca': 'Tipo de cobrança deve ser por_minuto ou por_hora.',
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def tipo_cobranca_label(self):
        return dict(self.TIPO_COBRANCA_CHOICES).get(self.tipo_cobranca, self.tipo_cobranca)


class Vaga(models.Model):
    estacionamento = models.ForeignKey(
        Estacionamento,
        on_delete=models.CASCADE,
        related_name='vagas',
    )
    numero = models.IntegerField()
    ocupada = models.BooleanField(default=False)

    class Meta:
        ordering = ['estacionamento', 'numero']
        unique_together = [['estacionamento', 'numero']]

    def __str__(self):
        return f'{self.estacionamento.nome} — Vaga {self.numero}'


class Movimentacao(models.Model):

    PAGAMENTOS = [
        ('PIX', 'PIX'),
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]

    vaga = models.ForeignKey(Vaga, on_delete=models.CASCADE, related_name='movimentacoes')
    placa = models.CharField(max_length=10)
    horario_entrada = models.DateTimeField(default=timezone.now)
    horario_saida = models.DateTimeField(null=True, blank=True)

    tempo_pago_minutos = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Tempo já pago/reservado antecipadamente (minutos).',
    )

    tempo_total_minutos = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    tempo_cobrado = models.PositiveIntegerField(null=True, blank=True)
    unidade_cobranca = models.CharField(max_length=10, blank=True)
    valor_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    forma_pagamento = models.CharField(
        max_length=10,
        choices=PAGAMENTOS,
        null=True,
        blank=True,
    )
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.placa

    @property
    def estacionamento(self):
        return self.vaga.estacionamento
