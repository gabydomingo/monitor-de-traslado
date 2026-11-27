// los nombres que vienen de los datos estan sin tildes (asi los normaliza el pipeline).
// para mostrarlos en la pagina se les devuelven aca, palabra por palabra

const PALABRAS: Record<string, string> = {
  alcoholicas: "alcohólicas",
  autonoma: "autónoma",
  azucar: "azúcar",
  cordoba: "córdoba",
  dolar: "dólar",
  geografico: "geográfico",
  gondola: "góndola",
  indices: "índices",
  indice: "índice",
  lacteos: "lácteos",
  limites: "límites",
  neuquen: "neuquén",
  papeleria: "papelería",
  publicos: "públicos",
  region: "región",
  rio: "río",
  rios: "ríos",
  tucuman: "tucumán",
  vehiculos: "vehículos",
  via: "vía",
};

// frases que ademas llevan coma
const FRASES: [RegExp, string][] = [
  [/^Electricidad gas y combustibles$/, "Electricidad, gas y combustibles"],
  [/^Diarios libros y papeleria$/, "Diarios, libros y papelería"],
];

export function conTildes(texto: string): string {
  let t = texto;
  for (const [re, por] of FRASES) t = t.replace(re, por);
  return t.replace(/\p{L}+/gu, (palabra) => {
    const nueva = PALABRAS[palabra.toLowerCase()];
    if (!nueva) return palabra;
    return palabra[0] === palabra[0].toUpperCase() ? nueva[0].toUpperCase() + nueva.slice(1) : nueva;
  });
}
