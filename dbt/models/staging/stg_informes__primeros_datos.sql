-- el primer dato publicado, con el codigo de la api al lado

select
    p.dataset,
    p.indicador,
    p.region,
    c.codigo,
    p.nombre,
    make_date(cast(p.periodo as integer) // 100, cast(p.periodo as integer) % 100, 1) as fecha,
    cast(p.valor as double) as valor_publicado,
    p.archivo
from {{ source('informes', 'primeros_datos') }} as p
left join {{ ref('informes_codigos') }} as c using (dataset, nombre)
