"use client";

import { useCallback } from "react";
import type { Resumen, Series } from "@/lib/tipos";
import { COLOR_REGION, type RegionId } from "@/lib/colores";
import { NG, sumarMeses, type Indice } from "@/lib/consultas";
import { mesLargo, nombreMes, pct } from "@/lib/formato";
import { abanico, barrasMes, trasladoRubros, type Barra, type FilaTraslado } from "@/lib/graficos";
import { Grafico } from "./Grafico";
import { NotaEnergia } from "./NotaEnergia";

// lo que se ve al elegir una region: que subio, que se espera y cuanto del mayorista llega
export function PanelRegion({
  resumen,
  series,
  idx,
  region,
}: {
  resumen: Resumen;
  series: Series;
  idx: Indice;
  region: RegionId;
}) {
  const { meta } = resumen;
  const info = resumen.regiones.find((r) => r.id === region)!;
  const rubros = resumen.rubros.filter((r) => !r.esGeneral);
  const general = idx.ultimo(region, NG)!.valor;
  const pron = idx.pronostico(region, NG)!;

  const barras: Barra[] = rubros.flatMap((r) => {
    const d = idx.ultimo(region, r.id);
    return d ? [{ nombre: r.nombre, valor: d.valor, contraste: r.esContraste }] : [];
  });
  const mayor = [...barras].filter((b) => !b.contraste).sort((a, b) => b.valor - a.valor)[0];

  const filas: FilaTraslado[] = rubros.flatMap((r) => {
    const t = idx.traslado(region, r.id);
    return t
      ? [
          {
            nombre: r.nombre,
            valor: t.largoPlazo,
            inf: t.intervalo[0],
            sup: t.intervalo[1],
            significativo: t.significativo,
            contraste: r.esContraste,
          },
        ]
      : [];
  });
  const significativos = filas.filter((f) => f.significativo && !f.contraste).length;

  // ultimos 13 meses del nivel general y el pronostico
  const ng = idx.serie(NG)!;
  const desde = series.meses.indexOf(sumarMeses(meta.ultimoMes, -12));
  const ultimos = series.meses.slice(desde).map((mes, i) => ({
    mes,
    valor: ng.gondola[region]?.[desde + i] ?? null,
  }));

  const color = COLOR_REGION[region];
  const dibujarBarras = useCallback(
    (w: number) => barrasMes(barras, general, color, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [region],
  );
  const dibujarAbanico = useCallback(
    (w: number) =>
      abanico(ultimos, { mes: meta.mesPronosticado, valor: pron.valor, banda80: pron.banda80, banda90: pron.banda90 }, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [region],
  );
  const dibujarTraslado = useCallback(
    (w: number) => trasladoRubros(filas, w),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [region],
  );

  return (
    <div className="py-6 md:py-8">
      <h2 id="titulo-region" className="flex items-center gap-3 text-[2rem] leading-tight font-semibold">
        <span aria-hidden className="size-4 rounded-sm" style={{ background: color }} />
        {region}
      </h2>
      <p className="mt-1 max-w-[60ch] text-tinta-2">{info.queAbarca}.</p>

      <Bloque titulo={`Que subio en ${nombreMes(meta.ultimoMes)}`}>
        <p className="max-w-[60ch]">
          Los precios subieron {pct(general)} en promedio. El rubro que mas subio fue{" "}
          {mayor.nombre.toLowerCase()}, con {pct(mayor.valor)}.
        </p>
        <Grafico
          dibujar={dibujarBarras}
          alto={barras.length * 22 + 36}
          descripcion={`Inflacion de ${mesLargo(meta.ultimoMes)} en ${region} por rubro, de mayor a menor`}
          className="mt-3"
        />
        <NotaEnergia />
      </Bloque>

      <Bloque titulo={`Que se espera para ${nombreMes(meta.mesPronosticado)}`}>
        <p className="max-w-[60ch]">
          El modelo dice {pct(pron.valor)}. Con lo que le erro antes, 8 de cada 10 veces el dato cae
          en la franja oscura (de {pct(pron.banda80[0])} a {pct(pron.banda80[1])}) y 9 de cada 10 en
          la clara (de {pct(pron.banda90[0])} a {pct(pron.banda90[1])}).
          {pron.ultimo !== null && (
            <> Si se repitiera el dato de {nombreMes(meta.ultimoMes)}, seria {pct(pron.ultimo)}.</>
          )}
        </p>
        <Grafico
          dibujar={dibujarAbanico}
          alto={220}
          descripcion={`Inflacion mensual de ${region} en los ultimos 12 meses y pronostico para ${mesLargo(meta.mesPronosticado)}: ${pct(pron.valor)}`}
          className="mt-3"
        />
        <p className="mt-2 max-w-[65ch] text-[0.8125rem] text-tinta-2">
          Es un pronostico estadistico, no un dato oficial. <a href="#pronostico">Como se hace y cuanto le erra</a>.
        </p>
      </Bloque>

      <Bloque titulo="Cuanto del mayorista llega a la gondola">
        <p className="max-w-[60ch]">
          Cuando el precio mayorista de un rubro sube mas que la inflacion general, la gondola no
          siempre sigue. El punto es la parte de esa suba que termina en el precio que pagas, con
          su rango. En {region} se puede afirmar para {significativos} de {filas.length - 1} rubros;
          el resto, en gris, no se distingue de cero.
        </p>
        <Grafico
          dibujar={dibujarTraslado}
          alto={filas.length * 22 + 50}
          descripcion={`Traslado del mayorista a la gondola por rubro en ${region}, con su rango`}
          className="mt-3"
        />
        <p className="mt-2 max-w-[65ch] text-[0.8125rem] text-tinta-2">
          100% quiere decir que llega toda la suba. Rango: 95% de confianza.{" "}
          <a href="#rubro">Ver cada rubro en detalle</a>.
        </p>
        <NotaEnergia />
      </Bloque>
    </div>
  );
}

function Bloque({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="mt-8 border-t border-filete pt-5">
      <h3 className="mb-2 text-[1.25rem] leading-snug font-semibold">{titulo}</h3>
      {children}
    </section>
  );
}
