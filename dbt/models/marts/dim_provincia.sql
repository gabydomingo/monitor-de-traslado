-- Provincias con su region del IPC, para el mapa.

select provincia_id, provincia, region, nota
from {{ ref('provincias') }}
