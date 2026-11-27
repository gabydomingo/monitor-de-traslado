-- el dolar y el rem llevados a meses, para el pronostico.
-- tc_inicio_mes: promedio de los dias del mes anteriores a que salga el mayorista del mes
-- pasado, que es cuando se hace el pronostico. si todavia no esta en el calendario, del 1
-- al 13 (desde 2018 el mayorista nunca salio antes del 14). en el mes en curso solo hay los
-- dias que ya pasaron, asi que tampoco mira el futuro

with corte as (
    -- el informe del mayorista de T-1 sale en el mes T
    select cast(fecha + interval 1 month as date) as fecha, publicado
    from {{ ref('stg_informes__calendario') }}
    where dataset = 'mayorista'
),

diario as (
    select
        cast(date_trunc('month', b.fecha) as date) as mes,
        b.fecha,
        b.valor,
        coalesce(c.publicado, cast(date_trunc('month', b.fecha) as date) + 13) as corte
    from {{ ref('stg_bcra') }} as b
    left join corte as c on c.fecha = date_trunc('month', b.fecha)
    where b.variable = 'tipo_cambio_mayorista'
),

dolar as (
    select
        mes as fecha,
        -- redondeo: duckdb suma en paralelo y el orden cambia los ultimos decimales entre
        -- corridas. sin esto el warehouse no sale identico dos veces
        round(avg(valor), 6) as tc_promedio,
        round(avg(valor) filter (where fecha < corte), 6) as tc_inicio_mes,
        min(corte) as corte,
        arg_max(valor, fecha) as tc_cierre,
        count(*) as dias_con_dato,
        max(fecha) as ultimo_dia
    from diario
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
    d.tc_inicio_mes,
    d.corte,
    d.tc_cierre,
    d.dias_con_dato,
    cast(d.ultimo_dia as date) as ultimo_dia,
    r.rem_12m
from dolar as d
left join rem as r using (fecha)
where d.fecha >= date '2015-01-01'
order by 1
