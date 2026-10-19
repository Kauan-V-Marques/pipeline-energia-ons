"""Gera o relatório web (HTML estático com gráficos Plotly) a partir dos marts."""

from datetime import date
from pathlib import Path

import duckdb
import plotly.graph_objects as go

CORES = {"SE": "#2563eb", "S": "#16a34a", "NE": "#f59e0b", "N": "#dc2626"}
NOMES = {"SE": "Sudeste/Centro-Oeste", "S": "Sul", "NE": "Nordeste", "N": "Norte"}
TIPOS_DIA = {"Dia útil": "#2563eb", "Fim de semana": "#16a34a", "Feriado": "#dc2626"}
LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, system-ui, sans-serif", size=13),
    margin=dict(l=60, r=20, t=50, b=50),
    hovermode="x unified",
    legend=dict(orientation="h", y=-0.18),
)


def _consulta(conn, sql: str) -> list[tuple]:
    return conn.execute(sql).fetchall()


def grafico_energia_anual(conn) -> go.Figure:
    linhas = _consulta(
        conn,
        """
        SELECT ano, id_subsistema, sum(energia_gwh) / 1000 AS twh
        FROM main_marts.agg_carga_mensal GROUP BY ALL ORDER BY ano
    """,
    )
    fig = go.Figure()
    for sub in ["SE", "S", "NE", "N"]:
        pontos = [(a, v) for a, s, v in linhas if s == sub]
        fig.add_bar(
            x=[a for a, _ in pontos], y=[v for _, v in pontos], name=NOMES[sub], marker_color=CORES[sub]
        )
    fig.update_layout(barmode="stack", title="Energia consumida por ano (TWh)", yaxis_title="TWh", **LAYOUT)
    return fig


def grafico_perfil_diario(conn, ano: int) -> go.Figure:
    linhas = _consulta(
        conn,
        f"""
        SELECT tipo_dia, hora, carga_media_mwmed / 1000 FROM main_marts.agg_perfil_horario
        WHERE ano = {ano} AND tipo_dia IN ('Dia útil', 'Fim de semana', 'Feriado') ORDER BY hora
    """,
    )
    fig = go.Figure()
    for tipo, cor in TIPOS_DIA.items():
        pontos = [(h, v) for t, h, v in linhas if t == tipo]
        fig.add_scatter(
            x=[h for h, _ in pontos],
            y=[v for _, v in pontos],
            name=tipo,
            line=dict(color=cor, width=3),
            mode="lines",
        )
    fig.update_layout(
        title=f"Curva típica do dia no SIN em {ano} (GWmed)",
        xaxis_title="Hora",
        yaxis_title="GWmed",
        xaxis=dict(dtick=2),
        **LAYOUT,
    )
    return fig


