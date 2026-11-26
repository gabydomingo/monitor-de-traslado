-- cada rubro en cada etapa: primaria (productor) -> industria (mayorista) -> gondola (ipc).
-- grano: rubro x etapa x indicador x codigo x region x mes

with corr as (
    select * from {{ ref('correspondencia_ciiu_coicop') }}
),

series as (
    select * from {{ ref('int_series_indice') }}
),

gondola as (
    select distinct
        c.par_id,
        'gondola' as etapa,
        s.fuente, s.indicador, s.codigo, s.descripcion, s.region,
        s.fecha, s.indice, s.var_mensual, s.var_log, s.sin_dato_indec, s.es_provisorio
    from corr as c
    inner join series as s
        on s.fuente = 'ipc'
        and s.clasificador = 'COICOP Argentina 2019'
        and s.codigo = c.coicop_codigo
),

mayorista as (
    select
        c.par_id,
        c.etapa,
        s.fuente, s.indicador, s.codigo, s.descripcion, s.region,
        s.fecha, s.indice, s.var_mensual, s.var_log, s.sin_dato_indec, s.es_provisorio
    from corr as c
    inner join series as s
        on s.fuente = 'mayorista'
        and s.clasificador = 'CIIU3'
        and s.codigo = c.ciiu_codigo
)

select * from gondola
union all
select * from mayorista
