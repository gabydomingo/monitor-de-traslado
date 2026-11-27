// copia los json que genera monitor.web (data/web, en la raiz del repo) adentro de web/.
// datos/ lo lee el build: el resumen va en el html. public/datos/ lo baja el navegador despues
// de cargar la pagina (series, backtest e historial), asi el html pesa menos
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { join } from "node:path";

const origen = join(import.meta.dirname, "..", "..", "data", "web");
const build = join(import.meta.dirname, "..", "datos");
const publico = join(import.meta.dirname, "..", "public", "datos");
const archivos = readdirSync(origen).filter((f) => f.endsWith(".json") && f !== "esquema.json");

mkdirSync(build, { recursive: true });
mkdirSync(publico, { recursive: true });
for (const f of archivos) {
  cpSync(join(origen, f), join(build, f));
  if (f !== "resumen.json") cpSync(join(origen, f), join(publico, f));
}
console.log(`datos: ${archivos.length} archivos de data/web`);