def grafico_mapa_calor(conn, ano: int) -> go.Figure:
    linhas = _consulta(
        conn,
        f"""
        SELECT mes, hora, avg(carga_mwmed) / 1000 FROM main_marts.agg_sin_horario
        WHERE ano = {ano} GROUP BY ALL ORDER BY mes, hora
    """,
    )
    matriz = [[0.0] * 24 for _ in range(12)]
    for mes, hora, valor in linhas:
        matriz[mes - 1][hora] = round(valor, 1)
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    fig = go.Figure(
        go.Heatmap(
            z=matriz,
            x=list(range(24)),
            y=meses,
            colorscale="YlOrRd",
            colorbar=dict(title="GWmed"),
            hovertemplate="%{y}, %{x}h: %{z} GWmed<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"Carga média do SIN por mês e hora em {ano}",
        xaxis_title="Hora",
        **{**LAYOUT, "hovermode": "closest"},
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def grafico_pandemia(conn) -> go.Figure:
    linhas = _consulta(
        conn,
        """
        SELECT ano, data, avg(carga_mwmed) / 1000
        FROM main_marts.agg_sin_horario
        WHERE ano IN (2019, 2020) AND mes BETWEEN 2 AND 7
        GROUP BY ALL ORDER BY data
    """,
    )
    fig = go.Figure()
    for ano, cor in ((2019, "#94a3b8"), (2020, "#dc2626")):
        # Os dois anos no mesmo calendário (2020, bissexto) para as datas se alinharem no eixo
        pontos = [(date(2020, d.month, d.day), v) for a, d, v in linhas if a == ano]
        fig.add_scatter(
            x=[d for d, _ in pontos],
            y=[v for _, v in pontos],
            name=str(ano),
            line=dict(color=cor, width=2),
            mode="lines",
        )
    fig.add_vline(x="2020-03-23", line_dash="dash", line_color="#475569")
    fig.add_annotation(
        x="2020-03-23", y=1, yref="paper", text=" início das restrições", showarrow=False, xanchor="left"
    )
    fig.update_layout(
        title="Pandemia: carga diária do SIN em 2020 vs 2019 (GWmed)",
        yaxis_title="GWmed",
        xaxis=dict(tickformat="%d/%m", dtick="M1"),
        **LAYOUT,
    )
    return fig


def tabela_picos(conn) -> str:
    linhas = _consulta(
        conn,
        """
        SELECT ano, data_hora, tipo_dia, carga_mwmed FROM main_marts.agg_picos_sin
        WHERE posicao = 1 ORDER BY ano
    """,
    )
    corpo = (
        "".join(
            f"<tr><td>{ano}</td><td>{dh:%d/%m/%Y %Hh}</td><td>{tipo}</td><td>{carga / 1000:,.1f}</td></tr>"
            for ano, dh, tipo, carga in linhas
        )
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return (
        "<table><thead><tr><th>Ano</th><th>Hora do pico</th><th>Tipo de dia</th><th>GWmed</th></tr></thead>"
        f"<tbody>{corpo}</tbody></table>"
    )


def indicadores(conn) -> dict:
    ano, anterior = _consulta(conn, "SELECT max(ano), max(ano) - 1 FROM main_marts.agg_carga_mensal")[0]
    energia = dict(
        _consulta(
            conn,
            f"""
        SELECT ano, sum(energia_gwh) / 1000 FROM main_marts.agg_carga_mensal
        WHERE ano IN ({ano}, {anterior}) GROUP BY ano
    """,
        )
    )
    pico = _consulta(
        conn, f"SELECT max(carga_mwmed) / 1000 FROM main_marts.agg_sin_horario WHERE ano = {ano}"
    )[0][0]
    imputadas = _consulta(conn, "SELECT count(*) FROM main_marts.fato_carga_horaria WHERE imputado")[0][0]
    linhas = _consulta(conn, "SELECT count(*) FROM main_marts.fato_carga_horaria")[0][0]
    return {
        "ano": ano,
        "energia_twh": energia[ano],
        "crescimento_pct": 100 * (energia[ano] / energia[anterior] - 1),
        "pico_gw": pico,
        "linhas": linhas,
        "imputadas": imputadas,
    }


def _br(valor: float, casas: int = 1) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar(banco: Path, destino: Path) -> Path:
    with duckdb.connect(str(banco), read_only=True) as conn:
        ind = indicadores(conn)
        ano = ind["ano"]
        figuras = [
            grafico_energia_anual(conn),
            grafico_perfil_diario(conn, ano),
            grafico_mapa_calor(conn, ano),
            grafico_pandemia(conn),
        ]
        picos = tabela_picos(conn)

    graficos = "".join(
        f'<section class="card">{fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False)}</section>'
        for i, fig in enumerate(figuras)
    )
    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carga de Energia no Brasil</title>
<style>
body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: #f1f5f9; color: #0f172a; }}
header {{ background: linear-gradient(120deg, #0f172a, #1e3a8a); color: #fff; padding: 32px 20px; }}
header h1 {{ margin: 0 0 6px; font-size: 28px; }} header p {{ margin: 0; color: #cbd5e1; }}
main {{ max-width: 1100px; margin: 0 auto; padding: 20px 16px 40px; display: grid; gap: 18px; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }}
.kpi, .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }}
.kpi strong {{ display: block; font-size: 26px; }} .kpi span {{ color: #64748b; font-size: 13px; }}
table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
footer {{ color: #64748b; font-size: 13px; text-align: center; padding-bottom: 30px; }} a {{ color: #2563eb; }}
</style></head><body>
<header><div style="max-width:1100px;margin:auto">
<h1>Carga de energia elétrica no Brasil</h1>
<p>Sistema Interligado Nacional · dados horários do ONS · gerado em {date.today():%d/%m/%Y}</p>
</div></header>
<main>
<div class="kpis">
  <div class="kpi"><strong>{_br(ind["energia_twh"])} TWh</strong><span>energia consumida em {ano}</span></div>
  <div class="kpi"><strong>{"+" if ind["crescimento_pct"] >= 0 else ""}{_br(ind["crescimento_pct"])}%</strong>
    <span>em relação a {ano - 1}</span></div>
  <div class="kpi"><strong>{_br(ind["pico_gw"])} GW</strong><span>maior carga horária em {ano}</span></div>
  <div class="kpi"><strong>{_br(ind["linhas"], 0)}</strong><span>leituras horárias ({ind["imputadas"]} estimadas)</span></div>
</div>
{graficos}
<section class="card"><h2 style="margin-top:0;font-size:18px">Maior pico de cada ano</h2>{picos}</section>
</main>
<footer>Fonte: <a href="https://dados.ons.org.br/dataset/curva-carga">ONS · Curva de Carga Horária</a> (CC-BY).
Pipeline: <a href="https://github.com/Kauan-V-Marques/pipeline-energia-ons">pipeline-energia-ons</a>.</footer>
</body></html>"""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino
