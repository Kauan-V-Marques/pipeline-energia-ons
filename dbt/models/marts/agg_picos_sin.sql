-- As horas de maior carga do SIN em cada ano
select
    ano,
    rank() over (partition by ano order by carga_mwmed desc) as posicao,
    data_hora,
    tipo_dia,
    round(carga_mwmed, 0) as carga_mwmed
from {{ ref('agg_sin_horario') }}
qualify posicao <= 10
