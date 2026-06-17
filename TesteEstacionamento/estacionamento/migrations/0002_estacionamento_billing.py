# Generated manually for billing engine refactor

import datetime
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def criar_estacionamento_padrao(apps, schema_editor):
    Estacionamento = apps.get_model('estacionamento', 'Estacionamento')
    Vaga = apps.get_model('estacionamento', 'Vaga')

    estacionamento, _ = Estacionamento.objects.get_or_create(
        nome='Estacionamento Principal',
        defaults={
            'valor': Decimal('10.00'),
            'tipo_cobranca': 'por_hora',
            'ativo': True,
        },
    )
    Vaga.objects.filter(estacionamento__isnull=True).update(estacionamento=estacionamento)


class Migration(migrations.Migration):

    dependencies = [
        ('estacionamento', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Estacionamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('tipo_cobranca', models.CharField(choices=[('por_minuto', 'Por minuto'), ('por_hora', 'Por hora')], max_length=20)),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.AddField(
            model_name='vaga',
            name='estacionamento',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='vagas',
                to='estacionamento.estacionamento',
            ),
        ),
        migrations.RunPython(criar_estacionamento_padrao, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='vaga',
            name='estacionamento',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='vagas',
                to='estacionamento.estacionamento',
            ),
        ),
        migrations.AlterField(
            model_name='vaga',
            name='numero',
            field=models.IntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='vaga',
            unique_together={('estacionamento', 'numero')},
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='tempo_pago_minutos',
            field=models.PositiveIntegerField(blank=True, help_text='Tempo já pago/reservado antecipadamente (minutos).', null=True),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='tempo_total_minutos',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='tempo_cobrado',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='unidade_cobranca',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='valor_base',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='valor_multa',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='horario_entrada',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='valor_pago',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
