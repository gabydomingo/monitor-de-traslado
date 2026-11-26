-- ultima version de cada dato

select *
from {{ ref('stg_bcra__versiones') }}
qualify row_number() over (
    partition by id_variable, fecha
    order by descargado_utc desc
) = 1
