select provincia_id, provincia, region, nota
from {{ ref('provincias') }}
