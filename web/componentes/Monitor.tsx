"use client";

import { useMemo, useState } from "react";
import type { Backtest, Resumen, Series } from "@/lib/tipos";
import type { Mapa } from "@/lib/medidas";
import type { RegionId } from "@/lib/colores";
import { indexar } from "@/lib/consultas";
import { Franja } from "./Franja";
import { MapaRegiones } from "./MapaRegiones";
import { PanelRegion } from "./PanelRegion";
import { VistaRubro } from "./VistaRubro";
import { SeccionPronostico } from "./SeccionPronostico";

// la region elegida gobierna todo: franja, panel, rubro y pronostico cambian juntos
export function Monitor({
  resumen,
  series,
  backtest,
  mapa,
}: {
  resumen: Resumen;
  series: Series;
  backtest: Backtest;
  mapa: Mapa;
}) {
  const [region, setRegion] = useState<RegionId>("GBA");
  const [rubro, setRubro] = useState("carnes");
  const idx = useMemo(() => indexar(resumen, series, backtest), [resumen, series, backtest]);

  return (
    <>
      <Franja resumen={resumen} idx={idx} region={region} onRegion={setRegion} />

      <section
        aria-labelledby="titulo-region"
        className="mx-auto grid max-w-[1200px] gap-x-12 px-4 md:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] md:px-8"
      >
        <div className="border-b border-filete py-6 md:sticky md:top-0 md:self-start md:border-b-0 md:py-8">
          <MapaRegiones mapa={mapa} resumen={resumen} idx={idx} region={region} onRegion={setRegion} />
        </div>
        <PanelRegion resumen={resumen} series={series} idx={idx} region={region} />
      </section>

      <VistaRubro
        resumen={resumen}
        series={series}
        idx={idx}
        region={region}
        rubro={rubro}
        onRubro={setRubro}
      />

      <SeccionPronostico resumen={resumen} backtest={backtest} idx={idx} region={region} />
    </>
  );
}
