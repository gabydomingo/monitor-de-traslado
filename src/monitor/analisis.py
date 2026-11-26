"""Funciones para el analisis exploratorio. Leen del warehouse que arma dbt."""

import warnings

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import adfuller, kpss

from monitor.config import RAIZ

BASE = RAIZ / "dbt" / "monitor.duckdb"
REGIONES = ["GBA", "Pampeana", "Noreste", "Noroeste", "Cuyo", "Patagonia"]


def conectar(ruta=BASE) -> duckdb.DuckDBPyConnection:
    if not ruta.exists():
        raise FileNotFoundError(f"No esta {ruta}. Correr antes `uv run dbt build` en dbt/")
    return duckdb.connect(str(ruta), read_only=True)


def cargar_precios(con) -> pd.DataFrame:
    # ipc en la gondola e ipim en el mayorista. ipib e ipp quedan para chequear robustez
    return con.execute(
        "select * from fct_precios where indicador in ('IPC', 'IPIM') order by fecha"
    ).df()


def nombres_rubros(con) -> dict:
    return dict(con.execute("select par_id, rubro from dim_rubro").fetchall())


def inflacion_general(con) -> pd.DataFrame:
    """var_log del nivel general: una columna por region del ipc y otra para el mayorista."""
    ipc = con.execute(
        "select region, fecha, var_log from int_series_indice "
        "where fuente = 'ipc' and clasificador = 'IPC'"
    ).df()
    may = con.execute(
        "select fecha, var_log from int_series_indice "
        "where fuente = 'mayorista' and indicador = 'IPIM' and codigo = 'NG'"
    ).df()
    general = ipc.pivot(index="fecha", columns="region", values="var_log")
    general["mayorista"] = may.set_index("fecha")["var_log"]
    return general


def serie_por_rubro(precios: pd.DataFrame, etapa: str, region: str | None = None) -> pd.DataFrame:
    """var_log mensual por rubro (columnas). Si una etapa tiene varios codigos, los promedio."""
    d = precios[precios["etapa"] == etapa]
    if region is not None:
        d = d[d["region"] == region]
    return d.groupby(["fecha", "par_id"])["var_log"].mean().unstack()


def relativa(series: pd.DataFrame, general: pd.Series) -> pd.DataFrame:
    # lo que sube cada rubro por encima (o por debajo) de la inflacion general
    return series.sub(general, axis=0)


def correlacion_rezagos(
    gondola: pd.DataFrame, industria: pd.DataFrame, max_rezago: int = 6
) -> pd.DataFrame:
    """Correlacion entre la gondola de hoy y la industria de k meses antes, por rubro."""
    rubros = gondola.columns.intersection(industria.columns)
    filas = {}
    for r in rubros:
        par = pd.concat([gondola[r], industria[r]], axis=1, keys=["g", "i"]).dropna()
        filas[r] = {k: par["g"].corr(par["i"].shift(k)) for k in range(max_rezago + 1)}
    return pd.DataFrame(filas).T.rename_axis("par_id").rename_axis("rezago", axis=1)


def perfil_estacional(series: pd.DataFrame) -> pd.DataFrame:
    """Promedio por mes del ano, en puntos porcentuales. Filas: rubro, columnas: mes."""
    return (series * 100).groupby(series.index.month).mean().T.rename_axis("mes", axis=1)


def estacionariedad(serie: pd.Series) -> dict:
    """ADF (h0: no estacionaria) y KPSS (h0: estacionaria). Conviene mirar los dos juntos."""
    x = serie.dropna()
    with warnings.catch_warnings():
        # kpss avisa cuando el p-valor se sale de su tabla (queda en 0.01 o 0.1)
        warnings.simplefilter("ignore", InterpolationWarning)
        p_adf = adfuller(x, autolag="AIC", result_object=True).pvalue
        p_kpss = kpss(x, regression="c", nlags="auto", result_object=True).pvalue
    return {
        "p_adf": p_adf,
        "p_kpss": p_kpss,
        "estacionaria": bool(p_adf < 0.05 and p_kpss > 0.05),
    }


def resumen_estacionariedad(precios: pd.DataFrame, region: str = "GBA") -> pd.DataFrame:
    d = precios[precios["region"].isin([region, "Total del pais"])]
    filas = []
    for (rubro, etapa, codigo), g in d.groupby(["par_id", "etapa", "codigo"]):
        nivel = np.log(g.set_index("fecha")["indice"].dropna())
        for transf, s in [("log nivel", nivel), ("var log", nivel.diff())]:
            filas.append(
                {"par_id": rubro, "etapa": etapa, "codigo": codigo, "transf": transf}
                | estacionariedad(s)
            )
    return pd.DataFrame(filas)


def multiplicador_regional(precios: pd.DataFrame, desde: str = "2016-12-01") -> pd.DataFrame:
    """Cuantas veces se multiplico el precio de gondola desde `desde`, por rubro y region."""
    g = precios[(precios["etapa"] == "gondola") & (precios["region"].isin(REGIONES))]
    g = g.groupby(["par_id", "region", "fecha"])["indice"].mean()
    inicio = g.xs(pd.Timestamp(desde), level="fecha")
    fin = g.xs(g.index.get_level_values("fecha").max(), level="fecha")
    return (fin / inicio).unstack()[REGIONES]


# graficos


def estilo() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "font.size": 10,
        }
    )


def mapa_calor(
    tabla: pd.DataFrame,
    titulo: str,
    fmt: str = "{:.2f}",
    cmap: str = "RdBu_r",
    centro: float | None = 0.0,
    rotar: int = 0,
    ax=None,
):
    ax = ax or plt.subplots(figsize=(1 + 0.75 * tabla.shape[1], 0.4 * tabla.shape[0] + 1))[1]
    valores = tabla.to_numpy(dtype=float)
    if centro is not None:
        lim = np.nanmax(np.abs(valores - centro))
        im = ax.imshow(valores, cmap=cmap, vmin=centro - lim, vmax=centro + lim, aspect="auto")
    else:
        im = ax.imshow(valores, cmap=cmap, aspect="auto")
    ax.set_xticks(
        range(tabla.shape[1]), tabla.columns, rotation=rotar, ha="right" if rotar else "center"
    )
    ax.set_yticks(range(tabla.shape[0]), tabla.index)
    ax.grid(False)
    for (i, j), v in np.ndenumerate(valores):
        if not np.isnan(v):
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=8)
    ax.set_title(titulo)
    plt.colorbar(im, ax=ax, shrink=0.8)
    return ax


def intervalos(tabla: pd.DataFrame, titulo: str, ax=None):
    """Estimacion con su intervalo del 95%. tabla: indice = etiqueta, columnas largo_plazo,
    ic_inf, ic_sup y significativo_fdr. Los no significativos van en gris."""
    tabla = tabla.sort_values("largo_plazo")
    ax = ax or plt.subplots(figsize=(8, 0.35 * len(tabla) + 1))[1]
    y = np.arange(len(tabla))
    color = np.where(tabla["significativo_fdr"], "tab:blue", "lightgray")
    ax.hlines(y, tabla["ic_inf"], tabla["ic_sup"], color=color, lw=2)
    ax.scatter(tabla["largo_plazo"], y, color=color, zorder=3)
    ax.axvline(0, color="black", lw=0.8)
    ax.axvline(1, color="black", lw=0.8, ls="--")
    ax.set_yticks(y, tabla.index)
    ax.set_title(titulo)
    return ax
