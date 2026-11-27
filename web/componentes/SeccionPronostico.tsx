"use client";

import { useCallback, useState } from "react";
import type { Registrado, Resumen } from "@/lib/tipos";
import { useArchivo, useCerca, type Bajando } from "@/lib/cliente";
import type { RegionId } from "@/lib/colores";
import { NG, aciertoDe, type Indice } from "@/lib/consultas";
import { fechaLarga, mesLargo, nombreMes, num, pct } from "@/lib/formato";
import { aciertos, type PuntoAcierto } from "@/lib/graficos";
import { Grafico } from "./Grafico";
import { NotaEnergia } from "./NotaEnergia";
import { Chevron } from "./Chevron";

// como se hace el pronostico, cuanto le erro hacia atras y el registro en vivo
export function SeccionPronostico({
  resumen,
  idx,
  region,
}: {
  resumen: Resumen;
  idx: Indice;
  region: RegionId;
}) {
  // el backtest y el registro se bajan cuando la seccion se acerca a la pantalla
  const [ref, cerca] = useCerca<HTMLElement>();
  const backtest = useArchivo("backtest", cerca);
  const historial = useArchivo("historial", cerca);
  const [serie, setSerie] = useState(NG);
  // por defecto los ultimos 24 meses: con diciembre de 2023 adentro no se ve el resto
  const [todo, setTodo] = useState(false);
  const { meta } = resumen;
  const rubro = idx.rubro(serie);
  const a = aciertoDe(backtest, region, serie);
  const meses = backtest?.meses ?? [];

  const desde = todo ? 0 : Math.max(0, meses.length - 24);
  const puntos: PuntoAcierto[] = a
    ? meses.slice(desde).flatMap((mes, j) => {
        const i = desde + j;
        const v = [
          a.real[i],
          a.pronostico[i],
          a.inf80[i],
          a.sup80[i],
          a.inf90[i],
          a.sup90[i],
        ];
        if (v.some((x) => x === null)) return [];
        const [real, pron, inf80, sup80, inf90, sup90] = v as number[];
        return [{ mes, real, pron, inf80, sup80, inf90, sup90 }];
      })
    : [];
  const adentro = puntos.filter(
    (p) => p.real >= p.inf80 && p.real <= p.sup80,
  ).length;
  const adentro90 = puntos.filter(
    (p) => p.real >= p.inf90 && p.real <= p.sup90,
  ).length;

  const dibujar = useCallback(
    (w: number) => aciertos(puntos, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [region, serie, todo, a],
  );

  const general = resumen.metricas.find((m) => m.grupo === "nivel_general")!;
  const rubros = resumen.metricas.find((m) => m.grupo === "rubros")!;
  const anios = [...new Set(resumen.errorAnual.map((e) => e.anio))].sort();
  const error = (grupo: string, anio: number) =>
    resumen.errorAnual.find((e) => e.grupo === grupo && e.anio === anio)!;
  // se calcula: cuando entren meses nuevos el texto sigue diciendo lo que dicen los datos
  const pierde = anios.filter((y) => {
    const e = error("nivel_general", y);
    return e.naive < e.combinado;
  });
  const rubrosSiempre = anios.every((y) => {
    const e = error("rubros", y);
    return e.combinado < e.naive;
  });
  const totalSeries = resumen.metricas.reduce((s, m) => s + m.series, 0);

  return (
    <section
      ref={ref}
      id="pronostico"
      aria-labelledby="titulo-pronostico"
      className="scroll-mt-4 border-t border-tinta"
    >
      <div className="mx-auto max-w-[1200px] px-4 py-10 md:px-8 md:py-14">
        <h2
          id="titulo-pronostico"
          className="text-[2rem] leading-tight font-semibold"
        >
          El pronóstico: cómo se hace y cuánto le erra
        </h2>

        <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-x-12 gap-y-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
          <div className="max-w-[65ch] space-y-4 font-serif text-[1.0625rem] leading-relaxed">
            <p>
              Cada mes, cuando el INDEC publica los precios mayoristas, un
              modelo de aprendizaje automático (machine learning) estima la
              inflación del mes en curso para cada rubro y cada región. Mira lo
              que pasó el mes anterior en el mayorista y en la góndola, el dólar
              de los primeros días del mes y lo que esperan los analistas que
              encuesta el Banco Central.
            </p>
            <p>
              Son dos modelos promediados: uno de árboles de decisión, que
              aprende de las {totalSeries} series juntas, y una regresión por
              serie, que puede seguir un salto del dólar que nunca vio.
            </p>
            <p>
              <strong>Puede errar.</strong> No es un dato oficial: por eso cada
              número va con dos franjas. La oscura es donde cayó el dato 8 de
              cada 10 veces cuando se probó hacia atrás; la clara, 9 de cada 10.
              Si el dólar salta a principio de mes, las franjas se agrandan
              solas.
            </p>
            <p>
              Donde más falla es con devaluaciones bruscas (en diciembre de 2023
              la franja de 8 de 10 acertó la mitad de las veces) y con frutas y
              verduras, que dependen del clima y de la cosecha.
            </p>
          </div>

          <figure>
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <figcaption className="font-serif text-[1.25rem] font-semibold">
                Lo que dijo y lo que pasó en {region}
              </figcaption>
              <div
                role="group"
                aria-label="Período"
                className="flex border border-filete text-sm"
              >
                {[false, true].map((k) => (
                  <button
                    key={String(k)}
                    type="button"
                    aria-pressed={todo === k}
                    onClick={() => setTodo(k)}
                    className={`cursor-pointer px-3 py-1 transition-colors duration-150 ease-out first:border-r first:border-filete ${
                      todo === k ? "bg-tinta text-papel" : "hover:bg-papel-2"
                    }`}
                  >
                    {k ? `${meses.length || 36} meses` : "24 meses"}
                  </button>
                ))}
              </div>
              <label className="flex w-full items-center gap-2 text-sm text-tinta-2">
                Serie
                <span className="relative w-full">
                  <select
                    value={serie}
                    onChange={(e) => setSerie(e.target.value)}
                    className="w-full min-w-0 cursor-pointer appearance-none pr-6 border-b border-tinta bg-transparent py-0.5 text-tinta transition-colors duration-150 ease-out hover:bg-papel-2"
                  >
                    {resumen.rubros.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.nombre}
                        {r.esContraste ? " (tarifa regulada)" : ""}
                      </option>
                    ))}
                  </select>
                  <Chevron className="text-tinta" />
                </span>
              </label>
            </div>
            <Grafico
              dibujar={dibujar}
              listo={puntos.length > 0}
              fallo={backtest === null}
              alto={300}
              descripcion={`Pronóstico y dato real de ${rubro.nombre} en ${region}, mes a mes. El dato cayó en la franja de 8 de cada 10 ${adentro} de ${puntos.length} veces`}
              className="mt-3"
            />
            <p className="mt-2 max-w-[65ch] text-[0.8125rem] text-tinta-2">
              Línea punteada: lo que dijo el modelo con los datos que había ese
              mes. Puntos: el dato del INDEC, lleno si cayó en la franja oscura
              y vacío si no. En estos {puntos.length} meses el dato cayó{" "}
              {adentro} veces en la oscura y {adentro90} en la clara.
            </p>
            {rubro.esContraste && <NotaEnergia />}
          </figure>
        </div>

        <div className="mt-12 grid grid-cols-[minmax(0,1fr)] gap-x-12 gap-y-10 lg:grid-cols-2">
          <div>
            <h3 className="text-[1.25rem] font-semibold">
              Cuánto le erró, en promedio
            </h3>
            <p className="mt-2 max-w-[60ch]">
              Error medio en puntos de inflación mensual, todas las regiones. La
              vara es lo más simple: suponer que el mes que viene va a ser igual
              a este.
            </p>
            <table className="mt-4 w-full text-sm">
              <caption className="sr-only">
                Error medio por período del modelo y de repetir el último dato
              </caption>
              <thead>
                <tr className="border-b border-tinta text-left">
                  <th
                    scope="col"
                    className="py-2 pr-2 font-normal text-tinta-2"
                  >
                    Período
                  </th>
                  <th
                    scope="col"
                    className="py-2 pr-2 text-right font-normal text-tinta-2"
                    colSpan={2}
                  >
                    Nivel general
                  </th>
                  <th
                    scope="col"
                    className="py-2 text-right font-normal text-tinta-2"
                    colSpan={2}
                  >
                    Rubros
                  </th>
                </tr>
                <tr className="border-b border-filete text-right text-[0.8125rem] text-tinta-2">
                  <td />
                  <th scope="col" className="py-1 pr-2 font-normal">
                    Repetir
                  </th>
                  <th scope="col" className="py-1 pr-2 font-normal">
                    Modelo
                  </th>
                  <th scope="col" className="py-1 pr-2 font-normal">
                    Repetir
                  </th>
                  <th scope="col" className="py-1 font-normal">
                    Modelo
                  </th>
                </tr>
              </thead>
              <tbody>
                {anios.map((anio) => {
                  const g = error("nivel_general", anio);
                  const r = error("rubros", anio);
                  return (
                    <tr
                      key={anio}
                      className="border-b border-filete text-right"
                    >
                      <th
                        scope="row"
                        className="py-2 pr-2 text-left font-normal"
                      >
                        {anio}
                        {g.meses < 12 && (
                          <span className="text-tinta-2">
                            {" "}
                            ({g.meses} meses)
                          </span>
                        )}
                      </th>
                      <Celda valor={g.naive} gana={g.naive < g.combinado} />
                      <Celda valor={g.combinado} gana={g.combinado < g.naive} />
                      <Celda valor={r.naive} gana={r.naive < r.combinado} />
                      <Celda valor={r.combinado} gana={r.combinado < r.naive} />
                    </tr>
                  );
                })}
                <tr className="border-b border-tinta text-right font-semibold">
                  <th scope="row" className="py-2 pr-2 text-left">
                    Total
                  </th>
                  <Celda
                    valor={general.naive}
                    gana={general.naive < general.combinado}
                  />
                  <Celda
                    valor={general.combinado}
                    gana={general.combinado < general.naive}
                  />
                  <Celda
                    valor={rubros.naive}
                    gana={rubros.naive < rubros.combinado}
                  />
                  <Celda
                    valor={rubros.combinado}
                    gana={rubros.combinado < rubros.naive}
                  />
                </tr>
              </tbody>
            </table>
            <div className="mt-4 max-w-[60ch] space-y-2 text-[0.9375rem]">
              <p>
                En los rubros el modelo erra{" "}
                {num(100 - (rubros.combinado / rubros.naive) * 100)}% menos que
                repetir el dato
                {rubrosSiempre ? ", en todos los períodos" : ""}
                {rubros.pValor < 0.05 ? ", y la diferencia es clara" : ""}.{" "}
                {pierde.length > 0 ? (
                  <>
                    En el nivel general{" "}
                    {general.combinado < general.naive
                      ? "gana en el total"
                      : "no gana"}
                    {general.pValor >= 0.05
                      ? " pero sin una diferencia clara"
                      : ""}
                    , y en {pierde.join(" y ")} repetir el dato anterior anduvo
                    mejor: con la inflación quieta, casi no se mueve de un mes a
                    otro y es muy difícil de mejorar. Por eso el panel de cada
                    región muestra también lo que daría repetir el dato.
                  </>
                ) : (
                  <>En el nivel general también gana en todos los períodos.</>
                )}
              </p>
              <p className="text-tinta-2">
                Las franjas cumplen lo que prometen: en los rubros el dato cayó
                en la oscura el {pct(rubros.cobertura80 * 100, 0)} de las veces
                y en la clara el {pct(rubros.cobertura90 * 100, 0)}; en el nivel
                general, {pct(general.cobertura80 * 100, 0)} y{" "}
                {pct(general.cobertura90 * 100, 0)}.
              </p>
            </div>
          </div>

          <Registro
            resumen={resumen}
            registro={historial === null ? null : historial?.registro}
            idx={idx}
            region={region}
          />
        </div>
      </div>
    </section>
  );
}

