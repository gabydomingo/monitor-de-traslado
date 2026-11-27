"use client";

import { useEffect, useRef, useState } from "react";
import type { Backtest, Historial, Series } from "./tipos";

// los json de abajo de la pagina se bajan en el navegador, no vienen en el html.
// una sola descarga por archivo aunque los pidan varios componentes
type Archivos = { series: Series; backtest: Backtest; historial: Historial };

const pedidos = new Map<string, Promise<unknown>>();

function bajar<K extends keyof Archivos>(nombre: K): Promise<Archivos[K]> {
  let p = pedidos.get(nombre);
  if (!p) {
    p = fetch(`/datos/${nombre}.json`).then((r) => {
      if (!r.ok) throw new Error(`${nombre}.json: ${r.status}`);
      return r.json();
    });
    // si falla, que el proximo intento vuelva a pedirlo
    p.catch(() => pedidos.delete(nombre));
    pedidos.set(nombre, p);
  }
  return p as Promise<Archivos[K]>;
}

/** baja el archivo cuando `activo` es true; devuelve undefined mientras tanto */
export function useArchivo<K extends keyof Archivos>(nombre: K, activo = true) {
  const [dato, setDato] = useState<Archivos[K]>();
  useEffect(() => {
    if (!activo) return;
    let vivo = true;
    bajar(nombre)
      .then((d) => vivo && setDato(d))
      .catch(() => {});
    return () => {
      vivo = false;
    };
  }, [nombre, activo]);
  return dato;
}

/** true cuando el elemento esta cerca de entrar en pantalla (y se queda en true) */
export function useCerca<T extends Element>(margen = "800px") {
  const ref = useRef<T>(null);
  const [cerca, setCerca] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || cerca) return;
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) setCerca(true);
      },
      { rootMargin: margen },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [cerca, margen]);
  return [ref, cerca] as const;
}
