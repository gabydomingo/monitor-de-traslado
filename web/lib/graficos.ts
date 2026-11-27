import * as Plot from "@observablehq/plot";
import {
  CONTRASTE,
  FILETE,
  NO_SIGNIFICATIVO,
  PUNTEADO_CONTRASTE,
  TINTA,
  TINTA_2,
} from "./colores";
import { fechaMes, mesCorto, mesLargo, num, parte, pct } from "./formato";

// todos los graficos salen de aca: mismas letras, ejes y colores en toda la pagina

const ESTILO = {
  fontSize: "12px",
  fontFamily: "inherit",
  color: TINTA_2,
  background: "transparent",
  overflow: "visible",
} as const;

const fmtPct = (d: number) => pct(d, 0);
// energia: relleno pizarra tenue con borde punteado, la marca de tarifa regulada
const BARRA_CONTRASTE = {
  fill: CONTRASTE,
  fillOpacity: 0.35,
  stroke: CONTRASTE,
  strokeWidth: 1.25,
  strokeDasharray: PUNTEADO_CONTRASTE,
} as const;

// borde color papel atras del texto, para que se lea arriba de lineas y barras
const HALO = {
  stroke: "#FAF9F6",
  strokeWidth: 3,
  paintOrder: "stroke",
} as const;

/** separa dos etiquetas de fin de linea si quedan muy juntas: devuelve el corrimiento en px */
function separar(a: number, b: number, rango: number): [number, number] {
  if (Math.abs(a - b) > rango * 0.08) return [0, 0];
  return a >= b ? [-7, 7] : [7, -7];
}
// margen izquierdo justo para la etiqueta mas larga (12px de Public Sans, ~6.4px por letra)
function margen(etiquetas: string[], ancho: number) {
  const largo = Math.max(...etiquetas.map((e) => e.length));
  return Math.min(Math.round(largo * 6.4) + 14, Math.round(ancho * 0.5));
}

// el globo de los tooltips en el papel de la pagina, con filete y sin la sombra de plot
const TIP = { fill: "#FAF9F6", stroke: FILETE, pathFilter: "none" } as const;

// en celular los nombres largos no entran al lado de las barras
const CORTOS: Record<string, string> = {
  "Electricidad, gas y combustibles": "Electricidad y gas",
  "Diarios, libros y papelería": "Diarios y libros",
  "Aguas gaseosas y jugos": "Gaseosas y jugos",
  "Equipamiento del hogar": "Equip. del hogar",
  "Productos medicinales": "Medicamentos",
  "Verduras y legumbres": "Verduras",
  "Bebidas alcohólicas": "Bebidas alcoh.",
  "Compra de vehículos": "Vehículos",
};
export const corto = (nombre: string, angosto: boolean) =>
  angosto ? (CORTOS[nombre] ?? nombre) : nombre;

const fmtMes = (d: Date) => {
  const m = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
  return mesCorto(m);
};

// ---------------------------------------------------------------- panel de la region

export interface Barra {
  nombre: string;
  valor: number;
  contraste: boolean;
}

