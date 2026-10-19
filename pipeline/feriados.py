"""Feriados nacionais do Brasil, incluindo os móveis (calculados a partir da Páscoa).

Feriados e pontos facultativos derrubam o consumo de energia, então entram no calendário.
"""

import csv
from datetime import date, timedelta
from pathlib import Path

FIXOS = {
    (1, 1): "Confraternização Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independência do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamação da República",
    (12, 25): "Natal",
}


def pascoa(ano: int) -> date:
    """Domingo de Páscoa pelo algoritmo de Meeus/Jones/Butcher (calendário gregoriano)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 (nome do algoritmo original)
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


def feriados(ano: int) -> list[tuple[date, str, str]]:
    """Lista (data, nome, tipo) com tipo 'feriado' ou 'ponto facultativo'."""
    lista = [(date(ano, mes, dia), nome, "feriado") for (mes, dia), nome in FIXOS.items()]
    if ano >= 2024:  # Lei 14.759/2023 tornou o 20 de novembro feriado nacional
        lista.append((date(ano, 11, 20), "Consciência Negra", "feriado"))

    p = pascoa(ano)
    lista += [
        (p - timedelta(days=48), "Carnaval (segunda)", "ponto facultativo"),
        (p - timedelta(days=47), "Carnaval (terça)", "ponto facultativo"),
        (p - timedelta(days=2), "Sexta-feira Santa", "feriado"),
        (p + timedelta(days=60), "Corpus Christi", "ponto facultativo"),
    ]
    return sorted(lista)


def gerar_seed(anos: range, destino: Path) -> int:
    linhas = [f for ano in anos for f in feriados(ano)]
    with destino.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["data", "nome", "tipo"])
        escritor.writerows((d.isoformat(), nome, tipo) for d, nome, tipo in linhas)
    return len(linhas)
