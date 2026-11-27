-- cuando se publico cada mes. el informe sale el mes siguiente al que describe

select
    case tipo when 'ipm' then 'mayorista' else tipo end as dataset,
    cast(date_trunc('month', cast(publicado as date)) - interval 1 month as date) as fecha,
    cast(publicado as date) as publicado,
    archivo
from {{ source('informes', 'listado') }}