/** inflacion del ultimo mes por rubro, de mayor a menor, con el nivel general de referencia */
export function barrasMes(
  datos: Barra[],
  general: number,
  color: string,
  ancho: number,
) {
  const angosto = ancho < 480;
  const orden = [...datos]
    .sort((a, b) => b.valor - a.valor)
    .map((d) => ({ ...d, nombre: corto(d.nombre, angosto) }));
  const max = Math.max(general, ...orden.map((d) => d.valor));
  const min = Math.min(0, ...orden.map((d) => d.valor));
  const izq = margen(
    orden.map((d) => d.nombre),
    ancho,
  );
  // si la barra termina justo antes de la linea del general, el numero va despues de la linea
  const umbral = (30 * (max * 1.04 - min)) / Math.max(1, ancho - izq - 44);
  const xEtiqueta = (d: Barra) =>
    d.valor < general && general - d.valor < umbral ? general : d.valor;
  return Plot.plot({
    width: ancho,
    height: orden.length * 22 + 36,
    marginLeft: izq,
    marginRight: 44,
    marginTop: 26,
    style: ESTILO,
    x: { domain: [min, max * 1.04], axis: null },
    y: {
      domain: orden.map((d) => d.nombre),
      label: null,
      tickSize: 0,
      tickPadding: 8,
    },
    marks: [
      Plot.ruleX([general], { stroke: TINTA, strokeDasharray: "2 2" }),
      Plot.barX(orden, {
        filter: (d: Barra) => !d.contraste,
        x: "valor",
        y: "nombre",
        fill: color,
        insetTop: 4,
        insetBottom: 4,
      }),
      Plot.barX(orden, {
        filter: (d: Barra) => d.contraste,
        x: "valor",
        y: "nombre",
        ...BARRA_CONTRASTE,
        insetTop: 4,
        insetBottom: 4,
      }),
      Plot.ruleX([0], { stroke: TINTA }),
      Plot.text([general], {
        x: (d: number) => d,
        frameAnchor: "top",
        dy: -16,
        text: (d: number) => `Nivel general ${pct(d)}`,
        fill: TINTA,
        textAnchor: "middle",
      }),
      Plot.text(orden, {
        x: xEtiqueta,
        y: "nombre",
        text: (d: Barra) => pct(d.valor),
        dx: 4,
        textAnchor: "start",
        fill: TINTA,
        ...HALO,
        filter: (d: Barra) => d.valor >= 0,
      }),
      Plot.text(orden, {
        x: 0,
        y: "nombre",
        text: (d: Barra) => pct(d.valor),
        dx: 4,
        textAnchor: "start",
        fill: TINTA,
        ...HALO,
        filter: (d: Barra) => d.valor < 0,
      }),
    ],
  });
}

export interface PuntoMes {
  mes: string;
  valor: number | null;
}

export interface Pron {
  mes: string;
  valor: number;
  banda80: [number, number];
  banda90: [number, number];
}

/** ultimos meses del dato real y el pronostico del que viene, abierto en abanico */
export function abanico(
  serie: PuntoMes[],
  p: Pron,
  ancho: number,
  alto = 220,
  fue: number | null = null,
) {
  const real = serie.filter((d) => d.valor !== null) as {
    mes: string;
    valor: number;
  }[];
  const ultimo = real[real.length - 1];
  const x0 = fechaMes(ultimo.mes);
  const x1 = fechaMes(p.mes);
  const banda = (b: [number, number]) => [
    { x: x0, y1: ultimo.valor, y2: ultimo.valor },
    { x: x1, y1: b[0], y2: b[1] },
  ];
  const valores = [
    ...real.map((d) => d.valor),
    p.banda90[0],
    p.banda90[1],
    ...(fue === null ? [] : [fue]),
  ];
  return Plot.plot({
    width: ancho,
    height: alto,
    marginLeft: 36,
    marginRight: 52,
    marginBottom: 28,
    style: ESTILO,
    x: {
      type: "utc",
      tickFormat: fmtMes,
      ticks: ancho < 420 ? 4 : 6,
      label: null,
    },
    y: {
      domain: [Math.min(0, ...valores), Math.max(...valores) * 1.08],
      tickFormat: fmtPct,
      grid: true,
      label: null,
      ticks: 4,
    },
    marks: [
      Plot.gridY({ stroke: FILETE, strokeOpacity: 1, ticks: 4 }),
      Plot.ruleY([0], { stroke: TINTA_2 }),
      Plot.areaY(banda(p.banda90), {
        x: "x",
        y1: "y1",
        y2: "y2",
        fill: TINTA,
        fillOpacity: 0.1,
      }),
      Plot.areaY(banda(p.banda80), {
        x: "x",
        y1: "y1",
        y2: "y2",
        fill: TINTA,
        fillOpacity: 0.22,
      }),
      Plot.lineY(real, {
        x: (d) => fechaMes(d.mes),
        y: "valor",
        stroke: TINTA,
        strokeWidth: 1.75,
      }),
      Plot.dot(real, {
        x: (d) => fechaMes(d.mes),
        y: "valor",
        fill: TINTA,
        r: 2.5,
      }),
      Plot.line(
        [
          { x: x0, y: ultimo.valor },
          { x: x1, y: p.valor },
        ],
        {
          x: "x",
          y: "y",
          stroke: TINTA,
          strokeDasharray: "3 3",
          strokeWidth: 1.5,
        },
      ),
      Plot.dot([{ x: x1, y: p.valor }], {
        x: "x",
        y: "y",
        fill: "#FAF9F6",
        stroke: TINTA,
        r: 4,
        strokeWidth: 1.5,
      }),
      Plot.text([{ x: x1, y: p.valor }], {
        x: "x",
        y: "y",
        text: () => pct(p.valor),
        dx: 8,
        textAnchor: "start",
        fill: TINTA,
        fontWeight: 600,
      }),
      // ya salio el dato: punto lleno con lo que fue
      ...(fue === null
        ? []
        : [
            Plot.dot([{ x: x1, y: fue }], {
              x: "x",
              y: "y",
              fill: TINTA,
              r: 4,
            }),
            Plot.text([{ x: x1, y: fue }], {
              x: "x",
              y: "y",
              text: () => `fue ${pct(fue)}`,
              dx: 8,
              dy: fue > p.valor ? -10 : 10,
              textAnchor: "start",
              fill: TINTA,
              ...HALO,
            }),
          ]),
      Plot.tip(
        real,
        Plot.pointerX({
          ...TIP,
          x: (d) => fechaMes(d.mes),
          y: "valor",
          title: (d) => `${mesLargo(d.mes)}: ${pct(d.valor)}`,
        }),
      ),
    ],
  });
}

