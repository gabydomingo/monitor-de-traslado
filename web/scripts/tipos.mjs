// genera lib/tipos.ts desde el json schema que escribe monitor.web. el contrato vive en
// python (pydantic): si cambia alla, se corre esto y typescript marca lo que se rompio
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { compile } from "json-schema-to-typescript";

const raiz = join(import.meta.dirname, "..");
const esquema = JSON.parse(readFileSync(join(raiz, "..", "data", "web", "esquema.json"), "utf8"));

// pydantic le pone "title" a cada campo y el generador lo convierte en un alias por campo
// (type Ultimomes = string). solo dejo el titulo de cada modelo
function sinTitulos(nodo, esModelo = false) {
  if (Array.isArray(nodo)) return nodo.map((x) => sinTitulos(x));
  if (nodo === null || typeof nodo !== "object") return nodo;
  const salida = {};
  for (const [k, v] of Object.entries(nodo)) {
    if (k === "title" && !esModelo) continue;
    // las tuplas de pydantic vienen como prefixItems (2020-12); el generador entiende items
    salida[k === "prefixItems" ? "items" : k] = sinTitulos(v);
  }
  return salida;
}
for (const [nombre, def] of Object.entries(esquema.$defs)) esquema.$defs[nombre] = sinTitulos(def, true);
// un tipo por cada definicion, y los tres archivos como raiz
const todo = {
  title: "Archivos",
  type: "object",
  properties: { resumen: { $ref: "#/$defs/Resumen" }, series: { $ref: "#/$defs/Series" }, backtest: { $ref: "#/$defs/Backtest" } },
  required: ["resumen", "series", "backtest"],
  additionalProperties: false,
  $defs: esquema.$defs,
};
const ts = await compile(todo, "Archivos", {
  bannerComment: "// generado por scripts/tipos.mjs desde data/web/esquema.json. no editar a mano",
  additionalProperties: false,
  unreachableDefinitions: true,
  style: { semi: true, printWidth: 100 },
});
writeFileSync(join(raiz, "lib", "tipos.ts"), ts);
console.log("tipos: lib/tipos.ts");