function Celda({ valor, gana }: { valor: number; gana: boolean }) {
  return (
    <td
      className={`py-2 pr-2 last:pr-0 ${gana ? "font-semibold" : "text-tinta-2"}`}
    >
      {num(valor, 2)}
    </td>
  );
}

// los pronosticos guardados antes de conocer el dato, con el dato cuando sale
function Registro({
  resumen,
  registro,
  idx,
  region,
}: {
  resumen: Resumen;
  registro: Bajando<Registrado[]>;
  idx: Indice;
  region: RegionId;
}) {
  const { meta } = resumen;
  const filas = (registro ?? []).filter((r) => r.region === region);
  const meses = [...new Set(filas.map((f) => f.mes))].sort().reverse();
  const prox = meta.proximoIpc;

  return (
    <div>
      <h3 className="text-[1.25rem] font-semibold">
        En vivo: lo que dijo antes de saberlo
      </h3>
      <p className="mt-2 max-w-[60ch]">
        Cada pronóstico se guarda el día que se hace, antes de que salga el
        dato, y no se toca más. Cuando el INDEC publica, se compara acá. El
        registro empezó en{" "}
        {resumen.automatizacion.primerRegistro
          ? mesLargo(resumen.automatizacion.primerRegistro)
          : "este mes"}{" "}
        y suma un mes cada vez.
      </p>
      {registro === null && (
        <p className="mt-4 max-w-[60ch] text-tinta-2">
          No se pudo bajar el registro. Revisá la conexión y recargá la página.
        </p>
      )}
      {meses.map((mes) => {
        const delMes = filas.filter((f) => f.mes === mes);
        const ng = delMes.find((f) => f.rubro === NG);
        const resto = delMes.filter((f) => f.rubro !== NG);
        const pendiente = delMes.every((f) => f.real === null);
        return (
          <div key={mes} className="mt-5">
            <p className="flex flex-wrap justify-between gap-2 border-b border-tinta pb-1 text-sm">
              <span className="font-semibold">{mesLargo(mes)}</span>
              <span className="text-tinta-2">
                {pendiente
                  ? mes === prox.mes
                    ? `El dato sale entre el ${prox.diaDesde} y el ${prox.diaHasta} de ${nombreMes(prox.publicacion)}`
                    : "Esperando el dato"
                  : `Guardado el ${fechaLarga(delMes[0].generado)}`}
              </span>
            </p>
            <TablaRegistro filas={ng ? [ng] : []} idx={idx} />
            {resto.length > 0 && (
              <details className="group mt-1">
                <summary className="cursor-pointer py-1 text-sm text-tinta-2 hover:text-tinta">
                  Ver los {resto.length} rubros
                </summary>
                <TablaRegistro filas={resto} idx={idx} />
              </details>
            )}
          </div>
        );
      })}
    </div>
  );
}

