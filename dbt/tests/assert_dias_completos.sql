-- Todo dia do período tem as 24 horas dos 4 subsistemas (96 linhas)
select c.data, count(f.data) as linhas
from {{ ref('dim_calendario') }} as c
left join {{ ref('fato_carga_horaria') }} as f using (data)
group by c.data
having count(f.data) <> 96
