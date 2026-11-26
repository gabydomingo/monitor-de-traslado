# Monitor de Traslado

¿Cuánto de una suba de precios mayoristas llega a la góndola, y en cuántos meses? Este proyecto lo mide por rubro y por región con datos oficiales de la [API del INDEC](https://api.indec.gob.ar/), y guarda además cada corrección que el INDEC hace a sus datos provisorios.

> Proyecto en construcción. En LinkedIn lo cuento como **Efecto Góndola**.

## Estado

- [x] Fase 0: base del repo (uv, ruff, pytest, CI)
- [ ] Fase 1: ingesta incremental con crudos versionados
- [ ] Fase 2: warehouse con dbt + DuckDB
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
