// paleta okabe-ito para las seis regiones del ipc. ambar y celeste no llegan a contraste AA
// como texto sobre el papel: van solo de relleno, el texto siempre en tinta
export const REGIONES = ["GBA", "Pampeana", "Noreste", "Noroeste", "Cuyo", "Patagonia"] as const;
export type RegionId = (typeof REGIONES)[number];

export const COLOR_REGION: Record<RegionId, string> = {
  GBA: "#0072B2",
  Pampeana: "#009E73",
  Noroeste: "#D55E00",
  Noreste: "#CC79A7",
  Cuyo: "#E69F00",
  Patagonia: "#56B4E9",
};

export const TINTA = "#1A1A1A";
export const TINTA_2 = "#595752";
export const FILETE = "#DFDDD5";
export const PAPEL = "#FAF9F6";
export const PAPEL_2 = "#F2F0E9";
// energia: tarifa regulada, va en gris pizarra y punteado
export const CONTRASTE = "#6B7280";
export const PUNTEADO_CONTRASTE = "4 3";
// lo que no se distingue de cero
export const NO_SIGNIFICATIVO = "#A8A59C";

export function esRegion(x: string): x is RegionId {
  return (REGIONES as readonly string[]).includes(x);
}