export interface FilaTraslado {
  nombre: string;
  valor: number;
  inf: number;
  sup: number;
  significativo: boolean;
  contraste: boolean;
}

const DOMINIO_TRASLADO: [number, number] = [-0.6, 1.8];
const recortar = (v: number) =>
  Math.max(DOMINIO_TRASLADO[0], Math.min(DOMINIO_TRASLADO[1], v));

/** traslado de largo plazo por rubro: punto con su rango; en gris lo que no se distingue de cero */
export function trasladoRubros(filas: FilaTraslado[], ancho: number) {
  const angosto = ancho < 480;
  const orden = [...filas]
    .sort((a, b) => b.valor - a.valor)
    .map((d) => ({ ...d, nombre: corto(d.nombre, angosto) }));
  const color = (d: FilaTraslado) =>
    d.contraste ? CONTRASTE : d.significativo ? TINTA : NO_SIGNIFICATIVO;
  return Plot.plot({
    width: ancho,
    height: orden.length * 22 + 50,
    marginLeft: margen(
      orden.map((d) => d.nombre),
      ancho,
    ),
    marginRight: 16,
    marginTop: 8,
    marginBottom: 34,
    style: ESTILO,
    x: {
      domain: DOMINIO_TRASLADO,
      tickFormat: (d: number) => parte(d),
      ticks: [-0.5, 0, 0.5, 1, 1.5],
      label: null,
    },
    y: {
      domain: orden.map((d) => d.nombre),
      label: null,
      tickSize: 0,
      tickPadding: 8,
    },
    marks: [
      Plot.ruleX([0], { stroke: TINTA_2 }),
      Plot.ruleX([1], { stroke: TINTA_2, strokeDasharray: "2 2" }),
      Plot.text([1], {
        x: (d: number) => d,
        frameAnchor: "bottom",
        dy: 28,
        text: () => "llega todo",
        fill: TINTA_2,
        fontSize: 11,
      }),
      Plot.ruleY(orden, {
        filter: (d: FilaTraslado) => !d.contraste,
        y: "nombre",
        x1: (d: FilaTraslado) => recortar(d.inf),
        x2: (d: FilaTraslado) => recortar(d.sup),
        stroke: color,
        strokeWidth: 1.5,
      }),
      Plot.ruleY(orden, {
        filter: (d: FilaTraslado) => d.contraste,
        y: "nombre",
        x1: (d: FilaTraslado) => recortar(d.inf),
        x2: (d: FilaTraslado) => recortar(d.sup),
        stroke: CONTRASTE,
        strokeWidth: 1.5,
        strokeDasharray: PUNTEADO_CONTRASTE,
      }),
      Plot.dot(orden, {
        x: (d: FilaTraslado) => recortar(d.valor),
        y: "nombre",
        fill: color,
        r: 4,
      }),
      Plot.tip(
        orden,
        Plot.pointerY({
          ...TIP,
          x: (d: FilaTraslado) => recortar(d.valor),
          y: "nombre",
          title: (d: FilaTraslado) =>
            `${d.nombre}: llega ${parte(d.valor)} (entre ${parte(d.inf)} y ${parte(d.sup)})` +
            (d.significativo ? "" : ". No se distingue de cero"),
        }),
      ),
    ],
  });
}

