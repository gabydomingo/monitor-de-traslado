-- lo vigente es lo que dice la api hoy: para cada mes, la ultima descarga que lo trajo.
-- las descargas siempre traen meses enteros, asi que si el indec borra o renombra una
-- fila, en la descarga nueva ya no esta y aca tampoco. tomando la ultima version de cada
-- fila por separado, una fila borrada quedaba viva con el valor viejo

with versiones as (
    select * from {{ ref('stg_ipc__versiones') }}
),

ultima as (
    select periodo, max(descargado_utc) as descargado_utc
    from versiones
    group by periodo
)

select v.*
from versiones as v
inner join ultima as u using (periodo, descargado_utc)
