"""Arma los JSON que lee la web (data/web) a partir del warehouse y de data/resultados.

El contrato son los modelos de pydantic de este archivo: de aca sale el JSON Schema y de
ahi los tipos de TypeScript de la web. Si algo no cumple el contrato, falla aca y no en el
navegador.

    uv run python -m monitor.web
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from monitor import analisis as a
from monitor import mensual, pronostico

log = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[2]
RESULTADOS = RAIZ / "data" / "resultados"
SALIDA = RAIZ / "data" / "web"
REPO = "https://github.com/gabydomingo/monitor-de-traslado"
NG = pronostico.NIVEL_GENERAL

Mes = str  # "2026-10"
Banda = tuple[float, float]


class Modelo(BaseModel):
    # snake_case en python, camelCase en el json
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)


# lo general


class Fuente(Modelo):
    nombre: str
    que: str
    url: str
    licencia: str


class ProximoDato(Modelo):
    mes: Mes = Field(description="el mes que se va a publicar")
    publicacion: Mes = Field(description="el mes en que sale")
    dia_desde: int
    dia_hasta: int


class Meta(Modelo):
    ultimo_mes: Mes = Field(description="ultimo mes con IPC publicado")
    mes_pronosticado: Mes
    proximo_ipc: ProximoDato
    pronostico_vigente: bool = Field(
        description="false entre que sale el ipc del mes pronosticado y el pronostico siguiente"
    )
    proximo_pronostico: ProximoDato = Field(
        description="mes = el que se va a pronosticar; sale cuando el indec publica el mayorista"
    )
    datos_nuevos: datetime = Field(description="la ultima vez que la ingesta trajo algo distinto")
    version_modelo: str
    version_datos: str
    repo: str
    fuentes: list[Fuente]


class Region(Modelo):
    id: str
    nombre: str
    que_abarca: str
    provincias: list[str]


class Rubro(Modelo):
    id: str
    nombre: str
    es_contraste: bool = Field(description="energia: tarifa regulada, referencia de contraste")
    es_general: bool
    etapas: list[Literal["industria", "primaria"]]


# por region y rubro


class Dato(Modelo):
    region: str
    rubro: str
    valor: float = Field(description="% mensual")


class Pronostico(Modelo):
    region: str
    rubro: str
    valor: float = Field(description="% mensual")
    banda80: Banda
    banda90: Banda
    ultimo: float | None = Field(description="el dato del mes anterior, o sea el naive")


class Traslado(Modelo):
    region: str
    rubro: str
    etapa: Literal["industria", "primaria"]
    largo_plazo: float = Field(description="cuanto de la suba relativa del mayorista llega")
    intervalo: Banda
    significativo: bool = Field(description="despues de corregir por comparaciones multiples")
    por_mes: tuple[float, float, float, float] = Field(description="mes 0 a 3")
    n: int


class TrasladoRegimen(Modelo):
    rubro: str
    regimen: Literal["baja", "media", "alta"]
    largo_plazo: float
    intervalo: Banda
    significativo: bool = Field(description="p < 0.05, sin corregir")
    n: int


class Cadena(Modelo):
    rubro: str
    origen: Literal["primaria", "industria"]
    respuesta: list[float] = Field(description="acumulada, mes 0 en adelante")
    inferior: list[float]
    superior: list[float]


class ErrorAnual(Modelo):
    grupo: Literal["rubros", "nivel_general"]
    anio: int
    naive: float
    combinado: float
    meses: int


class Metricas(Modelo):
    grupo: Literal["rubros", "nivel_general"]
    meses: int
    series: int
    naive: float = Field(description="error medio en pp")
    arx: float
    lgbm: float
    combinado: float
    p_valor: float = Field(description="diebold-mariano, combinado contra naive")
    cobertura80: float
    cobertura90: float


class Registrado(Modelo):
    mes: Mes
    region: str
    rubro: str
    pronostico: float
    banda80: Banda
    banda90: Banda | None
    real: float | None = Field(description="vacio hasta que el indec publica el mes")
    generado: datetime
    modelo: str


class Publicacion(Modelo):
    dataset: Literal["ipc", "mayorista"]
    mes: Mes
    publicado: date


class Revisiones(Modelo):
    comparados: int
    corregidos: int
    informes: int
    desde: Mes
    hasta: Mes


class Automatizacion(Modelo):
    primer_mes: Mes
    meses_ipc: int
    descargas: int
    meses_registrados: int
    primer_registro: Mes | None


class Resumen(Modelo):
    meta: Meta
    regiones: list[Region]
    rubros: list[Rubro]
    ultimo_dato: list[Dato]
    pronosticos: list[Pronostico]
    traslado: list[Traslado]
    traslado_regimen: list[TrasladoRegimen]
    cadena: list[Cadena]
    metricas: list[Metricas]
    error_anual: list[ErrorAnual]
    revisiones: Revisiones
    automatizacion: Automatizacion


# lo que esta mas abajo en la pagina va en otros archivos: el navegador los baja despues y
# quedan fuera del html. el registro ademas crece todos los meses


class Historial(Modelo):
    registro: list[Registrado]
    publicaciones: list[Publicacion]


class SerieRubro(Modelo):
    rubro: str
    mayorista: list[float | None]
    gondola: dict[str, list[float | None]] = Field(description="por region")
    traslado_movil: list[float | None] | None = Field(description="GBA, ventana movil")


class Series(Modelo):
    meses: list[Mes]
    rubros: list[SerieRubro]


class Acierto(Modelo):
    region: str
    rubro: str
    real: list[float | None]
    pronostico: list[float | None]
    naive: list[float | None]
    inf80: list[float | None]
    sup80: list[float | None]
    inf90: list[float | None]
    sup90: list[float | None]


class Backtest(Modelo):
    meses: list[Mes]
    series: list[Acierto]


ARCHIVOS = {"resumen": Resumen, "series": Series, "backtest": Backtest, "historial": Historial}

FUENTES = [
    Fuente(
        nombre="INDEC",
        que="IPC por region y rubro, Sistema de Indices de Precios Mayoristas, informes de prensa",
        url="https://www.indec.gob.ar",
        licencia="Datos publicos. Fuente: INDEC",
    ),
    Fuente(
        nombre="BCRA",
        que="Dolar mayorista (Com. A 3500) y expectativas del REM",
        url="https://www.bcra.gob.ar",
        licencia="Datos publicos. Fuente: BCRA",
    ),
    Fuente(
        nombre="IGN",
        que="Limites de provincias y partidos (SIG 250, via CONAE), simplificados para el mapa",
        url="https://github.com/mgaitan/departamentos_argentina",
        licencia="Fuente: Instituto Geografico Nacional. Convertido por mgaitan",
    ),
]

# el indec mide GBA como la ciudad mas los 24 partidos del conurbano; el resto de la
# provincia de Buenos Aires va en Pampeana
ABARCA = {
    "GBA": "Ciudad de Buenos Aires y los 24 partidos del conurbano",
    "Pampeana": "Buenos Aires sin el conurbano, Cordoba, Entre Rios, La Pampa y Santa Fe",
}


# helpers


def mes(f) -> Mes:
    return f"{pd.Timestamp(f):%Y-%m}"


def pct(log_var):
    """var_log -> % mensual con 2 decimales. Sirve para escalares y arrays."""
    return np.round(100 * np.expm1(log_var), 2)


def lista(serie) -> list[float | None]:
    return [None if pd.isna(v) else float(v) for v in serie]


def y_final(nombres: list[str]) -> str:
    return ", ".join(nombres[:-1]) + " y " + nombres[-1] if len(nombres) > 1 else "".join(nombres)


def r(v, n=2) -> float:
    return round(float(v), n)


# armado


def gondola_y_mayorista(con) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """var_log por rubro (columnas), con el nivel general como un rubro mas."""
    precios = a.cargar_precios(con)
    general = a.inflacion_general(con)
    gondola = {}
    for region in a.REGIONES:
        g = a.serie_por_rubro(precios, "gondola", region)
        g[NG] = general[region]
        gondola[region] = g
    industria = a.serie_por_rubro(precios, "industria")
    primaria = a.serie_por_rubro(precios, "primaria")
    mayorista = industria.combine_first(primaria[primaria.columns.difference(industria.columns)])
    mayorista[NG] = general["mayorista"]
    return gondola, mayorista


def armar_rubros(con) -> list[Rubro]:
    d = con.execute("select par_id, rubro, etapas, es_contraste from dim_rubro").df()
    rubros = [
        Rubro(
            id=f.par_id,
            nombre=f.rubro,
            es_contraste=bool(f.es_contraste),
            es_general=False,
            etapas=[e.strip() for e in f.etapas.split(",")],
        )
        for f in d.itertuples()
    ]
    general = Rubro(
        id=NG, nombre="Nivel general", es_contraste=False, es_general=True, etapas=["industria"]
    )
    return [general, *sorted(rubros, key=lambda x: x.nombre)]


def armar_regiones(con) -> list[Region]:
    d = con.execute("select provincia, region from dim_provincia order by provincia").df()
    return [
        Region(
            id=reg,
            nombre=reg,
            que_abarca=ABARCA.get(reg) or y_final(d[d.region == reg].provincia.tolist()),
            provincias=d[d.region == reg].provincia.tolist(),
        )
        for reg in a.REGIONES
    ]


def armar_pronosticos(prox: pd.DataFrame, gondola) -> list[Pronostico]:
    salida = []
    for f in prox.itertuples():
        previo = gondola[f.region][f.par_id].dropna()
        previo = previo[previo.index < pd.Timestamp(f.fecha)]
        salida.append(
            Pronostico(
                region=f.region,
                rubro=f.par_id,
                valor=r(f.pronostico),
                banda80=(r(f.inf), r(f.sup)),
                banda90=(r(f.inf_90), r(f.sup_90)),
                ultimo=float(pct(previo.iloc[-1])) if len(previo) else None,
            )
        )
    return salida


def armar_traslado() -> list[Traslado]:
    t = pd.read_csv(RESULTADOS / "traslado.csv")
    return [
        Traslado(
            region=f.region,
            rubro=f.par_id,
            etapa=f.etapa,
            largo_plazo=r(f.largo_plazo, 3),
            intervalo=(r(f.ic_inf, 3), r(f.ic_sup, 3)),
            significativo=bool(f.significativo_fdr),
            por_mes=(r(f.impacto, 3), r(f.mes_1, 3), r(f.mes_2, 3), r(f.mes_3, 3)),
            n=int(f.n),
        )
        for f in t.itertuples()
    ]


def armar_regimen() -> list[TrasladoRegimen]:
    t = pd.read_csv(RESULTADOS / "traslado_regimen.csv")
    return [
        TrasladoRegimen(
            rubro=f.par_id,
            regimen=f.regimen,
            largo_plazo=r(f.largo_plazo, 3),
            intervalo=(r(f.ic_inf, 3), r(f.ic_sup, 3)),
            significativo=bool(f.p_valor < 0.05),
            n=int(f.n),
        )
        for f in t.itertuples()
    ]


def armar_cadena() -> list[Cadena]:
    t = pd.read_csv(RESULTADOS / "cadena.csv").sort_values(["par_id", "origen", "mes"])
    return [
        Cadena(
            rubro=rubro,
            origen=origen,
            respuesta=[r(v, 3) for v in g.respuesta],
            inferior=[r(v, 3) for v in g.ic_inf],
            superior=[r(v, 3) for v in g.ic_sup],
        )
        for (rubro, origen), g in t.groupby(["par_id", "origen"])
    ]


def armar_metricas(bt: pd.DataFrame) -> tuple[list[Metricas], list[ErrorAnual]]:
    metricas, anual = [], []
    for grupo, d in [("rubros", bt[bt.par_id != NG]), ("nivel_general", bt[bt.par_id == NG])]:
        if d.empty:
            continue

        def mae(x, col):
            return r(100 * (x.y - x[col]).abs().mean())

        metricas.append(
            Metricas(
                grupo=grupo,
                meses=d.fecha.nunique(),
                series=d.groupby(["par_id", "region"]).ngroups,
                naive=mae(d, "naive"),
                arx=mae(d, "arx"),
                lgbm=mae(d, "lgbm"),
                combinado=mae(d, "combinado"),
                p_valor=r(pronostico.diebold_mariano(d, "combinado", "naive")["p_valor"], 4),
                cobertura80=r(d.y.between(d.lgbm_inf, d.lgbm_sup).mean(), 3),
                cobertura90=r(d.y.between(d.lgbm_inf_90, d.lgbm_sup_90).mean(), 3),
            )
        )
        for anio, x in d.groupby(d.fecha.dt.year):
            anual.append(
                ErrorAnual(
                    grupo=grupo,
                    anio=int(anio),
                    naive=mae(x, "naive"),
                    combinado=mae(x, "combinado"),
                    meses=x.fecha.nunique(),
                )
            )
    return metricas, anual


def armar_registro(gondola) -> list[Registrado]:
    ruta = mensual.REGISTRO
    if not ruta.exists():
        return []
    reg = pd.read_csv(ruta)
    reg["fecha"] = pd.to_datetime(reg["fecha"], format="ISO8601")
    salida = []
    for f in reg.itertuples():
        serie = gondola.get(f.region, pd.DataFrame()).get(f.par_id)
        real = serie.get(f.fecha) if serie is not None else None
        tiene_90 = "inf_90" in reg and pd.notna(getattr(f, "inf_90", None))
        salida.append(
            Registrado(
                mes=mes(f.fecha),
                region=f.region,
                rubro=f.par_id,
                pronostico=r(f.pronostico),
                banda80=(r(f.inf), r(f.sup)),
                banda90=(r(f.inf_90), r(f.sup_90)) if tiene_90 else None,
                real=None if real is None or pd.isna(real) else float(pct(real)),
                generado=f.generado_utc,
                modelo=f.modelo,
            )
        )
    return salida


def dias_de_publicacion(pub: pd.DataFrame, dataset: str) -> tuple[int, int]:
    # el rango de dias de los ultimos dos anios: el indec publica un calendario pero no hay API
    d = pub[pub.dataset == dataset].sort_values("fecha").tail(24)
    dias = pd.to_datetime(d.publicado).dt.day
    return int(dias.min()), int(dias.max())


def proximo_ipc(pub: pd.DataFrame, ultimo: pd.Timestamp) -> ProximoDato:
    siguiente = ultimo + pd.DateOffset(months=1)
    desde, hasta = dias_de_publicacion(pub, "ipc")
    return ProximoDato(
        mes=mes(siguiente),
        publicacion=mes(siguiente + pd.DateOffset(months=1)),
        dia_desde=desde,
        dia_hasta=hasta,
    )


def proximo_pronostico(
    pub: pd.DataFrame, ultimo: pd.Timestamp, pronosticado: pd.Timestamp
) -> ProximoDato:
    """El proximo mes a pronosticar y cuando: el mismo mes, al salir el mayorista del anterior."""
    objetivo = max(pronosticado, ultimo) + pd.DateOffset(months=1)
    desde, hasta = dias_de_publicacion(pub, "mayorista")
    return ProximoDato(
        mes=mes(objetivo), publicacion=mes(objetivo), dia_desde=desde, dia_hasta=hasta
    )


def armar_revisiones(con, pub: pd.DataFrame) -> Revisiones:
    n, corregidos, informes, desde, hasta = con.execute(
        "select count(*), coalesce(sum((abs(revision) > 1e-9)::int), 0), "
        "count(distinct archivo), min(fecha), max(fecha) from fct_primer_dato"
    ).fetchone()
    return Revisiones(
        comparados=n,
        corregidos=corregidos,
        informes=informes,
        desde=mes(desde),
        hasta=mes(hasta),
    )


def armar_series(gondola, mayorista, rubros: list[Rubro]) -> Series:
    meses = gondola["GBA"].index[gondola["GBA"][NG].notna()]
    movil = pd.read_csv(RESULTADOS / "traslado_movil.csv", index_col="fecha", parse_dates=True)
    salida = []
    for rubro in rubros:
        m = rubro.id
        salida.append(
            SerieRubro(
                rubro=m,
                mayorista=lista(pct(mayorista[m].reindex(meses))) if m in mayorista else [],
                gondola={
                    reg: lista(pct(gondola[reg][m].reindex(meses)))
                    for reg in a.REGIONES
                    if m in gondola[reg]
                },
                traslado_movil=lista(movil[m].reindex(meses).round(3)) if m in movil else None,
            )
        )
    return Series(meses=[mes(f) for f in meses], rubros=salida)


def armar_backtest(bt: pd.DataFrame) -> Backtest:
    meses = sorted(bt.fecha.unique())
    series = []
    for (region, rubro), d in bt.groupby(["region", "par_id"], sort=False):
        d = d.set_index("fecha").reindex(meses)
        series.append(
            Acierto(
                region=region,
                rubro=rubro,
                **{
                    destino: lista(pct(d[origen]))
                    for destino, origen in [
                        ("real", "y"),
                        ("pronostico", "combinado"),
                        ("naive", "naive"),
                        ("inf80", "lgbm_inf"),
                        ("sup80", "lgbm_sup"),
                        ("inf90", "lgbm_inf_90"),
                        ("sup90", "lgbm_sup_90"),
                    ]
                },
            )
        )
    return Backtest(meses=[mes(f) for f in meses], series=series)


def armar(con) -> dict[str, Modelo]:
    gondola, mayorista = gondola_y_mayorista(con)
    rubros = armar_rubros(con)
    pub = con.execute("select * from fct_publicaciones").df()
    manifest = pd.read_csv(mensual.MANIFEST)
    prox = pd.read_csv(RESULTADOS / "pronostico_proximo.csv", parse_dates=["fecha"])
    bt = pd.read_csv(RESULTADOS / "pronostico_backtest.csv", parse_dates=["fecha"])
    ultimo = gondola["GBA"][NG].dropna().index.max()
    registro = armar_registro(gondola)
    metricas, anual = armar_metricas(bt)

    meta = Meta(
        ultimo_mes=mes(ultimo),
        mes_pronosticado=mes(prox.fecha.max()),
        proximo_ipc=proximo_ipc(pub, ultimo),
        # cuando sale el ipc del mes pronosticado y todavia no el mayorista, el pronostico que
        # hay ya es viejo: la web lo muestra como resultado y no como lo que viene
        pronostico_vigente=bool(prox.fecha.max() > ultimo),
        proximo_pronostico=proximo_pronostico(pub, ultimo, prox.fecha.max()),
        # sin la hora de la corrida: si no, el json cambiaria todos los dias sin datos nuevos
        datos_nuevos=pd.to_datetime(manifest.fecha_utc).max().to_pydatetime(),
        version_modelo=pronostico.version_modelo(),
        version_datos=mensual.version_datos(),
        repo=REPO,
        fuentes=FUENTES,
    )
    resumen = Resumen(
        meta=meta,
        regiones=armar_regiones(con),
        rubros=rubros,
        ultimo_dato=[
            Dato(region=reg, rubro=m, valor=float(pct(gondola[reg].loc[ultimo, m])))
            for reg in a.REGIONES
            for m in gondola[reg].columns
            if pd.notna(gondola[reg].loc[ultimo, m])
        ],
        pronosticos=armar_pronosticos(prox, gondola),
        traslado=armar_traslado(),
        traslado_regimen=armar_regimen(),
        cadena=armar_cadena(),
        metricas=metricas,
        error_anual=anual,
        revisiones=armar_revisiones(con, pub),
        automatizacion=Automatizacion(
            primer_mes=mes(gondola["GBA"][NG].dropna().index.min()),
            meses_ipc=int(gondola["GBA"][NG].notna().sum()),
            descargas=len(manifest),
            meses_registrados=len({x.mes for x in registro}),
            primer_registro=min((x.mes for x in registro), default=None),
        ),
    )
    return {
        "resumen": resumen,
        "series": armar_series(gondola, mayorista, rubros),
        "backtest": armar_backtest(bt),
        "historial": Historial(
            registro=registro,
            publicaciones=[
                Publicacion(dataset=f.dataset, mes=mes(f.fecha), publicado=f.publicado)
                for f in pub.sort_values(["dataset", "fecha"]).itertuples()
            ],
        ),
    }


def esquema() -> dict:
    """JSON Schema de los tres archivos, para generar los tipos de la web."""
    from pydantic.json_schema import models_json_schema

    _, defs = models_json_schema(
        [(m, "serialization") for m in ARCHIVOS.values()], by_alias=True, title="Monitor"
    )
    return defs


def guardar(archivos: dict[str, Modelo], carpeta: Path = SALIDA) -> dict[str, int]:
    carpeta.mkdir(parents=True, exist_ok=True)
    tamanios = {}
    for nombre, modelo in archivos.items():
        texto = modelo.model_dump_json(by_alias=True)
        (carpeta / f"{nombre}.json").write_text(texto, encoding="utf-8")
        tamanios[nombre] = len(texto.encode())
    (carpeta / "esquema.json").write_text(
        json.dumps(esquema(), indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return tamanios


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    tamanios = guardar(armar(a.conectar()))
    for nombre, n in tamanios.items():
        log.info("%s.json: %.0f KB", nombre, n / 1024)


if __name__ == "__main__":
    main()