// ---------------------------------------------------------------- vista por rubro

export interface PuntoSerie {
  mes: string;
  valor: number;
  serie: "Mayorista" | "Góndola";
}

/** variacion mensual del mayorista y de la gondola del rubro */
export function mayoristaVsGondola(
  datos: PuntoSerie[],
  color: string,
  contraste: boolean,
  ancho: number,
) {
  const ultimos = (s: PuntoSerie["serie"]) =>
    datos.filter((d) => d.serie === s).at(-1);
  const m = ultimos("Mayorista");
  const g = ultimos("Góndola");
  const valores = datos.map((d) => d.valor);
  const [dm, dg] =
    m && g
      ? separar(m.valor, g.valor, Math.max(...valores) - Math.min(...valores))
      : [0, 0];
  return Plot.plot({
    width: ancho,
    height: 280,
    marginLeft: 40,
    marginRight: 78,
    marginBottom: 28,
    style: ESTILO,
    x: {
      type: "utc",
      tickFormat: fmtMes,
      ticks: ancho < 480 ? 4 : 8,
      label: null,
    },
    y: { tickFormat: fmtPct, grid: true, label: null, ticks: 5 },
    marks: [
      Plot.gridY({ stroke: FILETE, strokeOpacity: 1, ticks: 5 }),
      Plot.ruleY([0], { stroke: TINTA_2 }),
      Plot.lineY(datos, {
        filter: (d: PuntoSerie) => d.serie === "Mayorista",
        x: (d: PuntoSerie) => fechaMes(d.mes),
        y: "valor",
        stroke: TINTA,
        strokeWidth: 1.25,
      }),
      Plot.lineY(datos, {
        filter: (d: PuntoSerie) => d.serie === "Góndola",
        x: (d: PuntoSerie) => fechaMes(d.mes),
        y: "valor",
        stroke: contraste ? CONTRASTE : color,
        strokeWidth: 2.25,
        strokeDasharray: contraste ? PUNTEADO_CONTRASTE : undefined,
      }),
      Plot.text(m ? [m] : [], {
        x: (d: PuntoSerie) => fechaMes(d.mes),
        y: "valor",
        text: () => "Mayorista",
        dx: 6,
        dy: dm,
        textAnchor: "start",
        fill: TINTA,
      }),
      Plot.text(g ? [g] : [], {
        x: (d: PuntoSerie) => fechaMes(d.mes),
        y: "valor",
        text: () => "Góndola",
        dx: 6,
        dy: dg,
        textAnchor: "start",
        fill: TINTA,
        fontWeight: 600,
      }),
      Plot.tip(
        datos,
        Plot.pointerX({
          ...TIP,
          x: (d: PuntoSerie) => fechaMes(d.mes),
          y: "valor",
          title: (d: PuntoSerie) =>
            `${d.serie}, ${mesLargo(d.mes)}: ${pct(d.valor)}`,
        }),
      ),
    ],
  });
}

const MESES_TRASLADO = ["Mismo mes", "1 mes", "2 meses", "3 meses"];

/** cuanto llega en cada mes despues de la suba del mayorista */
export function porMes(
  valores: number[],
  significativo: boolean,
  contraste: boolean,
  ancho: number,
) {
  const datos = valores.map((v, i) => ({ mes: MESES_TRASLADO[i], v }));
  const lim = Math.max(0.3, ...valores.map(Math.abs)) * 1.15;
  return Plot.plot({
    width: ancho,
    height: 170,
    marginLeft: 40,
    marginTop: 22,
    marginBottom: 30,
    style: ESTILO,
    x: { domain: MESES_TRASLADO, label: null, tickSize: 0, padding: 0.35 },
    y: {
      domain: [Math.min(0, ...valores) * 1.15, lim],
      tickFormat: (d: number) => parte(d),
      ticks: 3,
      label: null,
      grid: true,
    },
    marks: [
      Plot.gridY({ stroke: FILETE, strokeOpacity: 1, ticks: 3 }),
      contraste
        ? Plot.barY(datos, { x: "mes", y: "v", ...BARRA_CONTRASTE })
        : Plot.barY(datos, {
            x: "mes",
            y: "v",
            fill: significativo ? TINTA : NO_SIGNIFICATIVO,
          }),
      Plot.ruleY([0], { stroke: TINTA }),
      Plot.text(datos, {
        filter: (d: { v: number }) => d.v >= 0,
        x: "mes",
        y: "v",
        text: (d: { v: number }) => parte(d.v),
        dy: -8,
        fill: TINTA,
      }),
      Plot.text(datos, {
        filter: (d: { v: number }) => d.v < 0,
        x: "mes",
        y: "v",
        text: (d: { v: number }) => parte(d.v),
        dy: 10,
        fill: TINTA,
      }),
    ],
  });
}

