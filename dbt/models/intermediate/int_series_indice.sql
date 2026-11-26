-- todos los indices (ipc y mayorista) en formato largo, con la variacion calculada aca

with ipc as (
    select
        'ipc' as fuente,
        'IPC' as indicador,
        clasificador, nivel, codigo, descripcion, region,
        fecha, valor as indice, sin_dato_indec, es_provisorio
    from {{ ref('stg_ipc') }}
    where tipo_de_indicador = 'Indice'
),

mayorista as (
    select
        'mayorista' as fuente,
        indicador,
        clasificador, nivel, codigo, descripcion, region,
        fecha, valor as indice, sin_dato_indec, es_provisorio
    from {{ ref('stg_mayorista') }}
    where tipo_de_indicador = 'Indice'
),

series as (
    select * from ipc
    union all
    select * from mayorista
)

select
    *,
    100 * (indice / lag(indice) over serie - 1) as var_mensual,
    -- la logaritmica es la que voy a usar en los modelos, se puede sumar entre meses
    ln(indice) - ln(lag(indice) over serie) as var_log
from series
window serie as (partition by fuente, indicador, clasificador, codigo, region order by fecha)
