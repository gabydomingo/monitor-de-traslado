# Model card: pronóstico de inflación mensual por rubro y región

Ficha del modelo que pronostica la inflación del mes en curso en [Efecto Góndola](https://efectogondola.vercel.app/). Cómo se arma está en la [metodología](metodologia.md); acá va qué hace, cuánto le erra y para qué no sirve.

## Qué hace

Pronostica la variación mensual del IPC del mes en curso para 19 rubros y el nivel general, en las 6 regiones del INDEC: 120 series. Cada pronóstico trae dos bandas, la del 80% y la del 90%.

- **Cuándo:** el día que el INDEC publica el mayorista del mes anterior, entre el 14 y el 23. El IPC de ese mes sale el mes siguiente, entre el 10 y el 17.
- **Con qué:** IPC y mayorista hasta el mes anterior, dólar de los primeros días del mes, REM, rubro, región y mes del año. Nada que no se supiera ese día.
- **Modelo:** promedio de un LightGBM global (300 árboles, 15 hojas) y una regresión lineal por serie. Bandas con cuantiles de LightGBM calibrados por conformal y agrandados según el movimiento del dólar.
- **Versión:** la del modelo y la de los datos quedan anotadas en cada fila del registro (`data/resultados/registro_pronosticos.csv`).

## Para qué sirve

- Tener una idea, antes del dato oficial, de por dónde va a andar la inflación de un rubro en una región, con su incertidumbre.
- Ver qué rubros se mueven antes o después que el mayorista.
- Comparar mes a mes lo que dijo contra lo que pasó, en el registro en vivo.

## Para qué no sirve

- **No es un dato oficial.** El oficial es el del INDEC.
- **No es para decisiones financieras ni contractuales:** ajustes de precios, inversiones, contratos.
- **No anticipa shocks.** Una devaluación o un cambio de tarifas que todavía no pasó no está en los datos.
- **Nada sobre energía.** "Electricidad, gas y combustibles" del hogar son tarifas reguladas: el pronóstico existe, pero depende de decisiones de gobierno y queda solo como contraste.

## Cuánto le erra

Con datos hasta octubre de 2026 (el notebook 03 los recalcula). Error medio absoluto, en puntos de inflación mensual. Prueba de origen móvil: cada mes se pronostica entrenando solo con lo anterior. "Naive" es repetir el dato del mes anterior.

**Rubros (114 series)**

| | naive | ARX | LightGBM | combinado |
|---|---|---|---|---|
| 36 meses (nov-23 a oct-26) | 2.88 | 2.48 | 2.32 | **2.24** |
| prueba final (nov-25 a oct-26) | 1.72 | 1.53 | 1.40 | 1.42 |

- Erra 22% menos que el naive y la diferencia es significativa (Diebold-Mariano, p = 0.001). Le gana todos los años.
- En la prueba final, que se miró una sola vez, sigue ganándole al naive (1.42 contra 1.72).
- Por rubro, lo más fácil es equipamiento del hogar, pan y librería (1.3 pp). Lo más difícil es verduras (6.0), energía (4.7), frutas (3.5) y combustibles (3.1).

**Nivel general (6 series)**

| | naive | combinado |
|---|---|---|
| 36 meses | 1.34 | **1.02** |
| prueba final | **0.37** | 0.59 |

- En el total gana, pero la diferencia no es significativa (p = 0.16): casi toda la ventaja sale de 2023 y 2024.
- Con la inflación quieta (2025 y 2026) pierde contra repetir el dato anterior. Se probaron arreglos, pero mirando la prueba final, así que no se aplicó ninguno. La web muestra los dos números.

**Bandas**

| | prometido | rubros | nivel general |
|---|---|---|---|
| banda del 80% | 80% | 80% | 78% |
| banda del 90% | 90% | 90% | 91% |

En 2026 la banda del 80% mide en promedio 4.6 pp en los rubros y 1.7 pp en el nivel general.

## Dónde falla

- **Devaluaciones bruscas.** En diciembre de 2023 la banda del 80% cubrió la mitad de los casos. Sin el ajuste por dólar cubría 36%.
- **Frutas y verduras.** Dependen del clima y la cosecha; los saltos grandes quedan afuera igual.
- **Nivel general en meses tranquilos.** Ver arriba.
- **Cambios de régimen.** El modelo aprende de 2017 en adelante. Una situación sin precedentes en esos años (por ejemplo, deflación sostenida) no está representada.

## Datos de entrenamiento

- IPC por región y rubro desde 2017, mayorista desde diciembre de 2015, dólar y REM del BCRA. Todo público.
- El INDEC no corrigió ninguna variación mensual en más de 20 mil datos revisados, así que el backtest usa los mismos números que había en cada momento.
- No hay datos personales.

## Cómo se controla

- **Tests** que verifican que ninguna variable use información del futuro, que las bandas cubran lo que prometen en datos simulados y que el registro no se reescriba.
- **Registro en vivo:** cada pronóstico queda guardado antes del dato y se compara cuando sale. Arrancó en noviembre de 2026; con los meses va a ser la medida más honesta del error.
- **Corrida automática** con GitHub Actions; cada corrida deja un resumen con el error del backtest.

## Contacto

Gabriel Domingo, en [LinkedIn](https://www.linkedin.com/in/gabydomingo/) y [GitHub](https://github.com/gabydomingo).
