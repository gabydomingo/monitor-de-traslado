// copia los json que genera monitor.web (data/web, en la raiz del repo) adentro de web/.
// asi el build no depende de archivos fuera de la carpeta del proyecto
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { join } from "node:path";

const origen = join(import.meta.dirname, "..", "..", "data", "web");
const destino = join(import.meta.dirname, "..", "datos");
mkdirSync(destino, { recursive: true });
const archivos = readdirSync(origen).filter((f) => f.endsWith(".json"));
for (const f of archivos) cpSync(join(origen, f), join(destino, f));
console.log(`datos: ${archivos.length} archivos de data/web`);
