import type { Backtest, Resumen, Series } from "./tipos";

export const NG = "nivel_general";

// indices para buscar rapido por region y rubro desde los componentes
export function indexar(resumen: Resumen, series: Series, backtest: Backtest) {
  const clave = (region: string, rubro: string) => `${region}|${rubro}`;
  const porClave = <T extends { region: string; rubro: string }>(xs: T[]) =>
    new Map(xs.map((x) => [clave(x.region, x.rubro), x]));

  const rubros = new Map(resumen.rubros.map((r) => [r.id, r]));
  const ultimo = porClave(resumen.ultimoDato);
  const pronostico = porClave(resumen.pronosticos);
  const acierto = porClave(backtest.series);
  const serie = new Map(series.rubros.map((s) => [s.rubro, s]));
  // el panel usa el traslado desde la industria; frutas y verduras solo tienen productor
  const traslado = new Map<string, Resumen["traslado"][number]>();
  for (const t of resumen.traslado) {
    const k = clave(t.region, t.rubro);
    if (!traslado.has(k) || t.etapa === "industria") traslado.set(k, t);
  }

  return {
    rubro: (id: string) => rubros.get(id)!,
    nombre: (id: string) => rubros.get(id)?.nombre ?? id,
    ultimo: (region: string, rubro: string) => ultimo.get(clave(region, rubro)),
    pronostico: (region: string, rubro: string) => pronostico.get(clave(region, rubro)),
    acierto: (region: string, rubro: string) => acierto.get(clave(region, rubro)),
    traslado: (region: string, rubro: string) => traslado.get(clave(region, rubro)),
    trasladoEtapas: (region: string, rubro: string) =>
      resumen.traslado.filter((t) => t.region === region && t.rubro === rubro),
    serie: (rubro: string) => serie.get(rubro),
    regimen: (rubro: string) => resumen.trasladoRegimen.filter((t) => t.rubro === rubro),
    cadena: (rubro: string) => resumen.cadena.filter((c) => c.rubro === rubro),
  };
}

export type Indice = ReturnType<typeof indexar>;

/** "2026-10" + n meses */
export function sumarMeses(mes: string, n: number): string {
  const total = Number(mes.slice(0, 4)) * 12 + Number(mes.slice(5, 7)) - 1 + n;
  return `${Math.floor(total / 12)}-${String((total % 12) + 1).padStart(2, "0")}`;
}
