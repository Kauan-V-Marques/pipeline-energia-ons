select
    data,
    hora,
    data_hora,
    id_subsistema,
    carga_mwmed,
    imputado
from {{ ref('stg_carga_horaria') }}