export interface FilaRegimen {
  regimen: string;
  valor: number;
  inf: number;
  sup: number;
  significativo: boolean;
}

/** el traslado en epocas de inflacion baja, media y alta (gba) */
export function regimenes(
  filas: FilaRegimen[],
  contraste: boolean,
  ancho: number,
) {
  const color = (d: FilaRegimen) =>
    contraste ? CONTRASTE : d.significativo ? TINTA : NO_SIGNIFICATIVO;
  return Plot.plot({
    width: ancho,
    height: filas.length * 34 + 44,
    marginLeft: margen(
      filas.map((d) => d.regimen),
      ancho,
    ),
    marginRight: 16,
    marginBottom: 30,
    style: ESTILO,
    x: {
      domain: DOMINIO_TRASLADO,
      tickFormat: (d: number) => parte(d),
      ticks: [0, 0.5, 1, 1.5],
      label: null,
    },
    y: {
      domain: filas.map((d) => d.regimen),
      label: null,
      tickSize: 0,
      tickPadding: 8,
    },
    marks: [
      Plot.ruleX([0], { stroke: TINTA_2 }),
      Plot.ruleX([1], { stroke: TINTA_2, strokeDasharray: "2 2" }),
      Plot.ruleY(filas, {
        y: "regimen",
        x1: (d: FilaRegimen) => recortar(d.inf),
        x2: (d: FilaRegimen) => recortar(d.sup),
        stroke: color,
        strokeWidth: 1.5,
        strokeDasharray: contraste ? PUNTEADO_CONTRASTE : undefined,
      }),
      Plot.dot(filas, {
        x: (d: FilaRegimen) => recortar(d.valor),
        y: "regimen",
        fill: color,
        r: 4.5,
      }),
      Plot.text(filas, {
        x: (d: FilaRegimen) => recortar(d.valor),
        y: "regimen",
        text: (d: FilaRegimen) => parte(d.valor),
        dy: -11,
        fill: TINTA,
        ...HALO,
      }),
    ],
  });
}

export interface PuntoCadena {
  origen: string;
  mes: number;
  valor: number;
  inf: number;
  sup: number;
}

/** respuesta acumulada de la gondola a una suba en el productor o en la industria */
export function cadena(datos: PuntoCadena[], ancho: number) {
  const ultimo = Math.max(...datos.map((x) => x.mes));
  const fin = (o: string) =>
    datos.find((d) => d.mes === ultimo && d.origen === o);
  const pri = fin("primaria");
  const ind = fin("industria");
  const valores = datos.flatMap((d) => [d.inf, d.sup]);
  const [dp, di] =
    pri && ind
      ? separar(
          pri.valor,
          ind.valor,
          Math.max(...valores) - Math.min(...valores),
        )
      : [0, 0];
  return Plot.plot({
    width: ancho,
    height: 220,
    marginLeft: 40,
    marginRight: 70,
    marginBottom: 32,
    style: ESTILO,
    x: {
      domain: [0, 6],
      ticks: 7,
      tickFormat: (d: number) => (d === 0 ? "mes 0" : `${d}`),
      label: null,
    },
    y: {
      tickFormat: (d: number) => parte(d),
      grid: true,
      ticks: 4,
      label: null,
    },
    marks: [
      Plot.gridY({ stroke: FILETE, strokeOpacity: 1, ticks: 4 }),
      Plot.ruleY([0], { stroke: TINTA_2 }),
      Plot.areaY(datos, {
        x: "mes",
        y1: "inf",
        y2: "sup",
        z: "origen",
        fill: TINTA,
        fillOpacity: 0.08,
      }),
      Plot.lineY(datos, {
        filter: (d: PuntoCadena) => d.origen === "industria",
        x: "mes",
        y: "valor",
        stroke: TINTA,
        strokeWidth: 1.75,
      }),
      Plot.lineY(datos, {
        filter: (d: PuntoCadena) => d.origen === "primaria",
        x: "mes",
        y: "valor",
        stroke: TINTA_2,
        strokeWidth: 1.25,
      }),
      Plot.text(pri ? [pri] : [], {
        x: "mes",
        y: "valor",
        text: () => "Productor",
        dx: 6,
        dy: dp,
        textAnchor: "start",
        fill: TINTA,
      }),
      Plot.text(ind ? [ind] : [], {
        x: "mes",
        y: "valor",
        text: () => "Industria",
        dx: 6,
        dy: di,
        textAnchor: "start",
        fill: TINTA,
        fontWeight: 600,
      }),
    ],
  });
}

