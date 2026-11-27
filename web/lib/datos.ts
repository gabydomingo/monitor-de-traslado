import "server-only";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Resumen } from "./tipos";
import { conTildes } from "./tildes";

// se leen en el build: la pagina es estatica y los json los copia scripts/datos.mjs
function leer<T>(nombre: string): T {
  return JSON.parse(
    readFileSync(join(process.cwd(), "datos", `${nombre}.json`), "utf8"),
  ) as T;
}

// los textos de los datos vienen sin tildes; se las devuelvo una sola vez aca
function mostrar(r: Resumen): Resumen {
  return {
    ...r,
    rubros: r.rubros.map((x) => ({ ...x, nombre: conTildes(x.nombre) })),
    regiones: r.regiones.map((x) => ({
      ...x,
      queAbarca: conTildes(x.queAbarca),
      provincias: x.provincias.map(conTildes),
    })),
    meta: {
      ...r.meta,
      fuentes: r.meta.fuentes.map((f) => ({
        ...f,
        que: conTildes(f.que),
        licencia: conTildes(f.licencia),
      })),
    },
  };
}

// solo el resumen: series, backtest e historial los baja el navegador (lib/cliente.ts)
export function cargar() {
  return { resumen: mostrar(leer<Resumen>("resumen")) };
}
