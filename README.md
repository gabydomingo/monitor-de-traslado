# Monitor de Traslado

Cuando sube el precio mayorista de algo, cuanto de esa suba llega a la gondola y en cuantos meses? Este proyecto lo mide por rubro y por region con datos de la [API del INDEC](https://api.indec.gob.ar/), y pronostica el mes que viene sumando el dolar y las expectativas de inflacion de la [API del BCRA](https://www.bcra.gob.ar/apis-banco-central/). De paso guarda cada correccion que hace el INDEC a sus datos provisorios, algo que la API no guarda.

En LinkedIn lo vengo contando como **Efecto Gondola**. Esta en construccion.

## Estado

- [x] Fase 0: base del repo (uv, ruff, pytest, CI)
- [x] Fase 1: ingesta diaria con los crudos versionados
- [x] Fase 2: warehouse con dbt y DuckDB
- [x] Fase 3: analisis exploratorio
- [x] Fase 4: modelo de traslado
- [x] Fase 5: pronostico
- [x] Fase 6: analisis de las revisiones
- [ ] Fase 7: web con mapa por regiones
- [ ] Fase 8: metodologia y documentacion

## Correrlo

Hace falta [uv](https://docs.astral.sh/uv/) y un token de la API del INDEC (es gratis, se saca registrandose en la pagina). La del BCRA no pide token.

```
uv sync
cp .env.example .env      # pegar el token
uv run pytest
```

## Ingesta

Un workflow de GitHub Actions baja todos los dias los ultimos 6 meses del IPC y de los precios mayoristas, que es donde el INDEC corrige, y del BCRA el dolar mayorista (com. A 3500) y la mediana del REM. Una vez por mes baja toda la historia.

- `src/monitor/cliente.py`: un cliente para cada API con los mismos reintentos (429 o 5xx). Pagina siempre con el mismo orden y antes de bajar cuenta cuantas filas tendrian que llegar. Si no llegan todas no guarda nada.
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
- **marts**: `fct_precios` (cada rubro en cada etapa: productor, industria y gondola por region), `fct_revisiones` (cada dato que el INDEC corrigio), `fct_bcra_mensual` (dolar y REM por mes), `dim_rubro`, `dim_region` y `dim_provincia`.

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

## Pronostico

En [`notebooks/03_pronostico.ipynb`](notebooks/03_pronostico.ipynb), con el codigo en `src/monitor/pronostico.py`. Pronostica la inflacion del mes que viene para cada rubro y region.

**Cuando y con que.** El pronostico se hace cuando sale el mayorista del mes anterior (desde 2018, entre el 14 y el 23). Para ese momento se sabe el IPC y el mayorista del mes anterior, el REM de fin de mes y el dolar de los dias anteriores a esa publicacion, que salen del calendario real del INDEC. No usa nada mas.

**Modelo.** El promedio de dos:

- un LightGBM global (un solo modelo para las 114 series, con rubro y region como variables), que capta relaciones no lineales;
- una regresion lineal por serie (ARX), que a diferencia de los arboles puede extrapolar un salto del dolar que nunca vio, como el de diciembre de 2023.

Mitad y mitad, sin ajustar pesos, para no sobreajustar.

**Validacion.** Origen movil sobre 36 meses: cada mes se entrena solo con lo anterior. Las decisiones las tome mirando nov-23 a oct-25. El ultimo anio quedo guardado como prueba final y se miro una sola vez.

| MAE (pp de inflacion mensual) | naive | ARX | LightGBM sin BCRA | LightGBM | combinado |
|---|---|---|---|---|---|
| 36 meses | 2.88 | 2.48 | | 2.36 | **2.24** |
| desarrollo (nov-23 a oct-25) | 3.47 | 2.95 | 3.02 | 2.82 | **2.65** |
| prueba final (nov-25 a oct-26) | 1.72 | 1.53 | 1.42 | 1.43 | 1.43 |

- El combinado le gana al naive por un 22% y la diferencia es significativa (Diebold-Mariano, p = 0.001).
- El dolar y el REM mejoran los meses con shock (dic-23 a 2024) y no cambian nada en los tranquilos: en la prueba final, un anio calmo, empatan. Es un seguro, no una mejora en todos los meses. La evidencia de la mejora sale del tramo donde tome las decisiones, asi que puede estar algo inflada.
- Los intervalos del 80% salen de cuantiles de LightGBM calibrados con conformal por rubro: cubren el 81% en total y entre 78% y 84% en cada rubro.
- Lo que mas pesa es el REM y despues el mayorista del mes anterior. La region casi no aporta.
- Los saltos grandes de verduras (clima, cosecha) quedan fuera del intervalo igual.

El MASE da arriba de 1 para casi todos, porque la escala sale de anios con menos inflacion. Por eso la comparacion va contra el naive del mismo periodo.

```
uv run python -m monitor.pronostico
```

## Revisiones

En [`notebooks/04_revisiones.ipynb`](notebooks/04_revisiones.ipynb). La API solo tiene el dato vigente, asi que para ver cuanto corrige el INDEC reconstrui la historia con los informes de prensa, que quedan online tal como salieron:

```
uv run python -m monitor.informes bajar      # listado y pdf del mayorista y del ipc
uv run python -m monitor.informes procesar   # saca la variacion mensual de cada pdf
```

Los pdf no se suben al repo (pesan 250 MB). Se suben el listado, con el hash de cada pdf, y lo que se saco de ellos (`data/informes/`). En dbt, `fct_primer_dato` cruza cada primer dato con el valor de hoy en la API.

- En mas de 20 mil datos (IPC desde 2017, mayorista desde 2018, por division y region), el INDEC no corrigio ninguna variacion mensual al decimal que publica. El "provisorio" del mayorista nunca cambio.
- Por eso el backtest del pronostico no esta sesgado por usar datos ya revisados.
- Restaurantes de abril a julio de 2020 tiene la variacion del nivel general: se imputo porque estaban cerrados y nunca se reemplazo.
- El mayorista se publica entre el 14 y el 23. Con ese calendario encontre una filtracion chica en el pronostico (usaba el dolar hasta el 15 y 4 meses salio antes): ahora el corte sale de la fecha real.

La ingesta sigue guardando cada version, asi que si el INDEC corrige algo de aca en adelante va a aparecer en `fct_revisiones`.

## Corrida mensual

`.github/workflows/modelo.yml` corre despues de cada ingesta. Casi todos los dias termina enseguida porque no hay nada nuevo. Cuando ya salieron el IPC y el mayorista del mes y pasaron 15 dias de dolar, actualiza el warehouse, corre el traslado y el pronostico, y guarda el pronostico en `data/resultados/registro_pronosticos.csv`.

Ese registro no se pisa: es lo que el modelo dijo en su momento, con la version de los datos y del modelo que uso. Cuando el INDEC publica el dato se puede medir el error real, no el de un backtest con datos ya revisados.

Todo junto tarda menos de un minuto. El backtest reparte los meses entre los nucleos que haya.

```
uv run python -m monitor.mensual
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
- BCRA, principales variables: dolar mayorista de referencia (variable 5, diario) y mediana del REM a 12 meses (variable 29, mensual desde junio de 2016).
- Informes tecnicos del INDEC (pdf): el primer dato publicado y la fecha de publicacion de cada mes.

El INDEC no publica precios por provincia, por eso todo va por region.

Fuentes: INDEC y BCRA.
