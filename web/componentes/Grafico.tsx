"use client";

import { useEffect, useRef, useState } from "react";

// envoltorio de observable plot: mide el ancho disponible y vuelve a dibujar cuando cambia.
// el alto se reserva desde el principio para que la pagina no salte al cargar
export function Grafico({
  dibujar,
  alto,
  descripcion,
  className = "",
  listo = true,
}: {
  dibujar: (ancho: number) => SVGSVGElement | HTMLElement;
  // false mientras se bajan los datos: reserva el lugar y no dibuja
  listo?: boolean;
  alto: number;
  descripcion: string;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [ancho, setAncho] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new ResizeObserver(([e]) =>
      setAncho(Math.floor(e.contentRect.width)),
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el || ancho === 0 || !listo) return;
    const grafico = dibujar(ancho);
    el.replaceChildren(grafico);
    return () => grafico.remove();
  }, [dibujar, ancho, listo]);

  return (
    <div
      ref={ref}
      role="img"
      aria-label={descripcion}
      className={`grafico w-full ${className}`}
      style={{ minHeight: alto }}
    />
  );
}