function TablaRegistro({ filas, idx }: { filas: Registrado[]; idx: Indice }) {
  if (!filas.length) return null;
  return (
    <table className="w-full text-sm">
      <thead className="sr-only">
        <tr>
          <th scope="col">Serie</th>
          <th scope="col">Pronóstico</th>
          <th scope="col">Franja de 8 de cada 10</th>
          <th scope="col">Dato real</th>
        </tr>
      </thead>
      <tbody>
        {filas.map((f) => {
          const adentro =
            f.real !== null && f.real >= f.banda80[0] && f.real <= f.banda80[1];
          const r = idx.rubro(f.rubro);
          return (
            <tr key={f.rubro} className="border-b border-filete">
              <th scope="row" className="py-1.5 pr-2 text-left font-normal">
                {r?.nombre ?? f.rubro}
                {r?.esContraste && (
                  <span className="text-tinta-2"> (tarifa regulada)</span>
                )}
              </th>
              <td className="py-1.5 pr-2 text-right">{pct(f.pronostico)}</td>
              <td className="py-1.5 pr-2 text-right text-tinta-2">
                {pct(f.banda80[0])} a {pct(f.banda80[1])}
              </td>
              <td className="py-1.5 text-right">
                {f.real === null ? (
                  <span className="text-tinta-2">falta</span>
                ) : (
                  <span className={adentro ? "font-semibold" : ""}>
                    {pct(f.real)} {adentro ? "adentro" : "afuera"}
                  </span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
