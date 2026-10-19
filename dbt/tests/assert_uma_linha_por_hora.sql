-- Cada subsistema tem no máximo uma linha por hora
select id_subsistema, data_hora, count(*) as linhas
from {{ ref('fato_carga_horaria') }}
group by all
having count(*) > 1
