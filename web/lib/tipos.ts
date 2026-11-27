// generado por scripts/tipos.mjs desde data/web/esquema.json. no editar a mano

export interface Archivos {
  resumen: Resumen;
  series: Series;
  backtest: Backtest;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Resumen".
 */
export interface Resumen {
  meta: Meta;
  regiones: Region[];
  rubros: Rubro[];
  ultimoDato: Dato[];
  pronosticos: Pronostico[];
  traslado: Traslado[];
  trasladoRegimen: TrasladoRegimen[];
  cadena: Cadena[];
  metricas: Metricas[];
  errorAnual: ErrorAnual[];
  registro: Registrado[];
  revisiones: Revisiones;
  automatizacion: Automatizacion;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Meta".
 */
export interface Meta {
  /**
   * ultimo mes con IPC publicado
   */
  ultimoMes: string;
  mesPronosticado: string;
  proximoIpc: ProximoDato;
  /**
   * false entre que sale el ipc del mes pronosticado y el pronostico siguiente
   */
  pronosticoVigente: boolean;
  proximoPronostico: ProximoDato1;
  /**
   * la ultima vez que la ingesta trajo algo distinto
   */
  datosNuevos: string;
  versionModelo: string;
  versionDatos: string;
  repo: string;
  fuentes: Fuente[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "ProximoDato".
 */
export interface ProximoDato {
  /**
   * el mes que se va a publicar
   */
  mes: string;
  /**
   * el mes en que sale
   */
  publicacion: string;
  diaDesde: number;
  diaHasta: number;
}
/**
 * mes = el que se va a pronosticar; sale cuando el indec publica el mayorista
 */
export interface ProximoDato1 {
  /**
   * el mes que se va a publicar
   */
  mes: string;
  /**
   * el mes en que sale
   */
  publicacion: string;
  diaDesde: number;
  diaHasta: number;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Fuente".
 */
export interface Fuente {
  nombre: string;
  que: string;
  url: string;
  licencia: string;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Region".
 */
export interface Region {
  id: string;
  nombre: string;
  queAbarca: string;
  provincias: string[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Rubro".
 */
export interface Rubro {
  id: string;
  nombre: string;
  /**
   * energia: tarifa regulada, referencia de contraste
   */
  esContraste: boolean;
  esGeneral: boolean;
  etapas: ("industria" | "primaria")[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Dato".
 */
export interface Dato {
  region: string;
  rubro: string;
  /**
   * % mensual
   */
  valor: number;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Pronostico".
 */
export interface Pronostico {
  region: string;
  rubro: string;
  /**
   * % mensual
   */
  valor: number;
  /**
   * @minItems 2
   * @maxItems 2
   */
  banda80: [number, number];
  /**
   * @minItems 2
   * @maxItems 2
   */
  banda90: [number, number];
  /**
   * el dato del mes anterior, o sea el naive
   */
  ultimo: number | null;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Traslado".
 */
export interface Traslado {
  region: string;
  rubro: string;
  etapa: "industria" | "primaria";
  /**
   * cuanto de la suba relativa del mayorista llega
   */
  largoPlazo: number;
  /**
   * @minItems 2
   * @maxItems 2
   */
  intervalo: [number, number];
  /**
   * despues de corregir por comparaciones multiples
   */
  significativo: boolean;
  /**
   * mes 0 a 3
   *
   * @minItems 4
   * @maxItems 4
   */
  porMes: [number, number, number, number];
  n: number;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "TrasladoRegimen".
 */
export interface TrasladoRegimen {
  rubro: string;
  regimen: "baja" | "media" | "alta";
  largoPlazo: number;
  /**
   * @minItems 2
   * @maxItems 2
   */
  intervalo: [number, number];
  /**
   * p < 0.05, sin corregir
   */
  significativo: boolean;
  n: number;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Cadena".
 */
export interface Cadena {
  rubro: string;
  origen: "primaria" | "industria";
  /**
   * acumulada, mes 0 en adelante
   */
  respuesta: number[];
  inferior: number[];
  superior: number[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Metricas".
 */
export interface Metricas {
  grupo: "rubros" | "nivel_general";
  meses: number;
  series: number;
  /**
   * error medio en pp
   */
  naive: number;
  arx: number;
  lgbm: number;
  combinado: number;
  /**
   * diebold-mariano, combinado contra naive
   */
  pValor: number;
  cobertura80: number;
  cobertura90: number;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "ErrorAnual".
 */
export interface ErrorAnual {
  grupo: "rubros" | "nivel_general";
  anio: number;
  naive: number;
  combinado: number;
  meses: number;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Registrado".
 */
export interface Registrado {
  mes: string;
  region: string;
  rubro: string;
  pronostico: number;
  /**
   * @minItems 2
   * @maxItems 2
   */
  banda80: [number, number];
  banda90: [number, number] | null;
  /**
   * vacio hasta que el indec publica el mes
   */
  real: number | null;
  generado: string;
  modelo: string;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Revisiones".
 */
export interface Revisiones {
  comparados: number;
  corregidos: number;
  informes: number;
  desde: string;
  hasta: string;
  publicaciones: Publicacion[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Publicacion".
 */
export interface Publicacion {
  dataset: "ipc" | "mayorista";
  mes: string;
  publicado: string;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Automatizacion".
 */
export interface Automatizacion {
  primerMes: string;
  mesesIpc: number;
  descargas: number;
  mesesRegistrados: number;
  primerRegistro: string | null;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Series".
 */
export interface Series {
  meses: string[];
  rubros: SerieRubro[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "SerieRubro".
 */
export interface SerieRubro {
  rubro: string;
  mayorista: (number | null)[];
  /**
   * por region
   */
  gondola: {
    [k: string]: (number | null)[];
  };
  /**
   * GBA, ventana movil
   */
  trasladoMovil: (number | null)[] | null;
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Backtest".
 */
export interface Backtest {
  meses: string[];
  series: Acierto[];
}
/**
 * This interface was referenced by `Archivos`'s JSON-Schema
 * via the `definition` "Acierto".
 */
export interface Acierto {
  region: string;
  rubro: string;
  real: (number | null)[];
  pronostico: (number | null)[];
  naive: (number | null)[];
  inf80: (number | null)[];
  sup80: (number | null)[];
  inf90: (number | null)[];
  sup90: (number | null)[];
}
