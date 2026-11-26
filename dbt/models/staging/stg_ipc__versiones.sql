-- todas las versiones que bajo la ingesta, una fila por dato y por version.
-- las categorias van sin tildes porque el indec no siempre las escribe igual

select
    -- en oct-2026 aparece "Estacionales" en vez de "Estacional"
    replace(strip_accents(clasificador), 'Estacionales, ', 'Estacional, ') as clasificador,
    strip_accents(nivel) as nivel,
    codigo,
    -- el nivel general viene como "NIVEL GENERAL" y como "Nivel general"
    case when codigo = '0' then 'Nivel general' else descripcion end as descripcion,
    strip_accents(region) as region,
    tipo_de_indicador,
    cast(periodo as integer) as periodo,
    make_date(cast(periodo // 100 as integer), cast(periodo % 100 as integer), 1) as fecha,
    unidad_de_medida,
    cast(valor as double) as valor,
    -- "///" es dato que no se pudo relevar (cuarentena 2020)
    coalesce(valor_null = '///', false) as sin_dato_indec,
    coalesce(observaciones like '%provisorio%', false) as es_provisorio,
    cast(_descargado_utc as timestamp) as descargado_utc,
    _ventana as ventana
from {{ source('raw', 'ipc') }}
