"use client";

import type { Resumen } from "@/lib/tipos";
import { REGIONES, COLOR_REGION, type RegionId } from "@/lib/colores";
import { NG, type Indice } from "@/lib/consultas";
import { nombreMes, pct } from "@/lib/formato";

// la franja de arriba: ultimo dato, pronostico con su banda, cuando sale el proximo y la region
export function Franja({
  resumen,
  idx,
  region,
  onRegion,
}: {
  resumen: Resumen;
  idx: Indice;
  region: RegionId;
  onRegion: (r: RegionId) => void;
}) {
  const { meta } = resumen;
  const ultimo = idx.ultimo(region, NG);
  const pron = idx.pronostico(region, NG);
  const info = resumen.regiones.find((r) => r.id === region)!;
  const prox = meta.proximoIpc;

  return (
    <div className="border-y border-tinta">
      <dl id="franja" className="mx-auto grid max-w-[1200px] grid-cols-2 md:grid-cols-4 md:px-8">
        <Celda
          titulo={`Inflacion de ${nombreMes(meta.ultimoMes)}`}
          className="border-r border-b border-filete md:border-b-0"
        >
          <Cifra>{pct(ultimo?.valor)}</Cifra>
          <Nota>Nivel general del IPC en {region}, segun el INDEC</Nota>
        </Celda>

        <Celda titulo={`Pronostico para ${nombreMes(meta.mesPronosticado)}`} className="border-b border-filete md:border-r md:border-b-0">
          <Cifra>{pct(pron?.valor)}</Cifra>
          {pron && (
            <Nota>
              8 de cada 10 veces el dato cae entre {pct(pron.banda80[0])} y {pct(pron.banda80[1])}.{" "}
              <a href="#pronostico">Cuanto le erra</a>
            </Nota>
          )}
        </Celda>

        <Celda titulo="Proximo dato del INDEC" className="border-r border-filete">
          <p className="font-serif text-[1.5rem] leading-tight font-medium md:text-[1.75rem]">
            {prox.diaDesde} al {prox.diaHasta} de {nombreMes(prox.publicacion)}
          </p>
          <Nota>
            Sale el IPC de {nombreMes(prox.mes)} y esta pagina se actualiza sola.{" "}
            <a href="#como-se-actualiza">Como</a>
          </Nota>
        </Celda>

        <Celda titulo="Region">
          <div className="relative">
            <span
              aria-hidden
              className="pointer-events-none absolute top-1/2 left-0 size-3 -translate-y-1/2 rounded-sm"
              style={{ background: COLOR_REGION[region] }}
            />
            <select
              aria-label="Elegir region"
              value={region}
              onChange={(e) => onRegion(e.target.value as RegionId)}
              className="w-full cursor-pointer appearance-none border-b border-tinta bg-transparent py-1 pr-6 pl-5 font-serif text-[1.5rem] leading-tight font-medium transition-colors duration-150 ease-out hover:bg-papel-2 md:text-[1.75rem]"
            >
              {REGIONES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
            <svg
              aria-hidden
              viewBox="0 0 12 8"
              className="pointer-events-none absolute top-1/2 right-1 w-3 -translate-y-1/2"
            >
              <path d="M1 1.5 6 6.5 11 1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </div>
          <Nota>{info.queAbarca}</Nota>
        </Celda>
      </dl>
    </div>
  );
}

function Celda({
  titulo,
  children,
  className = "",
}: {
  titulo: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col gap-1 px-4 py-4 md:px-5 md:py-5 md:first:pl-0 ${className}`}>
      <dt className="text-sm text-tinta-2">{titulo}</dt>
      <dd className="flex flex-col gap-1">{children}</dd>
    </div>
  );
}

function Cifra({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-serif text-[2.25rem] leading-none font-semibold tracking-tight md:text-[2.75rem]">
      {children}
    </p>
  );
}

function Nota({ children }: { children: React.ReactNode }) {
  return <p className="text-[0.8125rem] leading-snug text-tinta-2">{children}</p>;
}
