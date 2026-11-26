-- Regiones del IPC, mas el total nacional y el "Total del pais" del mayorista.

with provincias as (
    select region, count(*) as provincias, string_agg(provincia, ', ' order by provincia) as lista
    from {{ ref('provincias') }}
    group by region
),

regiones as (
    select * from (values
        ('Nacional', 0, 'ipc'),
        ('GBA', 1, 'ipc'),
        ('Pampeana', 2, 'ipc'),
        ('Noreste', 3, 'ipc'),
        ('Noroeste', 4, 'ipc'),
        ('Cuyo', 5, 'ipc'),
        ('Patagonia', 6, 'ipc'),
        ('Total del país', 7, 'mayorista')
    ) as t(region, orden, fuente)
)

select
    r.region,
    r.orden,
    r.fuente,
    coalesce(p.provincias, 0) as provincias,
    p.lista as lista_provincias
from regiones as r
left join provincias as p using (region)
