"use client";

import type { Resumen } from "@/lib/tipos";
import { ANCHO, ALTO, RECUADRO, type Mapa, type Trazo } from "@/lib/medidas";
import { COLOR_REGION, REGIONES, type RegionId } from "@/lib/colores";
import { NG, type Indice } from "@/lib/consultas";
import { nombreMes, pct } from "@/lib/formato";

// mapa de las seis regiones del ipc con un recuadro del gba. cada region es un boton:
// se elige con el mouse, con el dedo o con el teclado (tab y enter)
export function MapaRegiones({
  mapa,
  resumen,
  idx,
  region,
  onRegion,
}: {
  mapa: Mapa;
  resumen: Resumen;
  idx: Indice;
  region: RegionId;
  onRegion: (r: RegionId) => void;
}) {
  const { marca } = mapa;
  // la linea al recuadro sale del borde derecho de la marca del gba
  const linea = {
    x1: marca.x + marca.ancho,
    y1: marca.y + marca.alto / 2,
    x2: RECUADRO.x,
    y2: RECUADRO.y + RECUADRO.alto / 2,
  };

  return (
    <figure>
      <svg
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        className="mx-auto block h-auto w-full max-w-[460px]"
        role="group"
        aria-label="Mapa de las regiones del IPC. Elegí una región para ver sus datos"
      >
        <g>
          {mapa.regiones.map((t) => (
            <Region key={t.region} t={t} elegida={region} onRegion={onRegion} />
          ))}
        </g>
        {/* limites de provincia, finitos y en color papel: orientan sin competir */}
        <path d={mapa.provincias} fill="none" stroke="#FAF9F6" strokeWidth={0.6} pointerEvents="none" />
        <g pointerEvents="none">
          {mapa.regiones
            .filter((t) => t.region !== "GBA")
            .map((t) => (
              <Etiqueta key={t.region} t={t} elegida={t.region === region} />
            ))}
        </g>

        <rect
          x={marca.x}
          y={marca.y}
          width={marca.ancho}
          height={marca.alto}
          fill="none"
          stroke="#1A1A1A"
          strokeWidth={0.8}
          pointerEvents="none"
        />
        <line {...linea} stroke="#1A1A1A" strokeWidth={0.8} pointerEvents="none" />

        <g>
          <rect
            x={RECUADRO.x}
            y={RECUADRO.y}
            width={RECUADRO.ancho}
            height={RECUADRO.alto}
            fill="#FAF9F6"
            stroke="#1A1A1A"
            strokeWidth={1}
          />
          {mapa.recuadro.regiones.map((t) => (
            <Region key={t.region} t={t} elegida={region} onRegion={onRegion} recuadro />
          ))}
          <path
            d={mapa.recuadro.limites}
            fill="none"
            stroke="#FAF9F6"
            strokeWidth={0.5}
            pointerEvents="none"
          />
          <text x={RECUADRO.x} y={RECUADRO.y - 8} fontSize={15} fill="#1A1A1A" pointerEvents="none">
            <tspan fontWeight={700}>GBA</tspan>
            <tspan fill="#595752" fontSize={12} dx={6}>
              ciudad y 24 partidos
            </tspan>
          </text>
        </g>
      </svg>

      <figcaption className="mt-4">
        <p className="sr-only">También se puede elegir la región con esta lista.</p>
        <ul className="grid grid-cols-2 border-t border-filete sm:grid-cols-3">
          {REGIONES.map((r) => {
            const v = idx.ultimo(r, NG)?.valor;
            const activa = r === region;
            return (
              <li key={r} className="border-b border-filete">
                <button
                  type="button"
                  aria-pressed={activa}
                  onClick={() => onRegion(r)}
                  className={`flex w-full cursor-pointer items-center gap-2 px-2 py-2 text-left text-sm transition-colors duration-150 ease-out hover:bg-papel-2 ${
                    activa ? "bg-papel-2 font-semibold" : ""
                  }`}
                >
                  <span aria-hidden className="size-3 shrink-0 rounded-sm" style={{ background: COLOR_REGION[r] }} />
                  <span className="grow">{r}</span>
                  <span className="text-tinta-2">{pct(v)}</span>
                </button>
              </li>
            );
          })}
        </ul>
        <p className="mt-2 max-w-[65ch] text-[0.8125rem] text-tinta-2">
          Inflación de {nombreMes(resumen.meta.ultimoMes)}. El INDEC mide por región, no por provincia.
        </p>
      </figcaption>
    </figure>
  );
}

function Region({
  t,
  elegida,
  onRegion,
  recuadro = false,
}: {
  t: Trazo;
  elegida: RegionId;
  onRegion: (r: RegionId) => void;
  recuadro?: boolean;
}) {
  const activa = t.region === elegida;
  return (
    <path
      d={t.d}
      role="button"
      tabIndex={recuadro && t.region !== "GBA" ? -1 : 0}
      aria-label={`${t.region}${recuadro ? " (recuadro)" : ""}`}
      aria-pressed={activa}
      onClick={() => onRegion(t.region)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onRegion(t.region);
        }
      }}
      fill={COLOR_REGION[t.region]}
      fillOpacity={activa ? 1 : 0.42}
      stroke={activa ? "#1A1A1A" : "none"}
      strokeWidth={activa ? 1.2 : 0}
      strokeLinejoin="round"
      className="region cursor-pointer outline-none"
    />
  );
}

function Etiqueta({ t, elegida }: { t: Trazo; elegida: boolean }) {
  return (
    <text
      x={t.etiqueta[0]}
      y={t.etiqueta[1]}
      textAnchor="middle"
      fontSize={15}
      fontWeight={elegida ? 700 : 400}
      fill="#1A1A1A"
      stroke="#FAF9F6"
      strokeWidth={3}
      paintOrder="stroke"
    >
      {t.region}
    </text>
  );
}
