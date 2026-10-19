select id_subsistema, nome, regiao, estados
from {{ ref('subsistemas') }}
