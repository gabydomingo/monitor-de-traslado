-- cada codigo de la correspondencia tiene que tener datos.
-- si el indec deja de publicar alguno salta aca

with corr as (select * from {{ ref('correspondencia_ciiu_coicop') }}),
precios as (select distinct par_id, etapa, codigo from {{ ref('fct_precios') }})

select c.par_id, 'mayorista' as lado, c.ciiu_codigo as codigo
from corr as c
left join precios as p on p.par_id = c.par_id and p.etapa = c.etapa and p.codigo = c.ciiu_codigo
where p.codigo is null
union all
select distinct c.par_id, 'gondola', c.coicop_codigo
from corr as c
left join precios as p on p.par_id = c.par_id and p.etapa = 'gondola' and p.codigo = c.coicop_codigo
where p.codigo is null
