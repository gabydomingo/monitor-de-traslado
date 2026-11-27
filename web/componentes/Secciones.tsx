import type { Resumen } from "@/lib/tipos";
import { fechaLarga, mesLargo, nombreMes, num } from "@/lib/formato";
import { Calendario } from "./Calendario";

const REPO = "https://github.com/gabydomingo/monitor-de-traslado";
const NOTEBOOK = (n: string) => `${REPO}/blob/main/notebooks/${n}.ipynb`;

export function Cabecera({ resumen }: { resumen: Resumen }) {
  return (
    <header className="mx-auto flex max-w-[1200px] flex-wrap items-end justify-between gap-x-10 gap-y-2 px-4 pt-6 pb-4 md:px-8 md:pt-8">
      <div>
        <h1 className="text-[2.5rem] leading-none font-bold tracking-[-0.02em] md:text-[3.25rem]">
          Efecto Góndola
        </h1>
        <p className="mt-2 max-w-[52ch] text-[1.0625rem] text-tinta-2">
          Cuánto de lo que sube en el mayorista llega al precio que pagás, región por región, y qué
          se espera para el mes que viene.
        </p>
      </div>
      <p className="text-sm text-tinta-2">
        Datos del INDEC hasta {mesLargo(resumen.meta.ultimoMes)}
      </p>
    </header>
  );
}

// los engranajes: que pasa solo, todos los dias, para que esta pagina este al dia
export function ComoSeActualiza({ resumen }: { resumen: Resumen }) {
  const { meta, automatizacion: a } = resumen;
  return (
    <section id="como-se-actualiza" aria-labelledby="titulo-actualiza" className="scroll-mt-4 border-t border-tinta">
      <div className="mx-auto grid max-w-[1200px] gap-x-12 gap-y-8 px-4 py-10 md:px-8 md:py-14 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
        <div>
          <h2 id="titulo-actualiza" className="text-[2rem] leading-tight font-semibold">
            Cómo se actualiza sola esta página
          </h2>
          <p className="mt-3 max-w-[60ch]">
            Nadie la toca a mano. Cada pieza le pasa su resultado a la siguiente, y si en un paso no
            hay nada nuevo, la cadena se corta ahí sin cambiar nada.
          </p>
          <ol className="mt-6 border-t border-filete">
            {[
              [
                "Todos los días, 20:23",
                "Un proceso automático en GitHub baja el IPC y los precios mayoristas de la API del INDEC, y el dólar y las expectativas de inflación de la del Banco Central. Cada versión queda guardada con su fecha.",
              ],
              [
                "Enseguida",
                "Arma la base de datos y corre más de 80 controles: que no falten meses, que no haya datos repetidos ni vacíos, que las series cierren.",
              ],
              [
                "Cuando sale el mayorista del mes",
                "Vuelve a estimar el traslado y hace el pronóstico del mes en curso. Lo guarda en un registro que no se puede reescribir, antes de que salga el dato.",
              ],
              [
                "Si cambió algo",
                "Regenera los datos de esta página y la vuelve a publicar. Cuando sale el IPC, el registro se completa solo con lo que pasó.",
              ],
            ].map(([cuando, que], i) => (
              <li key={i} className="grid gap-x-6 gap-y-1 border-b border-filete py-4 sm:grid-cols-[12rem_minmax(0,1fr)]">
                <p className="font-serif text-[1.0625rem] font-semibold">
                  <span className="mr-2 text-tinta-2">{i + 1}</span>
                  {cuando}
                </p>
                <p className="max-w-[60ch]">{que}</p>
              </li>
            ))}
          </ol>
        </div>

        <div className="lg:pt-14">
          <dl className="grid grid-cols-2 border-t border-tinta">
            <Dato titulo="Datos nuevos por última vez" valor={fechaLarga(meta.datosNuevos)} ancho />
            <Dato titulo="Meses de IPC" valor={num(a.mesesIpc)} nota={`desde ${mesLargo(a.primerMes)}`} />
            <Dato titulo="Versiones guardadas" valor={num(a.descargas)} nota="descargas con algo nuevo" />
            <Dato
              titulo="Meses en el registro en vivo"
              valor={num(a.mesesRegistrados)}
              nota={a.primerRegistro ? `desde ${mesLargo(a.primerRegistro)}` : "todavía ninguno"}
            />
            <Dato titulo="Próximo IPC" valor={`${meta.proximoIpc.diaDesde} al ${meta.proximoIpc.diaHasta} de ${nombreMes(meta.proximoIpc.publicacion)}`} nota={`el de ${nombreMes(meta.proximoIpc.mes)}`} />
          </dl>
          <p className="mt-4 max-w-[60ch] text-[0.9375rem] text-tinta-2">
            Algunas partes todavía tienen pocos datos: el registro en vivo arrancó hace poco y suma un
            mes cada vez. Con el tiempo la comparación de lo que dijo contra lo que pasó va a pesar
            más que la prueba hacia atrás.
          </p>
          <p className="mt-3 text-[0.8125rem] text-tinta-2">
            Versión del modelo {meta.versionModelo}. <a href={`${REPO}/actions`}>Ver las corridas</a>.
          </p>
        </div>
      </div>
    </section>
  );
}

function Dato({ titulo, valor, nota, ancho = false }: { titulo: string; valor: string; nota?: string; ancho?: boolean }) {
  return (
    <div className={`border-b border-filete py-3 pr-3 ${ancho ? "col-span-2" : ""}`}>
      <dt className="text-sm text-tinta-2">{titulo}</dt>
      <dd className="font-serif text-[1.375rem] leading-tight font-semibold">{valor}</dd>
      {nota && <dd className="text-[0.8125rem] text-tinta-2">{nota}</dd>}
    </div>
  );
}

