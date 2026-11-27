# Metodología

Cómo se arma cada número de [Efecto Góndola](https://efectogondola.vercel.app/). El detalle con código está en las notebooks; acá va lo necesario para entender qué se hizo, por qué y hasta dónde se puede confiar.

## La pregunta

Cuando sube el precio mayorista de algo, cuánto de esa suba llega al precio que paga la gente y en cuánto tiempo. Y con eso, qué se puede esperar para el mes que viene.

## Datos

| Fuente | Qué | Desde | Frecuencia |
|---|---|---|---|
| INDEC, API | IPC por región y rubro (la góndola) | abr-2016 | mensual |
| INDEC, API | Sistema de Índices de Precios Mayoristas: IPIM, IPIB y precios del productor | dic-2015 | mensual |
| INDEC, informes de prensa | el primer dato publicado de cada mes y la fecha en que salió | 2017 | mensual |
| BCRA, API | dólar mayorista de referencia (Com. A 3500) | 2015 | diario |
| BCRA, API | mediana del REM a 12 meses | jun-2016 | mensual |

**Regiones.** El INDEC mide el IPC en seis regiones, no por provincia: GBA (la ciudad y los 24 partidos del conurbano), Pampeana, Noreste, Noroeste, Cuyo y Patagonia. El mayorista es uno solo para todo el país, así que el traslado compara un mayorista nacional con una góndola regional.

**Rubros.** 19 rubros del IPC que tienen un equivalente razonable en los índices mayoristas, más el nivel general. Cada uno tiene una calidad de correspondencia (alta, media o baja) en `dbt/seeds`. Carnes, lácteos, pan y cereales, frutas y verduras tienen además precio del productor.

**Energía.** "Electricidad, gas y combustibles" del hogar está como contraste: son tarifas reguladas, así que lo que suben no es traslado de mercado. Aparece en todos lados, marcado, pero no se usa para sacar conclusiones.

## Pipeline

1. **Ingesta** (GitHub Actions, todos los días a las 20:23). Baja los últimos 6 meses del INDEC y del BCRA; una vez por mes, toda la historia. Antes de guardar valida columnas, tipos y repetidos con pandera, y cuenta que lleguen todas las filas. Cada versión distinta queda guardada en parquet con un hash, así que nada se pisa.
2. **Warehouse** (dbt sobre DuckDB). Normaliza nombres y categorías, usa la última versión de cada dato y arma las tablas finales. 80 controles: claves únicas, meses sin huecos, que la variación calculada dé igual que la del INDEC y que la ingesta esté al día.
3. **Modelos.** Cuando ya salió el mayorista del mes, corren el traslado y el pronóstico, y el pronóstico se guarda en un registro que no se reescribe.
4. **Web.** `monitor.web` arma los json que lee la página, con un contrato en pydantic que también genera los tipos de TypeScript. Si cambió algo, Vercel publica de nuevo.

## Traslado

**Modelo.** Para cada rubro y región, una regresión con rezagos distribuidos:

```
góndola relativa(t) = a + b0 mayorista relativo(t) + ... + b3 mayorista relativo(t-3)
                        + c1 góndola relativa(t-1) + c2 góndola relativa(t-2) + error
```

"Relativo" quiere decir que a cada serie se le resta la inflación general del mes. Sin eso, mayorista y góndola parecen moverse igual en todos los rubros solo porque la inflación mueve todo junto.

**Lo que se informa.**

- **Traslado de largo plazo:** qué parte de una suba relativa del mayorista termina en la góndola, sumando todos los meses. 100% es que llega toda.
- **Por mes:** cuánto llega el mismo mes y en cada uno de los tres siguientes.
- **Intervalo del 95%** y si es distinto de cero.

**Decisiones y por qué.**

- **Rezagos fijos (3 del mayorista, 2 de la góndola).** Elegirlos con BIC y estimar con los mismos datos daba intervalos que, en series simuladas con traslado conocido, cubrían 84% en vez de 95%, y 16% de falsos positivos con traslado cero.
- **Errores robustos HC3.** Con rezagos fijos y HC3, la simulación da 95% de cobertura y 5% de falsos positivos. Hay un test que lo controla.
- **Corrección por comparaciones múltiples (Benjamini-Hochberg).** Son 132 estimaciones: sin corregir, algunas saldrían "significativas" por azar. En la web, las que no pasan van en gris.

**Extras.**

- **Por época** (solo GBA): inflación baja (2017 y desde 2025), media (2018-2021) y alta (2022-2024).
- **Cadena** (carnes, lácteos, pan): un VAR con productor, industria y góndola, que da la respuesta acumulada de la góndola a una suba en cada eslabón.

**Resultado.** 75 de 132 estimaciones son distintas de cero después de corregir. La mayor parte llega el mismo mes (60% en la mediana). Carnes y prendas trasladan más de 0.8; combustibles y equipamiento del hogar, alrededor de 0.6. Lácteos, aceites, pan y bebidas no se distinguen de cero.

## Pronóstico

**Cuándo se hace.** El mismo mes que se pronostica, el día que el INDEC publica el mayorista del mes anterior (del 14 al 23 según el mes). A esa altura se conoce:

- el IPC y el mayorista del mes anterior;
- el REM de fin de mes;
- el dólar hasta el día anterior a esa publicación, con el corte tomado del calendario real del INDEC.

No usa nada que no se supiera ese día.

**Variables.**

- rezagos de la propia serie (1, 2, 3 y 12 meses) y su media de 12;
- mayorista del rubro (1 y 2 meses);
- inflación general y mayorista general;
- dólar del mes anterior y de los primeros días del mes;
- REM;
- rubro, región y mes.

**Modelos.** El pronóstico es el promedio, mitad y mitad, de:

- un **LightGBM global**: un solo modelo para las 120 series (114 de rubros y 6 de nivel general);
- una **regresión lineal por serie (ARX)**, que a diferencia de los árboles puede extrapolar un salto del dólar que nunca vio.

Los pesos no se ajustaron, para no sobreajustar.

**Validación.** Origen móvil sobre 36 meses (nov-2023 a oct-2026): para cada mes se entrena solo con lo anterior y se pronostica ese mes. Las decisiones se tomaron mirando hasta oct-2025; los 12 meses siguientes quedaron como prueba final.

**Bandas.**

- Salen de cuantiles de LightGBM corregidos con conformal: con los últimos 12 meses de cada rubro se mide cuánto se erró y se ajusta el ancho para que cubran lo que prometen.
- Se agrandan cuando el dólar se mueve en los primeros días del mes.
- Hay dos: la del 80% (8 de cada 10) y la del 90%.

**Comparación.** Contra "naive": suponer que el mes que viene es igual a este. La diferencia se prueba con Diebold-Mariano.

Los resultados están en el [model card](model_card.md).

## Revisiones

La API del INDEC solo tiene el dato vigente. Para ver si el INDEC corrige lo que publica, se bajaron 218 informes de prensa (IPC desde 2017, mayorista desde 2018) y se sacó de cada PDF la variación mensual tal como salió. Después se compararon 20.363 datos con lo que muestra hoy la API.

No hay ninguna diferencia al decimal que se publica. La única rareza es restaurantes, de abril a julio de 2020: el INDEC imputó la variación del nivel general porque estaban cerrados.

Eso importa para el pronóstico, porque el backtest usa los mismos datos que había en cada momento. Y como la ingesta guarda cada versión, si el INDEC corrige algo de acá en adelante va a quedar registrado.

## Registro en vivo

El backtest dice cuánto le hubiera errado el modelo. El registro dice cuánto le erra de verdad.

Cada pronóstico se guarda el día que se hace, con la versión del modelo y de los datos, y no se toca más. Cuando sale el IPC, la web lo compara. Arrancó en noviembre de 2026.

## Límites

- **Es asociación, no causalidad.** El traslado medido puede incluir otras cosas que se mueven junto con el mayorista.
- **La correspondencia es aproximada en algunos rubros.** Equipamiento del hogar, energía y cuidado personal tienen calidad baja o media.
- **Mayorista nacional contra góndola regional.** Las diferencias entre regiones salen de la góndola, no de mayoristas distintos.
- **Pocos datos por época.** Las comparaciones por régimen de inflación tienen intervalos anchos.
- **Pronóstico del nivel general.** En meses tranquilos no le gana a repetir el último dato (ver el model card).

## Reproducirlo

```
uv sync
cp .env.example .env          # token de la API del INDEC
uv run python -m monitor.ingesta --modo completo
cd dbt && uv run dbt build && cd ..
uv run python -m monitor.traslado
uv run python -m monitor.pronostico
uv run python -m monitor.web
```

Notebooks: [exploración](../notebooks/01_eda.ipynb), [traslado](../notebooks/02_traslado.ipynb), [pronóstico](../notebooks/03_pronostico.ipynb) y [revisiones](../notebooks/04_revisiones.ipynb).
