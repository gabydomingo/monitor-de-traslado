import type { Backtest, Resumen, Series } from "./tipos";

export const NG = "nivel_general";

// indices para buscar rapido por region y rubro desde los componentes
export function indexar(resumen: Resumen) {
  const clave = (region: string, rubro: string) => `${region}|${rubro}`;
  const porClave = <T extends { region: string; rubro: string }>(xs: T[]) =>
    new Map(xs.map((x) => [clave(x.region, x.rubro), x]));

  const rubros = new Map(resumen.rubros.map((r) => [r.id, r]));
  const ultimo = porClave(resumen.ultimoDato);
  const pronostico = porClave(resumen.pronosticos);
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
    pronostico: (region: string, rubro: string) =>
      pronostico.get(clave(region, rubro)),
    traslado: (region: string, rubro: string) =>
      traslado.get(clave(region, rubro)),
    trasladoEtapas: (region: string, rubro: string) =>
      resumen.traslado.filter((t) => t.region === region && t.rubro === rubro),
    regimen: (rubro: string) =>
      resumen.trasladoRegimen.filter((t) => t.rubro === rubro),
    cadena: (rubro: string) => resumen.cadena.filter((c) => c.rubro === rubro),
  };
}

export type Indice = ReturnType<typeof indexar>;

// series y backtest llegan despues (lib/cliente.ts): pueden no estar todavia
export function serieDe(series: Series | undefined, rubro: string) {
  return series?.rubros.find((s) => s.rubro === rubro);
}

export function aciertoDe(
  backtest: Backtest | undefined,
  region: string,
  rubro: string,
) {
  return backtest?.series.find((s) => s.region === region && s.rubro === rubro);
}

/**
 * inflacion de cada rubro (y el nivel general) en una region y un mes. el ultimo mes sale del
 * resumen, que ya viene en el html; los anteriores de las series, que se bajan aparte
 */
export function valoresDelMes(
  resumen: Resumen,
  series: Series | undefined,
  region: string,
  mes: string,
): Map<string, number> | undefined {
  if (mes === resumen.meta.ultimoMes) {
    return new Map(
      resumen.ultimoDato
        .filter((d) => d.region === region)
        .map((d) => [d.rubro, d.valor]),
    );
  }
  const i = series?.meses.indexOf(mes) ?? -1;
  if (!series || i < 0) return undefined;
  const salida = new Map<string, number>();
  for (const s of series.rubros) {
    const v = s.gondola[region]?.[i];
    if (v !== null && v !== undefined) salida.set(s.rubro, v);
  }
  return salida;
}

/** "2026-10" + n meses */
export function sumarMeses(mes: string, n: number): string {
  const total = Number(mes.slice(0, 4)) * 12 + Number(mes.slice(5, 7)) - 1 + n;
  return `${Math.floor(total / 12)}-${String((total % 12) + 1).padStart(2, "0")}`;
}
