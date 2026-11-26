-- Cada vez que el INDEC cambio un dato ya publicado: valor anterior, valor nuevo y cuando.
-- Sale de comparar versiones sucesivas. Arranca vacia y se va llenando con el tiempo.

with versiones as (
    select
        'ipc' as dataset, 'IPC' as indicador, clasificador, nivel, codigo, region,
        tipo_de_indicador, fecha, valor, es_provisorio, descargado_utc
    from {{ ref('stg_ipc__versiones') }}
    union all
    select
        'mayorista' as dataset, indicador, clasificador, nivel, codigo, region,
        tipo_de_indicador, fecha, valor, es_provisorio, descargado_utc
    from {{ ref('stg_mayorista__versiones') }}
),

-- la misma version puede estar en la bajada reciente y en la completa: me quedo con una
sin_repetir as (
    select distinct * from versiones
    where tipo_de_indicador in ('Indice', 'Precio promedio')
),

con_anterior as (
    select
        *,
        lag(valor) over dato as valor_anterior,
        lag(es_provisorio) over dato as era_provisorio,
        lag(descargado_utc) over dato as descargado_anterior_utc
    from sin_repetir
    window dato as (
        partition by dataset, indicador, clasificador, nivel, codigo, region,
            tipo_de_indicador, fecha
        order by descargado_utc
    )
)

select
    dataset, indicador, clasificador, nivel, codigo, region, tipo_de_indicador, fecha,
    valor_anterior,
    valor as valor_nuevo,
    valor - valor_anterior as diferencia,
    100 * (valor / valor_anterior - 1) as diferencia_pct,
    era_provisorio,
    es_provisorio,
    descargado_anterior_utc,
    descargado_utc as detectado_utc
from con_anterior
where valor_anterior is not null
    and valor is distinct from valor_anterior
