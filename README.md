# Monitor de Traslado

¿Cuánto de una suba de precios mayoristas llega a la góndola, y en cuántos meses? Este proyecto lo mide por rubro y por región con datos oficiales de la [API del INDEC](https://api.indec.gob.ar/), y guarda además cada corrección que el INDEC hace a sus datos provisorios.

> Proyecto en construcción. En LinkedIn lo cuento como **Efecto Góndola**.

## Estado

- [x] Fase 0: base del repo (uv, ruff, pytest, CI)
- [x] Fase 1: ingesta incremental con crudos versionados
- [x] Fase 2: warehouse con dbt + DuckDB
- [ ] Fase 3: análisis exploratorio
- [ ] Fase 4: modelo de traslado
- [ ] Fase 5: pronóstico
- [ ] Fase 6: análisis de revisiones
- [ ] Fase 7: web con mapa por regiones
- [ ] Fase 8: documentación y metodología

## Cómo correrlo

Hace falta [uv](https://docs.astral.sh/uv/) y un token gratis de la API del INDEC.

```
uv sync
cp .env.example .env      # y pegar el token
uv run pytest
```

## Cómo funciona la ingesta

Un workflow de GitHub Actions corre todos los días y baja los **últimos 6 meses** del IPC y de los precios mayoristas, que es donde el INDEC corrige sus datos provisorios. Una vez por mes baja **toda la historia**.

1. **Cliente** (`src/monitor/cliente.py`): pagina de a 1000 filas con orden fijo, reintenta con espera progresiva si la API devuelve 429 o 5xx, y antes de bajar cuenta cuántas filas tendrían que llegar. Si no llegan todas, no guarda nada.
2. **Validación** (`src/monitor/validacion.py`, con pandera): columnas, tipos, períodos válidos y filas sin repetir. Si algo grave cambia en la API, el pipeline frena. Si aparece una columna o un valor nuevo, solo avisa.
3. **Versionado** (`src/monitor/almacenamiento.py`): se calcula un hash del contenido y **solo se guarda una versión nueva si cambió algo**. Cada versión queda en `data/raw/<dataset>/<ventana>/` en Parquet y se anota en `data/raw/manifest.csv`. Comparando versiones sale el historial de revisiones.

Para probarla en local sin tocar `data/raw`:

```
uv run python -m monitor.ingesta --modo reciente --salida data/prueba
```

## Warehouse (dbt + DuckDB)

dbt lee los Parquet de `data/raw` directamente con DuckDB y arma tres capas:

- **staging**: normaliza lo que viene de la API. Unifica nombres inconsistentes del INDEC ("Estacional" / "Estacionales", "NIVEL GENERAL" / "Nivel general"), pasa el período a fecha y marca los datos que el INDEC no pudo relevar (`///`, por ejemplo restaurantes en la cuarentena de 2020). Hay un modelo con **todas las versiones** y otro con la **última versión de cada dato**.
- **intermediate**: todas las series de índices en un mismo formato, con variación mensual y logarítmica calculadas por nosotros.
- **marts**: `fct_precios` (cada rubro en cada etapa: productor, industria, góndola por región), `fct_revisiones` (cada corrección del INDEC sobre un dato ya publicado), `dim_rubro`, `dim_region` y `dim_provincia`.

Tests: claves únicas, valores aceptados, relaciones entre tablas, que nuestra variación mensual coincida con la que publica el INDEC (±0,1 puntos), que no falten meses, que cada código de la tabla de correspondencia tenga datos, frescura de la ingesta y tests unitarios con datos inventados para la lógica de revisiones y de normalización.

```
cd dbt
uv run dbt build                                # modelos + tests
uv run dbt docs generate && uv run dbt docs serve   # documentacion y linaje
```

**Energía** está como contraste: la tarifa es regulada, así que su relación con el mayorista no es un traslado de mercado.

## Estructura

```
src/monitor/      código del pipeline (cliente de la API, ingesta, validación, modelos)
scripts/          scripts sueltos (exploración inicial de la API)
dbt/              modelos, seeds y tests de dbt
data/raw/         datos crudos versionados
tests/            tests con pytest
docs/             metodología y decisiones
```

## Datos

- **IPC** (`ipc_nacional`): desde abr-2016, 6 regiones + nacional.
- **Precios mayoristas** (`sipm_precios_mayoristas`): desde dic-2015, total del país.

El INDEC no publica precios por provincia, así que el análisis se hace por región.

Fuente: INDEC.
