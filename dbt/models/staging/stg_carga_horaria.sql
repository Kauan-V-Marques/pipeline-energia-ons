-- Curva de carga horária do ONS: tipada, sem duplicatas e com as horas faltantes preenchidas.
-- Carga em MWmed: a média de potência na hora (numericamente igual à energia em MWh).

with bruto as (
    select
        id_subsistema,
        din_instante as data_hora,
        -- Carga zero não existe num subsistema inteiro: é hora sem medição. Ex.: 04/11/2018 00h no Sul,
        -- madrugada em que começou o horário de verão e a meia-noite "não aconteceu".
        case when val_cargaenergiahomwmed > 0 then val_cargaenergiahomwmed end as carga
    from read_csv(
        '{{ var("pasta_raw") }}/CURVA_CARGA_*.csv',
        delim = ';',
        header = true,
        columns = {
            'id_subsistema': 'VARCHAR',
            'nom_subsistema': 'VARCHAR',
            'din_instante': 'TIMESTAMP',
            'val_cargaenergiahomwmed': 'DOUBLE'
        }
    )
    where year(din_instante) between {{ var('ano_inicio') }} and {{ var('ano_fim') }}
),

-- Se a mesma hora vier repetida na origem, fica a média
sem_duplicatas as (
    select id_subsistema, data_hora, avg(carga) as carga, count(*) as ocorrencias
    from bruto
    group by all
),

-- Hora sem valor: média da hora anterior e da seguinte do mesmo subsistema
preenchido as (
    select
        id_subsistema,
        data_hora,
        ocorrencias,
        carga as carga_original,
        coalesce(carga, (lag(carga) over janela + lead(carga) over janela) / 2) as carga_mwmed
    from sem_duplicatas
    window janela as (partition by id_subsistema order by data_hora)
)

select
    id_subsistema,
    data_hora,
    cast(data_hora as date) as data,
    hour(data_hora) as hora,
    round(carga_mwmed, 3) as carga_mwmed,
    carga_original is null as imputado,
    ocorrencias > 1 as duplicado_na_origem
from preenchido
