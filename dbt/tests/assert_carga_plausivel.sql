-- Carga zero, negativa ou acima de 100 GWmed num subsistema indica erro na origem
select *
from {{ ref('fato_carga_horaria') }}
where carga_mwmed <= 0 or carga_mwmed > 100000
