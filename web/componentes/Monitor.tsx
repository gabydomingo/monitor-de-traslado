"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Resumen } from "@/lib/tipos";
import { useArchivo } from "@/lib/cliente";
import type { Mapa } from "@/lib/medidas";
import type { RegionId } from "@/lib/colores";
import { indexar } from "@/lib/consultas";
import { Franja } from "./Franja";
import { MapaRegiones } from "./MapaRegiones";
import { PanelRegion } from "./PanelRegion";
import { VistaRubro } from "./VistaRubro";
import { SeccionPronostico } from "./SeccionPronostico";

// la region elegida gobierna todo: franja, panel, rubro y pronostico cambian juntos
export function Monitor({ resumen, mapa }: { resumen: Resumen; mapa: Mapa }) {
  const [region, setRegion] = useState<RegionId>("GBA");
  const [rubro, setRubro] = useState("carnes");
  const idx = useMemo(() => indexar(resumen), [resumen]);
  // las series se piden apenas carga la pagina: el panel y el rubro las usan enseguida
  const series = useArchivo("series");

  // el mes del panel. arranca en el ultimo dato; con ?mes=2023-12 en el link abre en ese mes
  const ultimo = resumen.meta.ultimoMes;
  const [mes, setMesEstado] = useState(ultimo);
  useEffect(() => {
    const pedido = new URLSearchParams(window.location.search).get("mes");
    if (
      pedido &&
      /^\d{4}-\d{2}$/.test(pedido) &&
      pedido >= "2017-01" &&
      pedido < ultimo
    ) {
      setMesEstado(pedido);
    }
  }, [ultimo]);
  const setMes = useCallback(
    (m: string) => {
      setMesEstado(m);
      const url = new URL(window.location.href);
      if (m === ultimo) url.searchParams.delete("mes");
      else url.searchParams.set("mes", m);
      window.history.replaceState(null, "", url);
    },
    [ultimo],
  );

  return (
    <>
      <Franja
        resumen={resumen}
        idx={idx}
        region={region}
        onRegion={setRegion}
      />

      <section
        aria-labelledby="titulo-region"
        className="mx-auto grid max-w-[1200px] gap-x-12 px-4 md:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] md:px-8"
      >
        <div className="border-b border-filete py-6 md:sticky md:top-0 md:self-start md:border-b-0 md:py-8">
          <MapaRegiones
            mapa={mapa}
            resumen={resumen}
            idx={idx}
            region={region}
            onRegion={setRegion}
            series={series}
            mes={mes}
          />
        </div>
        <PanelRegion
          resumen={resumen}
          series={series}
          idx={idx}
          region={region}
          mes={mes}
          onMes={setMes}
        />
      </section>

      <VistaRubro
        resumen={resumen}
        series={series}
        idx={idx}
        region={region}
        rubro={rubro}
        onRubro={setRubro}
      />

      <SeccionPronostico resumen={resumen} idx={idx} region={region} />
    </>
  );
}
