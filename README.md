# Monitor de Traslado

Cuando sube el precio mayorista de algo, cuanto de esa suba llega a la gondola y en cuantos meses? Este proyecto lo mide por rubro y por region con datos de la [API del INDEC](https://api.indec.gob.ar/). De paso guarda cada correccion que hace el INDEC a sus datos provisorios, algo que la API no guarda.

En LinkedIn lo vengo contando como **Efecto Gondola**. Esta en construccion.

## Estado

- [x] Fase 0: base del repo (uv, ruff, pytest, CI)
- [x] Fase 1: ingesta diaria con los crudos versionados
- [x] Fase 2: warehouse con dbt y DuckDB
- [x] Fase 3: analisis exploratorio
- [x] Fase 4: modelo de traslado
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

## Analisis exploratorio

En [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb). Lo principal:

- Hay tres etapas de inflacion bien distintas (cerca del 2% mensual, entre 3 y 4%, y muy alta en 2022-2024), asi que el traslado se va a estimar por etapa.
- Las series no son estacionarias en niveles y si en variaciones: se trabaja con variaciones logaritmicas.
- Si se comparan las variaciones tal cual, mayorista y gondola parecen moverse casi igual en todos los rubros. Es la inflacion general moviendo todo junto. Restandola, combustibles, tabaco y carnes siguen mostrando un traslado claro y rapido; en equipamiento del hogar, prendas y calzado llega con 1 o 2 meses de rezago.
- Solo verduras, frutas y prendas tienen estacionalidad fuerte.

Las funciones estan en `src/monitor/analisis.py`, el notebook solo las usa.

## Modelo de traslado

En [`notebooks/02_traslado.ipynb`](notebooks/02_traslado.ipynb), con el codigo en `src/monitor/traslado.py`. Para cada rubro y region, un modelo de rezagos distribuidos sobre precios relativos (a cada serie le resto su inflacion general), con los rezagos elegidos por BIC, errores Newey-West y correccion por comparaciones multiples. Para carnes, lacteos y pan hay ademas un VAR con la cadena completa: productor, industria y gondola.

Lo que sale (GBA, datos a oct-2026):

- Una suba mayorista llega a la gondola en el mismo mes o en el siguiente. Despues de 2 meses casi no queda nada.
- Carnes, combustibles, autos y prendas trasladan entre 70 y 80%. Lacteos, aceites y calzado casi nada.
- Con inflacion alta se traslada mas en 11 de 17 rubros.
- Entre regiones cambia poco, salvo combustibles (bastante menos en Patagonia) y autos.
- Con el IPIB en vez del IPIM da lo mismo, salvo tabaco y combustibles, que tienen impuestos pesados.

Es un modelo de asociacion, no causal. Los resultados quedan en `data/resultados/`:

```
uv run python -m monitor.traslado
```

## Carpetas

```
src/monitor/   el pipeline
scripts/       la exploracion inicial de la API
notebooks/     analisis
dbt/           modelos, seeds y tests
data/raw/      crudos versionados
data/resultados/  resultados del modelo
tests/         tests de python
docs/          metodologia
```

## Datos

- IPC (`ipc_nacional`): desde abril de 2016, 6 regiones mas el total nacional.
- Precios mayoristas (`sipm_precios_mayoristas`): desde diciembre de 2015, total del pais.

El INDEC no publica precios por provincia, por eso todo va por region.

Fuente: INDEC.