export function ElIndecNoCorrige({ resumen }: { resumen: Resumen }) {
  const r = resumen.revisiones;
  return (
    <section id="revisiones" aria-labelledby="titulo-revisiones" className="border-t border-tinta">
      <div className="mx-auto max-w-[1200px] px-4 py-10 md:px-8 md:py-14">
        <article className="mx-auto max-w-[65ch]">
          <h2 id="titulo-revisiones" className="text-[2.25rem] leading-tight font-semibold md:text-[2.75rem]">
            El INDEC no corrige
          </h2>
          <div className="mt-5 space-y-4 font-serif text-[1.125rem] leading-relaxed">
            <p>
              Una sospecha común con las estadísticas oficiales es que el primer dato sale de una
              manera y después, sin hacer ruido, se cambia. Para comprobarlo hizo falta reconstruir
              lo que el INDEC dijo el día que publicó cada mes.
            </p>
            <p>
              Se bajaron los {num(r.informes)} informes de prensa del IPC y de los precios
              mayoristas, de {mesLargo(r.desde)} a {mesLargo(r.hasta)}. De cada uno salen las
              variaciones mensuales tal como se publicaron, y cada una se compara con lo que la API
              del INDEC muestra hoy: {num(r.comparados)} datos, uno por uno.
            </p>
            <p className="font-semibold">
              {r.corregidos === 0
                ? "No hay ni una diferencia."
                : `Hay ${num(r.corregidos)} diferencias.`}
            </p>
            <p>
              El INDEC no revisa sus variaciones mensuales después de publicarlas. Eso tiene una
              consecuencia práctica para este monitor: la prueba hacia atrás del pronóstico usa
              los mismos datos que había en su momento, así que no está inflada por datos
              corregidos después. Además, la ingesta guarda cada versión que baja: si algún día el
              INDEC cambia un número, queda registrado.
            </p>
          </div>
          <Calendario />
        </article>
      </div>
    </section>
  );
}

export function Metodologia({ resumen }: { resumen: Resumen }) {
  const lineas: [string, React.ReactNode][] = [
    [
      "Rubros",
      "19 rubros del IPC que tienen un equivalente en los precios mayoristas, más el nivel general. Electricidad y gas son tarifas reguladas y quedan como contraste.",
    ],
    [
      "Traslado",
      "Regresión con rezagos del mayorista y de la góndola, sobre precios relativos a la inflación general. Errores robustos (HC3) y corrección por comparaciones múltiples (Benjamini-Hochberg): por eso hay rubros en gris.",
    ],
    [
      "Pronóstico",
      "Promedio de LightGBM y una regresión por serie. Bandas por conformal, calibradas por rubro con los 12 meses anteriores y agrandadas cuando se mueve el dólar. Probado mes a mes sobre los últimos 36, entrenando solo con lo anterior a cada mes.",
    ],
    [
      "Límites",
      "Es asociación, no causalidad. La correspondencia entre mayorista y góndola es aproximada en algunos rubros. El mayorista es nacional; la góndola, regional.",
    ],
  ];
  return (
    <section id="metodologia" aria-labelledby="titulo-metodologia" className="border-t border-tinta">
      <div className="mx-auto max-w-[1200px] px-4 py-10 md:px-8 md:py-14">
        <h2 id="titulo-metodologia" className="text-[2rem] leading-tight font-semibold">
          Cómo funciona
        </h2>
        <dl className="mt-6 grid gap-x-12 border-t border-filete md:grid-cols-2">
          {lineas.map(([t, d]) => (
            <div key={t} className="border-b border-filete py-4">
              <dt className="font-serif text-[1.125rem] font-semibold">{t}</dt>
              <dd className="mt-1 max-w-[60ch]">{d}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-6 max-w-[65ch]">
          La <a href={`${REPO}/blob/main/docs/metodologia.md`}>metodología completa</a> y la{" "}
          <a href={`${REPO}/blob/main/docs/model_card.md`}>ficha del modelo</a> (qué hace, cuánto le
          erra y para qué no sirve) están en el repositorio, con el código y cuatro notebooks:{" "}
          <a href={NOTEBOOK("01_eda")}>exploración</a>, <a href={NOTEBOOK("02_traslado")}>traslado</a>,{" "}
          <a href={NOTEBOOK("03_pronostico")}>pronóstico</a> y{" "}
          <a href={NOTEBOOK("04_revisiones")}>revisiones</a>. Versión de los datos:{" "}
          <span className="break-all text-tinta-2">{resumen.meta.versionDatos}</span>.
        </p>
      </div>
    </section>
  );
}

export function Pie({ resumen }: { resumen: Resumen }) {
  return (
    <footer className="border-t border-tinta">
      <div className="mx-auto grid max-w-[1200px] gap-x-12 gap-y-6 px-4 py-8 text-sm md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:px-8">
        <div>
          <p className="font-serif text-[1.125rem] font-semibold">Efecto Góndola</p>
          <p className="mt-1 text-tinta-2">
            Un proyecto de Gabriel Domingo, en{" "}
            <a href="https://www.linkedin.com/in/gabydomingo/">LinkedIn</a> y en{" "}
            <a href="https://github.com/gabydomingo">GitHub</a>.
          </p>
          <p className="mt-1 text-tinta-2">
            Código abierto: <a href={REPO}>monitor-de-traslado</a>
          </p>
        </div>
        <ul className="grid gap-2 text-tinta-2 sm:grid-cols-3">
          {resumen.meta.fuentes.map((f) => (
            <li key={f.nombre}>
              <a href={f.url} className="font-semibold text-tinta">
                {f.nombre}
              </a>
              <span className="block">{f.que}.</span>
              <span className="block">{f.licencia}.</span>
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
