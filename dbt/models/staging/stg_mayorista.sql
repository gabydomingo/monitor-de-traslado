-- igual que en el ipc: para cada mes, lo que trajo la ultima descarga

with versiones as (
    select * from {{ ref('stg_mayorista__versiones') }}
),

ultima as (
    select periodo, max(descargado_utc) as descargado_utc
    from versiones
    group by periodo
)

select v.*
from versiones as v
inner join ultima as u using (periodo, descargado_utc)
