-- todas las versiones de las series del bcra

select
    cast(id_variable as integer) as id_variable,
    variable,
    cast(fecha as date) as fecha,
    cast(periodo as integer) as periodo,
    cast(valor as double) as valor,
    cast(_descargado_utc as timestamp) as descargado_utc,
    _ventana as ventana
from {{ source('raw', 'bcra') }}
