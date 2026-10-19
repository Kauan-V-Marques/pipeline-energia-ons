-- Preencher lacunas é aceitável; muitas lacunas indicam problema nos dados de origem
select count(*) as horas_imputadas
from {{ ref('fato_carga_horaria') }}
where imputado
having count(*) > {{ var('max_horas_imputadas') }}
