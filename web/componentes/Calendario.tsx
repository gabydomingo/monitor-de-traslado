"use client";

import { useCallback } from "react";
import type { Publicacion } from "@/lib/tipos";
import { calendario } from "@/lib/graficos";
import { Grafico } from "./Grafico";

// que dia del mes publico el indec cada dato: de ahi sale cuando corre el pronostico
export function Calendario({ publicaciones }: { publicaciones: Publicacion[] }) {
  const dibujar = useCallback(
    (w: number) =>
      calendario(
        publicaciones.map((p) => ({ dataset: p.dataset, mes: p.publicado.slice(0, 7), dia: Number(p.publicado.slice(8, 10)) })),
        w,
      ),
    [publicaciones],
  );
  return (
    <figure className="mt-8 border-t border-filete pt-4">
      <figcaption className="font-sans text-[0.9375rem] font-semibold">
        Que dia del mes publica el INDEC
      </figcaption>
      <Grafico
        dibujar={dibujar}
        alto={200}
        descripcion="Dia del mes en que el INDEC publico cada IPC y cada indice mayorista desde 2017"
        className="mt-2"
      />
      <p className="mt-1 max-w-[65ch] text-[0.8125rem] text-tinta-2">
        Puntos llenos: IPC. Vacios: mayoristas. Salen de las mismas paginas de los informes. El
        pronostico se hace el dia que sale el mayorista.
      </p>
    </figure>
  );
}
