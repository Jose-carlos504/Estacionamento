from datetime import timedelta
from decimal import Decimal

from django.test import SimpleTestCase
from django.utils import timezone

from .billing import (
    TOLERANCIA_MINUTOS,
    CobrancaError,
    calcular_cobranca,
    calcular_minutos_exatos,
)


class MotorCobrancaTests(SimpleTestCase):
    def setUp(self):
        self.entrada = timezone.now()
        self.valor_min = Decimal('2.00')
        self.valor_hora = Decimal('10.00')

    def _saida_apos(self, minutos: float):
        return self.entrada + timedelta(minutes=minutos)

    def test_tolerancia_dez_minutos_gratis(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(10),
            self.valor_min,
            'por_minuto',
        )
        self.assertEqual(resultado.valor_final, Decimal('0'))
        self.assertTrue(resultado.dentro_tolerancia)
        self.assertEqual(resultado.tempo_cobrado, 0)

    def test_por_minuto_onze_minutos_cobra_um(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(11),
            self.valor_min,
            'por_minuto',
        )
        self.assertEqual(resultado.tempo_cobrado, 1)
        self.assertEqual(resultado.valor_final, Decimal('2.00'))

    def test_por_minuto_onze_min_meio_cobra_dois(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(11.5),
            self.valor_min,
            'por_minuto',
        )
        self.assertEqual(resultado.tempo_cobrado, 2)
        self.assertEqual(resultado.valor_final, Decimal('4.00'))

    def test_por_hora_cinquenta_nove_min_cobra_uma_hora(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(59),
            self.valor_hora,
            'por_hora',
        )
        self.assertEqual(resultado.tempo_cobrado, 1)
        self.assertEqual(resultado.unidade_cobranca, 'hora')
        self.assertEqual(resultado.valor_final, Decimal('10.00'))

    def test_por_hora_uma_hora_um_min_cobra_duas_horas(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(61),
            self.valor_hora,
            'por_hora',
        )
        self.assertEqual(resultado.tempo_cobrado, 2)
        self.assertEqual(resultado.valor_final, Decimal('20.00'))

    def test_multa_excedente_cinquenta_porcento(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(90),
            Decimal('1.00'),
            'por_minuto',
            tempo_pago_minutos=60,
        )
        self.assertEqual(resultado.tempo_excedente_minutos, 30)
        self.assertEqual(resultado.valor_base, Decimal('30.00'))
        self.assertEqual(resultado.multa, Decimal('15.00'))
        self.assertEqual(resultado.valor_final, Decimal('45.00'))

    def test_dentro_tempo_pago_sem_cobranca(self):
        resultado = calcular_cobranca(
            self.entrada,
            self._saida_apos(45),
            self.valor_min,
            'por_minuto',
            tempo_pago_minutos=60,
        )
        self.assertEqual(resultado.valor_final, Decimal('0'))

    def test_rejeita_valor_zero(self):
        with self.assertRaises(CobrancaError):
            calcular_cobranca(
                self.entrada,
                self._saida_apos(20),
                Decimal('0'),
                'por_minuto',
            )

    def test_rejeita_saida_antes_entrada(self):
        with self.assertRaises(CobrancaError):
            calcular_minutos_exatos(self.entrada, self.entrada)

    def test_minutos_exatos(self):
        minutos = calcular_minutos_exatos(self.entrada, self._saida_apos(11.5))
        self.assertAlmostEqual(minutos, 11.5)
