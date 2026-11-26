-- Todas las versiones del mayorista (SIPM) que bajo la ingesta, normalizadas.

select
    indicador,
    clasificador,
    nivel,
    codigo_apertura as codigo,
    descripcion,
    region,
    tipo_de_indicador,
    cast(periodo as integer) as periodo,
    make_date(cast(periodo // 100 as integer), cast(periodo % 100 as integer), 1) as fecha,
    unidad_de_medida,
    cast(valor as double) as valor,
    -- "///" = el INDEC no pudo relevar el dato (ej. restaurantes en la cuarentena de 2020)
    coalesce(valor_null = '///', false) as sin_dato_indec,
    -- el INDEC marca el ultimo mes como "* Dato provisorio"
    coalesce(observaciones like '%provisorio%', false) as es_provisorio,
    cast(_descargado_utc as timestamp) as descargado_utc,
    _ventana as ventana
from {{ source('raw', 'mayorista') }}
