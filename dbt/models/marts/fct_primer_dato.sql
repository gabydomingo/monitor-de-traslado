-- el primer dato que publico el indec contra el que esta hoy en la api.
-- la api da la variacion con un decimal, igual que los informes

with api as (
    select 'ipc' as dataset, 'IPC' as indicador, region, codigo, fecha, valor
    from {{ ref('stg_ipc') }}
    where tipo_de_indicador = 'v_m'
        and (nivel = 'Division' or codigo = '0')
    union all
    select 'mayorista', indicador, region, codigo, fecha, valor
    from {{ ref('stg_mayorista') }}
    where tipo_de_indicador = 'v_m'
)

select
    p.dataset,
    p.indicador,
    p.region,
    p.codigo,
    p.nombre,
    p.fecha,
    p.valor_publicado,
    a.valor as valor_actual,
    round(a.valor - p.valor_publicado, 1) as revision,
    c.publicado,
    p.archivo
from {{ ref('stg_informes__primeros_datos') }} as p
left join api as a using (dataset, indicador, region, codigo, fecha)
left join {{ ref('stg_informes__calendario') }} as c using (dataset, fecha)
