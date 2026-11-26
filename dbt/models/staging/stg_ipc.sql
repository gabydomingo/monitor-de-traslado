-- IPC vigente: de cada dato, la ultima version descargada.

select *
from {{ ref('stg_ipc__versiones') }}
qualify row_number() over (
    partition by clasificador, nivel, codigo, region, tipo_de_indicador, periodo
    order by descargado_utc desc
) = 1
