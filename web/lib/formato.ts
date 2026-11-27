// numeros y fechas en castellano rioplatense: coma decimal, meses en minuscula

const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

const numeros = new Map<number, Intl.NumberFormat>();
function nf(decimales: number) {
  let f = numeros.get(decimales);
  if (!f) {
    f = new Intl.NumberFormat("es-AR", {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    });
    numeros.set(decimales, f);
  }
  return f;
}

/** 1.98 -> "2,0%". El signo menos tipografico para los negativos */
export function pct(v: number | null | undefined, decimales = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "s/d";
  return nf(decimales).format(v).replace("-", "−") + "%";
}

export function num(v: number, decimales = 0): string {
  return nf(decimales).format(v).replace("-", "−");
}

/** "2026-10" -> "octubre" */
export function nombreMes(mes: string): string {
  return MESES[Number(mes.slice(5, 7)) - 1];
}

/** "2026-10" -> "octubre de 2026" */
export function mesLargo(mes: string): string {
  return `${nombreMes(mes)} de ${mes.slice(0, 4)}`;
}

/** "2026-10" -> "oct 26" */
export function mesCorto(mes: string): string {
  return `${nombreMes(mes).slice(0, 3)} ${mes.slice(2, 4)}`;
}

/** "2026-10" -> Date del primer dia, para los ejes */
export function fechaMes(mes: string): Date {
  return new Date(Date.UTC(Number(mes.slice(0, 4)), Number(mes.slice(5, 7)) - 1, 1));
}

/** fecha iso -> "26 de noviembre de 2026", en hora argentina */
export function fechaLarga(iso: string): string {
  const d = new Date(iso);
  const partes = new Intl.DateTimeFormat("es-AR", {
    timeZone: "America/Argentina/Buenos_Aires",
    day: "numeric",
    month: "numeric",
    year: "numeric",
  }).formatToParts(d);
  const dia = partes.find((p) => p.type === "day")!.value;
  const mes = Number(partes.find((p) => p.type === "month")!.value);
  const anio = partes.find((p) => p.type === "year")!.value;
  return `${dia} de ${MESES[mes - 1]} de ${anio}`;
}

/** traslado como porcentaje: 0.55 -> "55%" */
export function parte(v: number): string {
  return `${num(Math.round(v * 100))}%`;
}
