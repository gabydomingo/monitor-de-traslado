# Monitor de Traslado

Cuando sube el precio mayorista de algo, cuanto de esa suba llega a la gondola y en cuantos meses? Este proyecto lo mide por rubro y por region con datos de la [API del INDEC](https://api.indec.gob.ar/). De paso guarda cada correccion que hace el INDEC a sus datos provisorios, algo que la API no guarda.

En LinkedIn lo vengo contando como **Efecto Gondola**. Esta en construccion.

## Estado

- [x] Fase 0: base del repo (uv, ruff, pytest, CI)
- [x] Fase 1: ingesta diaria con los crudos versionados
- [x] Fase 2: warehouse con dbt y DuckDB
- [ ] Fase 3: analisis exploratorio
- [ ] Fase 4: modelo de traslado
- [ ] Fase 5: pronostico
- [ ] Fase 6: analisis de las revisiones
- [ ] Fase 7: web con mapa por regiones
- [ ] Fase 8: metodologia y documentacion

## Correrlo

Hace falta [uv](https://docs.astral.sh/uv/) y un token de la API del INDEC (es gratis, se saca registrandose en la pagina).

```
uv sync
cp .env.example .env      # pegar el token
uv run pytest
```

## Ingesta

Un workflow de GitHub Actions baja todos los dias los ultimos 6 meses del IPC y de los precios mayoristas, que es donde el INDEC corrige. Una vez por mes baja toda la historia.

- `src/monitor/cliente.py`: pagina de a 1000 filas siempre con el mismo orden, reintenta si la API tira 429 o un 5xx, y antes de bajar cuenta cuantas filas tendrian que llegar. Si no llegan todas no guarda nada.
- `src/monitor/validacion.py`: chequea columnas, tipos, periodos y que no haya filas repetidas (con pandera). Si algo importante cambia frena. Si aparece una columna o un valor nuevo solo avisa.
- `src/monitor/almacenamiento.py`: saca un hash del contenido y solo guarda una version nueva si cambio algo. Las versiones quedan en `data/raw/` en parquet y anotadas en `data/raw/manifest.csv`.

Para probarla sin tocar `data/raw`:

```
uv run python -m monitor.ingesta --modo reciente --salida data/prueba
```

## Warehouse

dbt lee los parquet de `data/raw` con DuckDB y arma tres capas:

- **staging**: limpia lo que viene de la API. El INDEC no siempre escribe igual las categorias ("Estacional" y "Estacionales", "NIVEL GENERAL" y "Nivel general", con y sin tildes), asi que se normalizan. Tambien marca los datos que el INDEC no pudo relevar (`///`), como restaurantes en la cuarentena de 2020. Hay un modelo con todas las versiones y otro con la ultima de cada dato.
- **intermediate**: todos los indices en el mismo formato, con la variacion mensual y la logaritmica.
- **marts**: `fct_precios` (cada rubro en cada etapa: productor, industria y gondola por region), `fct_revisiones` (cada dato que el INDEC corrigio), `dim_rubro`, `dim_region` y `dim_provincia`.

Los tests chequean claves unicas, valores, relaciones entre tablas, que la variacion que calculo de igual que la del INDEC (con 0.1 de margen por redondeo), que no falten meses y que la ingesta este al dia. Hay tests unitarios con datos inventados para la logica de revisiones y de normalizacion.

```
cd dbt
uv run dbt build
uv run dbt docs generate && uv run dbt docs serve
```

Energia esta solo como contraste: la tarifa es regulada, asi que no es traslado de mercado.

## Carpetas

```
src/monitor/   el pipeline
scripts/       la exploracion inicial de la API
dbt/           modelos, seeds y tests
data/raw/      crudos versionados
tests/         tests de python
docs/          metodologia
```

## Datos

- IPC (`ipc_nacional`): desde abril de 2016, 6 regiones mas el total nacional.
- Precios mayoristas (`sipm_precios_mayoristas`): desde diciembre de 2015, total del pais.

El INDEC no publica precios por provincia, por eso todo va por region.

Fuente: INDEC.
