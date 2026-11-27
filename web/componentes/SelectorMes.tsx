"use client";

import { mesLargo, nombreMes } from "@/lib/formato";
import { Chevron } from "./Chevron";

// flechas para ir de a un mes y una lista para saltar a cualquiera desde 2017
export function SelectorMes({
  meses,
  mes,
  ultimo,
  onMes,
}: {
  meses: string[];
  mes: string;
  ultimo: string;
  onMes: (m: string) => void;
}) {
  const i = meses.indexOf(mes);
  const anios = [...new Set(meses.map((m) => m.slice(0, 4)))].reverse();
  const flecha =
    "flex size-8 shrink-0 cursor-pointer items-center justify-center border border-filete transition-colors duration-150 ease-out hover:bg-papel-2 disabled:cursor-default disabled:text-filete disabled:hover:bg-transparent";

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      <div className="flex items-center">
        <button
          type="button"
          aria-label="Mes anterior"
          disabled={i <= 0}
          onClick={() => onMes(meses[i - 1])}
          className={flecha}
        >
          <svg aria-hidden viewBox="0 0 8 12" className="w-2">
            <path
              d="M6.5 1 1.5 6l5 5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
        </button>
        <span className="relative">
          <select
            aria-label="Elegir mes"
            value={mes}
            onChange={(e) => onMes(e.target.value)}
            className="h-8 min-w-[11rem] cursor-pointer appearance-none border-y border-filete bg-transparent pr-7 pl-3 text-sm transition-colors duration-150 ease-out hover:bg-papel-2"
          >
            {anios.map((a) => (
              <optgroup key={a} label={a}>
                {meses
                  .filter((m) => m.startsWith(a))
                  .reverse()
                  .map((m) => (
                    <option key={m} value={m}>
                      {mesLargo(m)}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
          <Chevron className="right-2 text-tinta" />
        </span>
        <button
          type="button"
          aria-label="Mes siguiente"
          disabled={i < 0 || mes >= ultimo}
          onClick={() => onMes(meses[i + 1])}
          className={flecha}
        >
          <svg aria-hidden viewBox="0 0 8 12" className="w-2">
            <path
              d="M1.5 1 6.5 6l-5 5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
        </button>
      </div>
      {mes !== ultimo && (
        <button
          type="button"
          onClick={() => onMes(ultimo)}
          className="cursor-pointer text-sm underline decoration-tinta-2 underline-offset-[3px] hover:decoration-tinta"
        >
          Volver a {nombreMes(ultimo)}
        </button>
      )}
    </div>
  );
}
