-- Um dia por linha, com atributos para análise e o tipo de dia (útil, fim de semana, feriado)

with dias as (
    select cast(unnest(generate_series(
        date '{{ var("ano_inicio") }}-01-01', date '{{ var("ano_fim") }}-12-31', interval 1 day
    )) as date) as data
),

-- Dois feriados no mesmo dia viram uma linha só ("feriado" vence "ponto facultativo")
feriados as (
    select data, string_agg(nome, ' / ') as nome, min(tipo) as tipo
    from {{ ref('feriados') }}
    group by data
)

select
    d.data,
    year(d.data) as ano,
    quarter(d.data) as trimestre,
    month(d.data) as mes,
    ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][month(d.data)] as nome_mes,
    strftime(d.data, '%Y-%m') as ano_mes,
    day(d.data) as dia,
    isodow(d.data) as dia_semana,
    ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo'][isodow(d.data)] as nome_dia_semana,
    f.nome as feriado,
    case
        when f.tipo = 'feriado' then 'Feriado'
        when f.tipo = 'ponto facultativo' then 'Ponto facultativo'
        when isodow(d.data) in (6, 7) then 'Fim de semana'
        else 'Dia útil'
    end as tipo_dia
from dias as d
left join feriados as f on f.data = d.data