// ---------------------------------------------------------------- pronostico

export interface PuntoAcierto {
  mes: string;
  real: number;
  pron: number;
  inf80: number;
  sup80: number;
  inf90: number;
  sup90: number;
}

/** lo que dijo el modelo cada mes contra lo que paso, con sus bandas */
export function aciertos(datos: PuntoAcierto[], ancho: number) {
  const adentro = (d: PuntoAcierto) => d.real >= d.inf80 && d.real <= d.sup80;
  const x = (d: PuntoAcierto) => fechaMes(d.mes);
  return Plot.plot({
    width: ancho,
    height: 300,
    marginLeft: 40,
    marginRight: 20,
    marginBottom: 28,
    style: ESTILO,
    x: {
      type: "utc",
      tickFormat: fmtMes,
      ticks: ancho < 480 ? "6 months" : "3 months",
      label: null,
    },
    y: { tickFormat: fmtPct, grid: true, label: null, ticks: 5 },
    marks: [
      Plot.gridY({ stroke: FILETE, strokeOpacity: 1, ticks: 5 }),
      Plot.ruleY([0], { stroke: TINTA_2 }),
      Plot.areaY(datos, {
        x,
        y1: "inf90",
        y2: "sup90",
        fill: TINTA,
        fillOpacity: 0.1,
        curve: "step",
      }),
      Plot.areaY(datos, {
        x,
        y1: "inf80",
        y2: "sup80",
        fill: TINTA,
        fillOpacity: 0.22,
        curve: "step",
      }),
      Plot.lineY(datos, {
        x,
        y: "pron",
        stroke: TINTA,
        strokeDasharray: "3 3",
        strokeWidth: 1.25,
        curve: "step",
      }),
      Plot.dot(datos, {
        x,
        y: "real",
        r: 3.5,
        fill: (d: PuntoAcierto) => (adentro(d) ? TINTA : "#FAF9F6"),
        stroke: TINTA,
        strokeWidth: 1.25,
      }),
      Plot.tip(
        datos,
        Plot.pointerX({
          ...TIP,
          x,
          y: "real",
          title: (d: PuntoAcierto) =>
            `${mesLargo(d.mes)}\nDijo ${pct(d.pron)} (8 de 10: ${pct(d.inf80)} a ${pct(d.sup80)})\nFue ${pct(d.real)}`,
        }),
      ),
    ],
  });
}

// ---------------------------------------------------------------- revisiones

export interface PuntoPublicacion {
  dataset: "ipc" | "mayorista";
  mes: string;
  dia: number;
}

/** que dia del mes publico el indec cada dato */
export function calendario(datos: PuntoPublicacion[], ancho: number) {
  return Plot.plot({
    width: ancho,
    height: 200,
    marginLeft: 36,
    marginRight: 12,
    marginBottom: 28,
    style: ESTILO,
    x: {
      type: "utc",
      tickFormat: (d: Date) => `${d.getUTCFullYear()}`,
      ticks: ancho < 480 ? 4 : 9,
      label: null,
    },
    y: {
      domain: [8, 26],
      ticks: [10, 15, 20, 25],
      label: null,
      grid: true,
      tickFormat: (d: number) => `día ${num(d)}`,
    },
    marks: [
      Plot.gridY({ stroke: FILETE, strokeOpacity: 1, ticks: [10, 15, 20, 25] }),
      Plot.dot(datos, {
        x: (d: PuntoPublicacion) => fechaMes(d.mes),
        y: "dia",
        r: 2.25,
        fill: (d: PuntoPublicacion) =>
          d.dataset === "ipc" ? TINTA : "#FAF9F6",
        stroke: TINTA,
        strokeWidth: 1,
      }),
    ],
  });
}
