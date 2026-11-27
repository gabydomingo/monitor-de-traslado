"use client";

import { useCallback } from "react";
import { useArchivo, useCerca } from "@/lib/cliente";
import { calendario } from "@/lib/graficos";
import { Grafico } from "./Grafico";

// que dia del mes publico el indec cada dato: de ahi sale cuando corre el pronostico
export function Calendario() {
  const [ref, cerca] = useCerca<HTMLElement>();
  const publicaciones = useArchivo("historial", cerca)?.publicaciones ?? [];
  const dibujar = useCallback(
    (w: number) =>
      calendario(
        publicaciones.map((p) => ({
          dataset: p.dataset,
          mes: p.publicado.slice(0, 7),
          dia: Number(p.publicado.slice(8, 10)),
        })),
        w,
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [publicaciones.length],
  );
  return (
    <figure ref={ref} className="mt-8 border-t border-filete pt-4">
      <figcaption className="font-sans text-[0.9375rem] font-semibold">
        Qué día del mes publica el INDEC
      </figcaption>
      <Grafico
        dibujar={dibujar}
        listo={publicaciones.length > 0}
        alto={200}
        descripcion="Día del mes en que el INDEC publicó cada IPC y cada índice mayorista desde 2017"
        className="mt-2"
      />
      <p className="mt-1 max-w-[65ch] text-[0.8125rem] text-tinta-2">
        Puntos llenos: IPC. Vacíos: mayoristas. Salen de las mismas páginas de
        los informes. El pronóstico se hace el día que sale el mayorista.
      </p>
    </figure>
  );
}
