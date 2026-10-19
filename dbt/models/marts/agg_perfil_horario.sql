-- Curva típica do dia: carga média do SIN em cada hora, por tipo de dia e ano
select
    ano,
    tipo_dia,
    hora,
    round(avg(carga_mwmed), 0) as carga_media_mwmed
from {{ ref('agg_sin_horario') }}
group by all
