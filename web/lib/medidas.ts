import type { RegionId } from "./colores";

// medidas del mapa, compartidas entre el build (lib/mapa.ts) y el navegador
export const ANCHO = 520;
export const ALTO = 760;
// donde va el recuadro del gba: en el mar, a la altura del sur de buenos aires
export const RECUADRO = { x: 318, y: 318, ancho: 192, alto: 152 };

export interface Trazo {
  region: RegionId;
  d: string;
  etiqueta: [number, number];
}

export interface Mapa {
  regiones: Trazo[];
  provincias: string;
  recuadro: { regiones: Trazo[]; limites: string };
  // rectangulo del gba sobre el mapa grande, de donde sale la linea al recuadro
  marca: { x: number; y: number; ancho: number; alto: number };
}
