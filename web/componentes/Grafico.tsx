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
  fallo = false,
}: {
  dibujar: (ancho: number) => SVGSVGElement | HTMLElement;
  // false mientras se bajan los datos: reserva el lugar y no dibuja
  listo?: boolean;
  // true si los datos no se pudieron bajar: en el lugar del grafico queda el aviso
  fallo?: boolean;
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
    if (!el || ancho === 0 || !listo || fallo) return;
    const grafico = dibujar(ancho);
    // el contenedor ya es role="img" con su descripcion: lo de adentro no se lee de a pedazos
    grafico.setAttribute("aria-hidden", "true");
    el.replaceChildren(grafico);
    return () => grafico.remove();
  }, [dibujar, ancho, listo, fallo]);

  if (fallo) {
    return (
      <div
        className={`flex w-full items-center border border-dashed border-filete px-4 text-[0.9375rem] text-tinta-2 ${className}`}
        style={{ minHeight: alto }}
      >
        <p>
          No se pudieron bajar los datos de este gráfico. Revisá la conexión y
          recargá la página.
        </p>
      </div>
    );
  }

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
