-- cuando publico el indec cada mes del ipc y del mayorista. la web lo usa para decir cuando
-- sale el proximo dato. tabla y no vista para que python no dependa de la carpeta de dbt
select dataset, fecha, publicado
from {{ ref('stg_informes__calendario') }}
