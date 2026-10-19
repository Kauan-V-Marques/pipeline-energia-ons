-- Energia mensal por subsistema e crescimento sobre o mesmo mês do ano anterior

with mensal as (
    select
        c.ano,
        c.mes,
        f.id_subsistema,
        round(sum(f.carga_mwmed) / 1000, 1) as energia_gwh,
        round(avg(f.carga_mwmed), 0) as carga_media_mwmed,
        round(max(f.carga_mwmed), 0) as carga_maxima_mwmed
    from {{ ref('fato_carga_horaria') }} as f
    join {{ ref('dim_calendario') }} as c using (data)
    group by all
)

select
    *,
    lag(energia_gwh) over (partition by id_subsistema, mes order by ano) as energia_gwh_ano_anterior,
    round(100 * (energia_gwh / lag(energia_gwh) over (partition by id_subsistema, mes order by ano) - 1), 2)
        as crescimento_pct
from mensal
