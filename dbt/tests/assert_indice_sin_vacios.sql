-- un indice vacio solo puede ser un dato que el indec no pudo relevar ("///").
-- si no, la api mando algo roto y la ultima version piso un dato bueno

select fuente, indicador, clasificador, codigo, region, fecha
from {{ ref('int_series_indice') }}
where indice is null and not sin_dato_indec
