-- Falla si hay filas repetidas para la combinacion de columnas (la clave de la tabla).
{% test combinacion_unica(model, columnas) %}
select {{ columnas | join(', ') }}, count(*) as repeticiones
from {{ model }}
group by {{ columnas | join(', ') }}
having count(*) > 1
{% endtest %}
