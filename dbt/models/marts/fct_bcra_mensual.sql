-- el dolar y el rem llevados a meses, para el pronostico.
-- tc_quincena es el promedio del 1 al 15: el pronostico se hace cuando sale el
-- mayorista del mes anterior (cerca del 19), asi que esos dias ya se conocen

with dolar as (
    select
        date_trunc('month', fecha) as fecha,
        avg(valor) as tc_promedio,
        avg(valor) filter (where day(fecha) <= 15) as tc_quincena,
        arg_max(valor, fecha) as tc_cierre,
        count(*) as dias_con_dato,
        max(fecha) as ultimo_dia
    from {{ ref('stg_bcra') }}
    where variable = 'tipo_cambio_mayorista'
    group by 1
),

rem as (
    -- el dato viene fechado el ultimo dia del mes en que se hizo la encuesta
    select date_trunc('month', fecha) as fecha, valor as rem_12m
    from {{ ref('stg_bcra') }}
    where variable = 'rem_12m'
)

select
    cast(d.fecha as date) as fecha,
    d.tc_promedio,
    d.tc_quincena,
    d.tc_cierre,
    d.dias_con_dato,
    cast(d.ultimo_dia as date) as ultimo_dia,
    r.rem_12m
from dolar as d
left join rem as r using (fecha)
where d.fecha >= date '2015-01-01'
order by 1
