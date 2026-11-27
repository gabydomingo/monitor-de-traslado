# Monitor de Traslado

Cuando sube el precio mayorista de algo, cuanto de esa suba llega a la gondola y en cuantos meses? Este proyecto lo mide por rubro y por region con datos de la [API del INDEC](https://api.indec.gob.ar/), y pronostica el mes que viene sumando el dolar y las expectativas de inflacion de la [API del BCRA](https://www.bcra.gob.ar/apis-banco-central/). De paso guarda cada version de los datos, algo que la API no hace, para ver si el INDEC corrige lo que publica (hasta ahora no corrigio nada, ver [Revisiones](#revisiones)).

En LinkedIn lo vengo contando como **Efecto Gondola**, y asi se llama la pagina: [efectogondola.vercel.app](https://efectogondola.vercel.app/).

## Estado

- [x] Fase 0: base del repo (uv, ruff, pytest, CI)
- [x] Fase 1: ingesta diaria con los crudos versionados
- [x] Fase 2: warehouse con dbt y DuckDB
- [x] Fase 3: analisis exploratorio
- [x] Fase 4: modelo de traslado
- [x] Fase 5: pronostico
- [x] Fase 6: analisis de las revisiones
- [x] Fase 7: web con mapa por regiones
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

En [`notebooks/02_traslado.ipynb`](notebooks/02_traslado.ipynb), con el codigo en `src/monitor/traslado.py`. Para cada rubro y region, un modelo de rezagos distribuidos sobre precios relativos (a cada serie le resto su inflacion general): el mayorista de este mes y de los 3 anteriores, y 2 meses de la propia gondola. Errores HC3 y correccion por comparaciones multiples. Para carnes, lacteos y pan hay ademas un VAR con la cadena completa: productor, industria y gondola.

Los rezagos son fijos a proposito. Con series simuladas de traslado conocido, elegirlos por BIC y estimar con los mismos datos daba intervalos del 95% que cubrian 84% y, con traslado cero, 16% de falsos positivos. Con rezagos fijos y HC3 cubren 95% y se equivocan 5% (hay un test que lo controla).

Lo que sale (GBA, datos a oct-2026):

- La mayor parte de una suba mayorista llega en el mismo mes (60% en la mediana) y el resto en los 3 meses siguientes.
- Carnes y prendas trasladan mas de 0.8, combustibles y equipamiento del hogar 0.6. Lacteos, aceites, pan y bebidas no se distinguen de cero.
- De 132 estimaciones, 75 son significativas despues de corregir por comparaciones multiples.
- Con inflacion alta se traslada mas en 10 de 17 rubros.
- Entre regiones cambia poco, salvo combustibles (bastante menos en el Noreste y Patagonia) y autos.
- Con el IPIB en vez del IPIM da lo mismo, salvo tabaco y combustibles, que tienen impuestos pesados.

Es un modelo de asociacion, no causal. Los resultados quedan en `data/resultados/`:

```
uv run python -m monitor.traslado
```

## Pronostico

En [`notebooks/03_pronostico.ipynb`](notebooks/03_pronostico.ipynb), con el codigo en `src/monitor/pronostico.py`. Pronostica la inflacion del mes que viene para cada rubro y region, y el nivel general de cada region.

**Cuando y con que.** El pronostico se hace cuando sale el mayorista del mes anterior (desde 2018, entre el 14 y el 23). Para ese momento se sabe el IPC y el mayorista del mes anterior, el REM de fin de mes y el dolar de los dias anteriores a esa publicacion, que salen del calendario real del INDEC. No usa nada mas.

**Modelo.** El promedio de dos:

- un LightGBM global (un solo modelo para las 120 series: 114 de rubros y 6 de nivel general, con rubro y region como variables), que capta relaciones no lineales;
- una regresion lineal por serie (ARX), que a diferencia de los arboles puede extrapolar un salto del dolar que nunca vio, como el de diciembre de 2023.

Mitad y mitad, sin ajustar pesos, para no sobreajustar.

**Validacion.** Origen movil sobre 36 meses: cada mes se entrena solo con lo anterior. Las decisiones las tome mirando nov-23 a oct-25. El ultimo anio quedo guardado como prueba final y se miro una sola vez.

| MAE (pp de inflacion mensual) | naive | ARX | LightGBM sin BCRA | LightGBM | combinado |
|---|---|---|---|---|---|
| 36 meses | 2.88 | 2.48 | | 2.32 | **2.24** |
| desarrollo (nov-23 a oct-25) | 3.46 | 2.95 | 3.01 | 2.77 | **2.65** |
| prueba final (nov-25 a oct-26) | 1.72 | 1.53 | 1.42 | 1.40 | 1.42 |

La tabla es solo de los rubros; el nivel general va aparte, mas abajo.

- El combinado le gana al naive por un 22% y la diferencia es significativa (Diebold-Mariano, p = 0.001).
- El dolar y el REM mejoran los meses con shock (dic-23 a 2024) y no cambian nada en los tranquilos: en la prueba final, un anio calmo, casi empatan. Es un seguro, no una mejora en todos los meses. La evidencia de la mejora sale del tramo donde tome las decisiones, asi que puede estar algo inflada.
- Dos bandas, de 80% y 90%, que salen de cuantiles de LightGBM calibrados con conformal por rubro y se agrandan cuando el dolar se mueve a principio de mes. Cubren 80% y 90% en total. En dic-2023 la del 80% paso de cubrir 36% a 50% gracias al dolar, sin ensanchar los meses tranquilos (en 2026 miden 4.6 y 6.2 pp).
- Lo que mas pesa es el REM y despues el mayorista del mes anterior. La region casi no aporta.
- Los saltos grandes de verduras (clima, cosecha) quedan fuera del intervalo igual.
- **Nivel general.** Entra como una serie mas por region, con el IPIM general como mayorista, para que la web tenga un pronostico de la inflacion de cada region. En los 36 meses erra 1.02 pp contra 1.34 del naive, pero la diferencia no es significativa (p = 0.16) y en la prueba final pierde: 0.59 contra 0.37. Con la inflacion quieta, repetir el dato del mes pasado es muy dificil de mejorar. No lo corregi mirando la prueba final; la web muestra los dos para que se vea.

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

Los pdf no se suben al repo (pesan 250 MB). La ingesta diaria corre `informes calendario`, que suma solo las fechas de publicacion nuevas, sin bajar pdf. Se suben el listado, con el hash de cada pdf, y lo que se saco de ellos (`data/informes/`). En dbt, `fct_primer_dato` cruza cada primer dato con el valor de hoy en la API.

- En mas de 20 mil datos (IPC desde 2017, mayorista desde 2018, por division y region), el INDEC no corrigio ninguna variacion mensual al decimal que publica. El "provisorio" del mayorista nunca cambio.
- Por eso el backtest del pronostico no esta sesgado por usar datos ya revisados.
- Restaurantes de abril a julio de 2020 tiene la variacion del nivel general: se imputo porque estaban cerrados y nunca se reemplazo.
- El mayorista se publica entre el 14 y el 23. Con ese calendario encontre una filtracion chica en el pronostico (usaba el dolar hasta el 15 y 4 meses salio antes): ahora el corte sale de la fecha real.

La ingesta sigue guardando cada version, asi que si el INDEC corrige algo de aca en adelante va a aparecer en `fct_revisiones`.

## Corrida mensual

`.github/workflows/modelo.yml` corre despues de cada ingesta. Casi todos los dias termina enseguida porque no hay nada nuevo. Cuando ya salieron el IPC y el mayorista del mes y hay dolar hasta el 13, actualiza el warehouse, corre el traslado y el pronostico, y guarda el pronostico en `data/resultados/registro_pronosticos.csv`. Despues, todos los dias, regenera los datos de la web (`data/web`); si cambiaron, los sube y Vercel vuelve a publicar la pagina.

Ese registro no se pisa: es lo que el modelo dijo en su momento, con la version de los datos y del modelo que uso. Si se suma una serie nueva (como el nivel general), entran solo las filas que no estaban. Cuando el INDEC publica el dato se puede medir el error real, no el de un backtest con datos ya revisados.

Todo junto tarda menos de un minuto. El backtest reparte los meses entre los nucleos que haya.

```
uv run python -m monitor.mensual
```

## Web

La pagina publica se llama Efecto Gondola. Es un sitio estatico en Next.js (`web/`), sin servidor ni base de datos.

- **Datos.** `monitor.web` arma cuatro JSON en `data/web` a partir del warehouse y de `data/resultados`. El resumen (unos 55 KB) va dentro de la pagina; series, backtest e historial (registro en vivo y calendario) los baja el navegador despues, y los dos ultimos recien cuando se llega a esa parte. Asi la primera carga pesa la mitad. El contrato son los modelos de pydantic de `src/monitor/web.py`: de ahi sale `data/web/esquema.json` y de ese esquema los tipos de TypeScript (`web/lib/tipos.ts`). Si el contrato cambia y los tipos no, falla el CI.
- **Mapa.** Regiones del IPC con limites del IGN (SIG 250, via CONAE), en GeoJSON por [mgaitan/departamentos_argentina](https://github.com/mgaitan/departamentos_argentina). GBA es la ciudad mas los 24 partidos del conurbano; el resto de Buenos Aires va en Pampeana. Se simplifica con mapshaper (`npm run geo`) y se dibuja en el build con d3-geo: al navegador llegan solo los trazos.
- **Graficos.** Observable Plot. El pronostico va en gris tinta, nunca en el color de una region. Energia siempre en gris pizarra punteado y con la aclaracion de tarifa regulada.
- **Publicacion.** [efectogondola.vercel.app](https://efectogondola.vercel.app/), en Vercel con raiz en `web/`. Solo hace build si cambio algo en `web/` o en `data/web` desde el ultimo deploy (`web/vercel.json`).
- **Cualquier mes.** El panel de cada region tiene un selector de mes desde enero de 2017, que tambien cambia la lista de regiones debajo del mapa. Se puede compartir un mes con el link: `efectogondola.vercel.app/?mes=2023-12`. La franja de arriba y el pronostico siempre muestran lo ultimo.
- **Entre un mes y otro.** Cuando sale el IPC del mes pronosticado y todavia no el mayorista, el pronostico que hay ya es viejo: la pagina lo muestra como "dijo y fue" y avisa cuando sale el siguiente.

```
uv run python -m monitor.web   # regenera data/web
cd web
npm install
npm run dev                     # http://localhost:3000
npm run tipos                   # tipos desde el esquema
npm run build                   # sitio estatico en web/out
```

## Carpetas

```
src/monitor/   el pipeline
scripts/       la exploracion inicial de la API
notebooks/     analisis
dbt/           modelos, seeds y tests
data/raw/      crudos versionados
data/resultados/  resultados del modelo
data/informes/ listado y primeros datos de los informes del indec
data/web/      los json que lee la pagina
web/           la pagina (Next.js estatico)
tests/         tests de python
docs/          metodologia (fase 8)
PRODUCT.md     para quien es la pagina y que tiene que lograr
DESIGN.md      el sistema visual de la pagina (colores, letras, graficos)
```

## Datos

- IPC (`ipc_nacional`): desde abril de 2016, 6 regiones mas el total nacional.
- Precios mayoristas (`sipm_precios_mayoristas`): desde diciembre de 2015, total del pais.
- BCRA, principales variables: dolar mayorista de referencia (variable 5, diario) y mediana del REM a 12 meses (variable 29, mensual desde junio de 2016).
- Informes tecnicos del INDEC (pdf): el primer dato publicado y la fecha de publicacion de cada mes.

El INDEC no publica precios por provincia, por eso todo va por region.

Fuentes: INDEC y BCRA. Limites del mapa: Instituto Geografico Nacional (SIG 250, via CONAE), convertidos por [mgaitan/departamentos_argentina](https://github.com/mgaitan/departamentos_argentina).
