import "server-only";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Backtest, Resumen, Series } from "./tipos";

// se leen en el build: la pagina es estatica y los json los copia scripts/datos.mjs
function leer<T>(nombre: string): T {
  return JSON.parse(readFileSync(join(process.cwd(), "datos", `${nombre}.json`), "utf8")) as T;
}

export function cargar() {
  return {
    resumen: leer<Resumen>("resumen"),
    series: leer<Series>("series"),
    backtest: leer<Backtest>("backtest"),
  };
}
