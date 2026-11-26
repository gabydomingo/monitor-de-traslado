-- la variacion que calculo tiene que dar igual que la del indec.
-- dejo 0.1 de margen porque el indice viene redondeado

with nuestra as (
    select fuente, indicador, clasificador, codigo, region, fecha, var_mensual
    from {{ ref('int_series_indice') }}
    where var_mensual is not null
),

indec as (
    select 'ipc' as fuente, 'IPC' as indicador, clasificador, codigo, region, fecha, valor
    from {{ ref('stg_ipc') }} where tipo_de_indicador = 'v_m'
    union all
    select 'mayorista', indicador, clasificador, codigo, region, fecha, valor
    from {{ ref('stg_mayorista') }} where tipo_de_indicador = 'v_m'
)

select n.*, i.valor as var_indec, abs(n.var_mensual - i.valor) as diferencia
from nuestra as n
inner join indec as i using (fuente, indicador, clasificador, codigo, region, fecha)
where abs(n.var_mensual - i.valor) > 0.1
