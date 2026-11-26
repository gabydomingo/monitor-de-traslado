-- ultima version de cada dato

select *
from {{ ref('stg_mayorista__versiones') }}
qualify row_number() over (
    partition by indicador, clasificador, nivel, codigo, region, tipo_de_indicador, periodo
    order by descargado_utc desc
) = 1
