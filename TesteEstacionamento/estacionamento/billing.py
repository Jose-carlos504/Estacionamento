"""
Motor de cobrança do estacionamento.

Regras: tolerância 10 min, arredondamento para cima, multa 50% sobre excedente
quando há tempo pago antecipado.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

TOLERANCIA_MINUTOS = 10
MULTA_PERCENTUAL = Decimal('0.50')
TipoCobranca = Literal['por_minuto', 'por_hora']
UnidadeCobranca = Literal['minuto', 'hora']


class CobrancaError(ValueError):
    """Erro de validação no cálculo de cobrança."""


@dataclass(frozen=True)
class ResultadoCobranca:
    tempo_total_minutos: float
    tempo_cobrado: int
    unidade_cobranca: UnidadeCobranca
    valor_base: Decimal
    multa: Decimal
    valor_final: Decimal
    dentro_tolerancia: bool
    tempo_pago_minutos: int | None = None
    tempo_excedente_minutos: float = 0.0

    def as_dict(self) -> dict:
        return {
            'tempo_total_minutos': self.tempo_total_minutos,
            'tempo_cobrado': self.tempo_cobrado,
            'unidade_cobranca': self.unidade_cobranca,
            'valor_base': self.valor_base,
            'multa': self.multa,
            'valor_final': self.valor_final,
            'dentro_tolerancia': self.dentro_tolerancia,
            'tempo_pago_minutos': self.tempo_pago_minutos,
            'tempo_excedente_minutos': self.tempo_excedente_minutos,
        }


def _arredondar_moeda(valor: Decimal) -> Decimal:
    if valor < 0:
        raise CobrancaError('Valor negativo não permitido.')
    return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_minutos_exatos(entrada: datetime, saida: datetime) -> float:
    if entrada is None or saida is None:
        raise CobrancaError('Entrada e saída são obrigatórias para calcular a cobrança.')
    if saida <= entrada:
        raise CobrancaError('Horário de saída deve ser posterior à entrada.')
    return (saida - entrada).total_seconds() / 60.0


def _minutos_cobraveis_com_tolerancia(total_minutos: float) -> int:
    if total_minutos <= TOLERANCIA_MINUTOS:
        return 0
    return math.ceil(total_minutos - TOLERANCIA_MINUTOS)


def _minutos_cobraveis_sem_tolerancia(minutos: float) -> int:
    if minutos <= 0:
        return 0
    return math.ceil(minutos)


def _valor_por_minutos_cobraveis(
    minutos_cobraveis: int,
    valor_unitario: Decimal,
    tipo_cobranca: TipoCobranca,
    *,
    total_minutos_bruto: float | None = None,
) -> tuple[int, UnidadeCobranca, Decimal]:
    if tipo_cobranca == 'por_hora':
        if total_minutos_bruto is None:
            total_minutos_bruto = float(minutos_cobraveis)
        if total_minutos_bruto <= TOLERANCIA_MINUTOS:
            return 0, 'hora', Decimal('0')
        horas = math.ceil(total_minutos_bruto / 60)
        valor_base = valor_unitario * Decimal(horas)
        return horas, 'hora', _arredondar_moeda(valor_base)

    if minutos_cobraveis <= 0:
        return 0, 'minuto', Decimal('0')

    quantidade = minutos_cobraveis
    valor_base = valor_unitario * Decimal(quantidade)
    return quantidade, 'minuto', _arredondar_moeda(valor_base)


def _validar_parametros(valor_unitario: Decimal, tipo_cobranca: str) -> None:
    if valor_unitario is None or valor_unitario <= 0:
        raise CobrancaError('Valor da cobrança deve ser maior que zero.')
    if tipo_cobranca not in ('por_minuto', 'por_hora'):
        raise CobrancaError('Tipo de cobrança inválido. Use por_minuto ou por_hora.')


def calcular_cobranca(
    entrada: datetime,
    saida: datetime,
    valor_unitario: Decimal,
    tipo_cobranca: TipoCobranca,
    tempo_pago_minutos: int | None = None,
) -> ResultadoCobranca:
    """
    Calcula cobrança completa entre entrada e saída.

    - Tolerância grátis de 10 min no período cobrado normal.
    - Com tempo pago antecipado: cobra só o excedente + multa de 50% sobre o excedente.
    """
    _validar_parametros(valor_unitario, tipo_cobranca)

    total_minutos = calcular_minutos_exatos(entrada, saida)

    if tempo_pago_minutos is not None and tempo_pago_minutos < 0:
        raise CobrancaError('Tempo pago antecipado não pode ser negativo.')

    if tempo_pago_minutos and tempo_pago_minutos > 0:
        return _calcular_com_tempo_pago(
            total_minutos=total_minutos,
            valor_unitario=valor_unitario,
            tipo_cobranca=tipo_cobranca,
            tempo_pago_minutos=tempo_pago_minutos,
        )

    return _calcular_periodo_normal(
        total_minutos=total_minutos,
        valor_unitario=valor_unitario,
        tipo_cobranca=tipo_cobranca,
    )


def _calcular_periodo_normal(
    total_minutos: float,
    valor_unitario: Decimal,
    tipo_cobranca: TipoCobranca,
) -> ResultadoCobranca:
    dentro_tolerancia = total_minutos <= TOLERANCIA_MINUTOS
    minutos_cobraveis = _minutos_cobraveis_com_tolerancia(total_minutos)
    quantidade, unidade, valor_base = _valor_por_minutos_cobraveis(
        minutos_cobraveis,
        valor_unitario,
        tipo_cobranca,
        total_minutos_bruto=total_minutos,
    )
    valor_final = _arredondar_moeda(valor_base)

    return ResultadoCobranca(
        tempo_total_minutos=round(total_minutos, 2),
        tempo_cobrado=quantidade,
        unidade_cobranca=unidade,
        valor_base=valor_base,
        multa=Decimal('0'),
        valor_final=valor_final,
        dentro_tolerancia=dentro_tolerancia,
    )


def _calcular_com_tempo_pago(
    total_minutos: float,
    valor_unitario: Decimal,
    tipo_cobranca: TipoCobranca,
    tempo_pago_minutos: int,
) -> ResultadoCobranca:
    if total_minutos <= tempo_pago_minutos:
        dentro_tolerancia = total_minutos <= TOLERANCIA_MINUTOS
        return ResultadoCobranca(
            tempo_total_minutos=round(total_minutos, 2),
            tempo_cobrado=0,
            unidade_cobranca='minuto' if tipo_cobranca == 'por_minuto' else 'hora',
            valor_base=Decimal('0'),
            multa=Decimal('0'),
            valor_final=Decimal('0'),
            dentro_tolerancia=dentro_tolerancia,
            tempo_pago_minutos=tempo_pago_minutos,
            tempo_excedente_minutos=0.0,
        )

    excesso = total_minutos - tempo_pago_minutos
    minutos_cobraveis = _minutos_cobraveis_sem_tolerancia(excesso)
    quantidade, unidade, valor_base = _valor_por_minutos_cobraveis(
        minutos_cobraveis,
        valor_unitario,
        tipo_cobranca,
        total_minutos_bruto=excesso,
    )
    multa = _arredondar_moeda(valor_base * MULTA_PERCENTUAL)
    valor_final = _arredondar_moeda(valor_base + multa)

    return ResultadoCobranca(
        tempo_total_minutos=round(total_minutos, 2),
        tempo_cobrado=quantidade,
        unidade_cobranca=unidade,
        valor_base=valor_base,
        multa=multa,
        valor_final=valor_final,
        dentro_tolerancia=False,
        tempo_pago_minutos=tempo_pago_minutos,
        tempo_excedente_minutos=round(excesso, 2),
    )
