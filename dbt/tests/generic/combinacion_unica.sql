-- falla si hay filas repetidas para esas columnas
{% test combinacion_unica(model, columnas) %}
select {{ columnas | join(', ') }}, count(*) as repeticiones
from {{ model }}
group by {{ columnas | join(', ') }}
having count(*) > 1
{% endtest %}
