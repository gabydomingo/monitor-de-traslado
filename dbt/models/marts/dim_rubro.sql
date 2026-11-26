-- Un rubro por fila, con que tan buena es la correspondencia entre mayorista e IPC.

with seed as (
    select * from {{ ref('correspondencia_ciiu_coicop') }}
)

select
    par_id,
    any_value(rubro) as rubro,
    any_value(coicop_codigo) as coicop_codigo,
    any_value(coicop_nivel) as coicop_nivel,
    count(*) as codigos_mayorista,
    string_agg(distinct etapa, ', ' order by etapa) as etapas,
    bool_or(etapa = 'primaria') as tiene_etapa_primaria,
    -- la peor calidad de sus codigos manda
    case min(case calidad when 'baja' then 1 when 'media' then 2 else 3 end)
        when 1 then 'baja' when 2 then 'media' else 'alta'
    end as calidad,
    -- energia: tarifa regulada, se muestra solo como contraste
    par_id = 'energia' as es_contraste
from seed
group by par_id
