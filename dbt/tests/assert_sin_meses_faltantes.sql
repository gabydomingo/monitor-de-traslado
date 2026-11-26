-- ninguna serie puede tener meses salteados

select fuente, indicador, clasificador, codigo, region,
    min(fecha) as desde, max(fecha) as hasta, count(*) as meses
from {{ ref('int_series_indice') }}
group by all
having count(*) <> date_diff('month', min(fecha), max(fecha)) + 1
