"use client";

import { useCallback, useState } from "react";
import type { Resumen, Series } from "@/lib/tipos";
import { COLOR_REGION, type RegionId } from "@/lib/colores";
import type { Indice } from "@/lib/consultas";
import { parte } from "@/lib/formato";
import {
  cadena,
  mayoristaVsGondola,
  porMes,
  regimenes,
  type FilaRegimen,
  type PuntoCadena,
  type PuntoSerie,
} from "@/lib/graficos";
import { Grafico } from "./Grafico";
import { NotaEnergia } from "./NotaEnergia";
import { Chevron } from "./Chevron";

const DESDE = { reciente: "2024-01", todo: "2017-01" } as const;
const REGIMEN = {
  baja: "Baja (2017, 2025-26)",
  media: "Media (2018-21)",
  alta: "Alta (2022-24)",
} as const;

// un rubro a la vez: mayorista contra gondola, cuanto llega, en cuanto tiempo y si cambia
export function VistaRubro({
  resumen,
  series,
  idx,
  region,
  rubro,
  onRubro,
}: {
  resumen: Resumen;
  series: Series;
  idx: Indice;
  region: RegionId;
  rubro: string;
  onRubro: (r: string) => void;
}) {
  const [desde, setDesde] = useState<keyof typeof DESDE>("reciente");
  const info = idx.rubro(rubro);
  const s = idx.serie(rubro)!;
  const etapas = idx.trasladoEtapas(region, rubro);
  const t = idx.traslado(region, rubro);
  const reg = idx.regimen(rubro);
  const cad = idx.cadena(rubro);
  const opciones = resumen.rubros.filter((r) => !r.esGeneral);
  // cuantos rubros trasladan mas con inflacion alta que con baja
  const porRubro = Map.groupBy(resumen.trasladoRegimen, (x) => x.rubro);
  let masConAlta = 0;
  let conAmbas = 0;
  for (const filas of porRubro.values()) {
    const alta = filas.find((f) => f.regimen === "alta");
    const baja = filas.find((f) => f.regimen === "baja");
    if (!alta || !baja) continue;
    conAmbas += 1;
    if (alta.largoPlazo > baja.largoPlazo) masConAlta += 1;
  }

  const inicio = series.meses.indexOf(DESDE[desde]);
  const puntos: PuntoSerie[] = series.meses.slice(inicio).flatMap((mes, i) => {
    const m = s.mayorista[inicio + i];
    const g = s.gondola[region]?.[inicio + i];
    const out: PuntoSerie[] = [];
    if (m !== null && m !== undefined)
      out.push({ mes, valor: m, serie: "Mayorista" });
    if (g !== null && g !== undefined)
      out.push({ mes, valor: g, serie: "Gondola" });
    return out;
  });

  const clave = `${region}|${rubro}|${desde}`;
  const dibujarSerie = useCallback(
    (w: number) =>
      mayoristaVsGondola(puntos, COLOR_REGION[region], info.esContraste, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [clave],
  );
  const dibujarMeses = useCallback(
    (w: number) => porMes(t!.porMes, t!.significativo, info.esContraste, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [clave],
  );
  const filasRegimen: FilaRegimen[] = reg.map((r) => ({
    regimen: REGIMEN[r.regimen],
    valor: r.largoPlazo,
    inf: r.intervalo[0],
    sup: r.intervalo[1],
    significativo: r.significativo,
  }));
  const dibujarRegimen = useCallback(
    (w: number) => regimenes(filasRegimen, info.esContraste, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [rubro],
  );
  const puntosCadena: PuntoCadena[] = cad.flatMap((c) =>
    c.respuesta.map((v, mes) => ({
      origen: c.origen,
      mes,
      valor: v,
      inf: c.inferior[mes],
      sup: c.superior[mes],
    })),
  );
  const dibujarCadena = useCallback(
    (w: number) => cadena(puntosCadena, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [rubro],
  );

  return (
    <section
      id="rubro"
      aria-labelledby="titulo-rubro"
      className="scroll-mt-4 border-t border-tinta"
    >
      <div className="mx-auto max-w-[1200px] px-4 py-10 md:px-8 md:py-14">
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
          <div>
            <h2
              id="titulo-rubro"
              className="text-[2rem] leading-tight font-semibold"
            >
              Rubro por rubro
            </h2>
            <p className="mt-1 max-w-[60ch] text-tinta-2">
              Del mayorista a la gondola en {region}. El mayorista es uno solo
              para todo el pais.
            </p>
          </div>
          <label className="flex w-full flex-col gap-1 text-sm text-tinta-2 sm:w-auto">
            Rubro
            <span className="relative">
              <select
                value={rubro}
                onChange={(e) => onRubro(e.target.value)}
                className="w-full min-w-0 cursor-pointer appearance-none pr-6 border-b sm:min-w-[16rem] border-tinta bg-transparent py-1 font-serif text-[1.25rem] text-tinta transition-colors duration-150 ease-out hover:bg-papel-2"
              >
                {opciones.map((r) => (
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
        {info.esContraste && <NotaEnergia className="mt-4" />}

        <div className="mt-8 grid grid-cols-[minmax(0,1fr)] gap-x-12 gap-y-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
          <figure>
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <figcaption className="font-serif text-[1.25rem] font-semibold">
                Cuanto subio cada mes
              </figcaption>
              <div
                role="group"
                aria-label="Periodo"
                className="flex border border-filete text-sm"
              >
                {(Object.keys(DESDE) as (keyof typeof DESDE)[]).map((k) => (
                  <button
                    key={k}
                    type="button"
                    aria-pressed={desde === k}
                    onClick={() => setDesde(k)}
                    className={`cursor-pointer px-3 py-1 transition-colors duration-150 ease-out first:border-r first:border-filete ${
                      desde === k ? "bg-tinta text-papel" : "hover:bg-papel-2"
                    }`}
                  >
                    {k === "reciente" ? "Desde 2024" : "Desde 2017"}
                  </button>
                ))}
              </div>
            </div>
            <Grafico
              dibujar={dibujarSerie}
              alto={280}
              descripcion={`Variacion mensual del precio mayorista y de gondola de ${info.nombre} en ${region}`}
              className="mt-3"
            />
            <p className="mt-2 max-w-[65ch] text-[0.8125rem] text-tinta-2">
              Variacion mensual. Mayorista: indice de precios internos al por
              mayor (IPIM) o, para frutas y verduras, precios del productor.
              Gondola: IPC de {region}.
            </p>
          </figure>

          <div>
            <h3 className="text-[1.25rem] font-semibold">
              Cuanto llega y cuando
            </h3>
            {t ? (
              <>
                <p className="mt-2 max-w-[60ch]">
                  {t.significativo ? (
                    <>
                      De cada suba del mayorista por encima de la inflacion
                      general, a la gondola llega{" "}
                      <strong>{parte(t.largoPlazo)}</strong> (entre{" "}
                      {parte(t.intervalo[0])} y {parte(t.intervalo[1])}).
                    </>
                  ) : (
                    <>
                      La estimacion da {parte(t.largoPlazo)}, pero el rango va
                      de {parte(t.intervalo[0])} a {parte(t.intervalo[1])}: no
                      se puede distinguir de cero. Con estos datos no se puede
                      afirmar que haya traslado.
                    </>
                  )}
                </p>
                <Grafico
                  dibujar={dibujarMeses}
                  alto={170}
                  descripcion={`Parte de la suba que llega en el mismo mes y en los tres siguientes: ${t.porMes.map(parte).join(", ")}`}
                  className="mt-3"
                />
                <p className="mt-1 max-w-[65ch] text-[0.8125rem] text-tinta-2">
                  Lo que llega el mismo mes de la suba y en cada uno de los tres
                  siguientes. La suma da el total.
                  {etapas.length > 1 && " Medido desde la industria."}
                </p>
              </>
            ) : (
              <p className="mt-2 text-tinta-2">
                No hay estimacion para este rubro en {region}.
              </p>
            )}
          </div>

          {filasRegimen.length > 0 && (
            <div>
              <h3 className="text-[1.25rem] font-semibold">Segun la epoca</h3>
              <p className="mt-2 max-w-[60ch]">
                Solo para GBA, que tiene la serie mas larga: el mismo calculo
                separado por epocas de inflacion. En {masConAlta} de los{" "}
                {conAmbas} rubros llega mas con inflacion alta que con baja,
                pero cada epoca tiene pocos datos y los rangos son anchos.
              </p>
              <Grafico
                dibujar={dibujarRegimen}
                alto={filasRegimen.length * 34 + 44}
                descripcion={`Traslado de ${info.nombre} en GBA segun la epoca de inflacion`}
                className="mt-3"
              />
            </div>
          )}

          {puntosCadena.length > 0 && (
            <div>
              <h3 className="text-[1.25rem] font-semibold">
                Del campo a la gondola
              </h3>
              <p className="mt-2 max-w-[60ch]">
                Para {info.nombre.toLowerCase()} hay precio del productor y de
                la industria. Esto es cuanto sube la gondola de GBA, acumulado
                mes a mes, despues de una suba en cada eslabon. La linea gris
                parte del productor; la negra, de la industria. Tambien solo
                para GBA.
              </p>
              <Grafico
                dibujar={dibujarCadena}
                alto={220}
                descripcion={`Respuesta acumulada de la gondola de ${info.nombre} a una suba del productor y de la industria`}
                className="mt-3"
              />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
