-- Todas las versiones del IPC que bajo la ingesta, con nombres y tipos normalizados.
-- Una misma fila aparece una vez por cada version guardada.

select
    -- en oct-2026 el INDEC empezo a escribir "Estacionales" en vez de "Estacional"
    replace(clasificador, 'Estacionales, ', 'Estacional, ') as clasificador,
    nivel,
    codigo,
    -- el nivel general aparece como "NIVEL GENERAL" y como "Nivel general"
    case when codigo = '0' then 'Nivel general' else descripcion end as descripcion,
    region,
    tipo_de_indicador,
    cast(periodo as integer) as periodo,
    make_date(cast(periodo // 100 as integer), cast(periodo % 100 as integer), 1) as fecha,
    unidad_de_medida,
    cast(valor as double) as valor,
    -- "///" = el INDEC no pudo relevar el dato (ej. restaurantes en la cuarentena de 2020)
    coalesce(valor_null = '///', false) as sin_dato_indec,
    coalesce(observaciones like '%provisorio%', false) as es_provisorio,
    cast(_descargado_utc as timestamp) as descargado_utc,
    _ventana as ventana
from {{ source('raw', 'ipc') }}
