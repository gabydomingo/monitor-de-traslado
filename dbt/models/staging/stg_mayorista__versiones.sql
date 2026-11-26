-- todas las versiones del mayorista, igual que en el ipc

select
    indicador,
    strip_accents(clasificador) as clasificador,
    strip_accents(nivel) as nivel,
    codigo_apertura as codigo,
    descripcion,
    strip_accents(region) as region,
    tipo_de_indicador,
    cast(periodo as integer) as periodo,
    make_date(cast(periodo // 100 as integer), cast(periodo % 100 as integer), 1) as fecha,
    unidad_de_medida,
    cast(valor as double) as valor,
    coalesce(valor_null = '///', false) as sin_dato_indec,
    -- el ultimo mes viene como "* Dato provisorio"
    coalesce(observaciones like '%provisorio%', false) as es_provisorio,
    cast(_descargado_utc as timestamp) as descargado_utc,
    _ventana as ventana
from {{ source('raw', 'mayorista') }}
