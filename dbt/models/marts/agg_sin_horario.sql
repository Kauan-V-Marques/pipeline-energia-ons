-- Carga do SIN (Sistema Interligado Nacional) hora a hora: soma dos quatro subsistemas
select
    f.data_hora,
    f.data,
    f.hora,
    c.ano,
    c.mes,
    c.tipo_dia,
    sum(f.carga_mwmed) as carga_mwmed
from {{ ref('fato_carga_horaria') }} as f
join {{ ref('dim_calendario') }} as c using (data)
group by all
