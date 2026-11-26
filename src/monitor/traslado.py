"""Modelo de traslado: cuanto de una suba mayorista llega a la gondola y en cuanto tiempo.

Todo en variaciones log relativas: a cada serie le resto su inflacion general, porque si no
el modelo mide la inflacion y no el traslado (ver notebooks/01_eda.ipynb).
"""

import itertools
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.api import VAR

from monitor import analisis as a
from monitor.config import RAIZ

log = logging.getLogger(__name__)

MAX_K = 3  # rezagos del mayorista
MAX_P = 2  # rezagos de la gondola
ESTACIONALES = {"verduras", "frutas", "prendas", "energia"}
REGIMENES = {
    "baja": [("2017-01-01", "2017-12-01"), ("2025-01-01", "2099-12-01")],
    "media": [("2018-01-01", "2021-12-01")],
    "alta": [("2022-01-01", "2024-12-01")],
}
CADENA = ["carnes", "lacteos", "pan_cereales"]


def regimen(fechas: pd.DatetimeIndex) -> pd.Series:
    etiqueta = pd.Series(pd.NA, index=fechas, dtype="object")
    for nombre, tramos in REGIMENES.items():
        for desde, hasta in tramos:
            etiqueta[(fechas >= desde) & (fechas <= hasta)] = nombre
    return etiqueta


def armar_datos(y: pd.Series, x: pd.Series, estacional: bool = False) -> pd.DataFrame:
    """y, x y todos sus rezagos. Se arma una sola vez con el maximo de rezagos para que
    todas las combinaciones se comparen sobre la misma muestra."""
    d = pd.DataFrame({"y": y, "x0": x})
    for k in range(1, MAX_K + 1):
        d[f"x{k}"] = x.shift(k)
    for j in range(1, MAX_P + 1):
        d[f"y{j}"] = y.shift(j)
    if estacional:
        meses = pd.get_dummies(d.index.month, prefix="mes", drop_first=True, dtype=float)
        d = d.join(meses.set_index(d.index))
    return d.dropna()


def ajustar(datos: pd.DataFrame, k: int, p: int):
    columnas = [f"x{i}" for i in range(k + 1)] + [f"y{j}" for j in range(1, p + 1)]
    columnas += [c for c in datos.columns if c.startswith("mes_")]
    # newey-west: los residuos de series mensuales suelen estar autocorrelacionados
    hac = int(4 * (len(datos) / 100) ** (2 / 9))
    modelo = sm.OLS(datos["y"], sm.add_constant(datos[columnas]))
    return modelo.fit(cov_type="HAC", cov_kwds={"maxlags": hac})


def elegir_rezagos(datos: pd.DataFrame) -> tuple[int, int]:
    combos = itertools.product(range(MAX_K + 1), range(MAX_P + 1))
    return min(combos, key=lambda kp: ajustar(datos, *kp).bic)


def largo_plazo(res, k: int, p: int) -> tuple[float, float]:
    """Traslado de largo plazo sum(b) / (1 - sum(f)) y su error con el metodo delta."""
    xs = [f"x{i}" for i in range(k + 1)]
    ys = [f"y{j}" for j in range(1, p + 1)]
    b = res.params[xs].sum()
    f = res.params[ys].sum() if ys else 0.0
    if 1 - f < 0.1:  # casi raiz unitaria, el cociente no tiene sentido
        return np.nan, np.nan
    grad = pd.Series(0.0, index=res.params.index)
    grad[xs] = 1 / (1 - f)
    grad[ys] = b / (1 - f) ** 2
    var = grad @ res.cov_params() @ grad
    return b / (1 - f), float(np.sqrt(var))


def resumir(res, k: int, p: int) -> dict:
    lp, ee = largo_plazo(res, k, p)
    z = lp / ee if ee and ee > 0 else np.nan
    return {
        "rezagos_x": k,
        "rezagos_y": p,
        "impacto": res.params["x0"],
        "acumulado": res.params[[f"x{i}" for i in range(k + 1)]].sum(),
        "largo_plazo": lp,
        "ee_largo_plazo": ee,
        "ic_inf": lp - 1.96 * ee,
        "ic_sup": lp + 1.96 * ee,
        "p_valor": 2 * (1 - stats.norm.cdf(abs(z))) if not np.isnan(z) else np.nan,
        "r2": res.rsquared,
        "n": int(res.nobs),
        # si queda autocorrelacion en los residuos faltan rezagos
        "p_ljungbox": acorr_ljungbox(res.resid, lags=[6])["lb_pvalue"].iloc[0],
    }


def estimar(y: pd.Series, x: pd.Series, estacional: bool = False) -> dict:
    datos = armar_datos(y, x, estacional)
    k, p = elegir_rezagos(datos)
    return resumir(ajustar(datos, k, p), k, p)


def estimar_por_regimen(y: pd.Series, x: pd.Series, estacional: bool = False) -> list[dict]:
    # los rezagos se eligen con toda la muestra y se mantienen, asi los regimenes se comparan
    datos = armar_datos(y, x, estacional)
    k, p = elegir_rezagos(datos)
    etiquetas = regimen(datos.index)
    filas = []
    for nombre in REGIMENES:
        sub = datos[etiquetas == nombre]
        if estacional:
            # con 2 o 3 anios no alcanzan los datos para 11 dummies
            sub = sub.drop(columns=[c for c in sub.columns if c.startswith("mes_")])
        if len(sub) < 18:
            continue
        filas.append({"regimen": nombre} | resumir(ajustar(sub, k, p), k, p))
    return filas


def traslado_movil(y: pd.Series, x: pd.Series, ventana: int = 36, k: int = 1) -> pd.Series:
    """Traslado acumulado (k rezagos, sin rezagos de y) en ventanas moviles."""
    datos = armar_datos(y, x)
    valores = {}
    for fin in range(ventana, len(datos) + 1):
        sub = datos.iloc[fin - ventana : fin]
        valores[sub.index[-1]] = ajustar(sub, k, 0).params[[f"x{i}" for i in range(k + 1)]].sum()
    return pd.Series(valores, name="traslado")


def corregir_fdr(p_valores: pd.Series, alfa: float = 0.05) -> pd.Series:
    """Benjamini-Hochberg: con 100 tests, al 5% saldrian unos 5 'hallazgos' por azar."""
    ok = p_valores.notna()
    signif = pd.Series(False, index=p_valores.index)
    if ok.any():
        signif[ok] = multipletests(p_valores[ok], alpha=alfa, method="fdr_bh")[0]
    return signif


def cadena(primaria: pd.Series, industria: pd.Series, gondola: pd.Series, horizonte: int = 6):
    """VAR con el orden productor -> industria -> gondola. Devuelve la respuesta acumulada de
    la gondola a una suba de 1 en cada etapa anterior, con intervalo del 95%."""
    datos = pd.concat(
        [primaria, industria, gondola], axis=1, keys=["primaria", "industria", "gondola"]
    )
    datos = datos.dropna().asfreq("MS")
    res = VAR(datos).fit(maxlags=4, ic="bic")
    if res.k_ar == 0:
        # bic a veces elige 0 rezagos y sin rezagos no hay respuesta en el tiempo
        res = VAR(datos).fit(1)
    irf = res.irf(horizonte)
    # paso el shock de "1 desvio" a "1 punto" dividiendo por el impacto propio
    escala = np.diag(irf.orth_irfs[0])
    inf, sup = irf.cum_errband_mc(orth=True, repl=500, rng=np.random.default_rng(0), signif=0.05)
    filas = []
    for i, origen in enumerate(["primaria", "industria"]):
        acum = irf.orth_cum_effects[:, 2, i] / escala[i]
        for h in range(horizonte + 1):
            filas.append(
                {
                    "origen": origen,
                    "mes": h,
                    "respuesta": acum[h],
                    "ic_inf": inf[h, 2, i] / escala[i],
                    "ic_sup": sup[h, 2, i] / escala[i],
                }
            )
    return pd.DataFrame(filas), res


def datos_modelo(con, indicador: str = "IPIM"):
    """Gondola por region, industria y primaria, todo relativo a su inflacion general."""
    precios = con.execute(
        "select * from fct_precios where indicador in ('IPC', ?) order by fecha", [indicador]
    ).df()
    general = a.inflacion_general(con)
    gondola = {
        r: a.relativa(a.serie_por_rubro(precios, "gondola", r), general[r]) for r in a.REGIONES
    }
    industria = a.relativa(a.serie_por_rubro(precios, "industria"), general["mayorista"])
    primaria = a.relativa(a.serie_por_rubro(precios, "primaria"), general["mayorista"])
    return gondola, {"industria": industria, "primaria": primaria}


def estimar_todo(con, indicador: str = "IPIM") -> pd.DataFrame:
    gondola, mayorista = datos_modelo(con, indicador)
    filas = []
    for region, g in gondola.items():
        for etapa, m in mayorista.items():
            for rubro in g.columns.intersection(m.columns):
                fila = estimar(g[rubro], m[rubro], rubro in ESTACIONALES)
                filas.append({"par_id": rubro, "region": region, "etapa": etapa} | fila)
    tabla = pd.DataFrame(filas)
    tabla["indicador"] = indicador
    tabla["significativo_fdr"] = corregir_fdr(tabla["p_valor"])
    return tabla


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    salida = RAIZ / "data" / "resultados"
    salida.mkdir(parents=True, exist_ok=True)
    con = a.conectar()

    tabla = estimar_todo(con)
    tabla.to_csv(salida / "traslado.csv", index=False)
    log.info(
        "traslado: %d estimaciones, %d significativas", len(tabla), tabla.significativo_fdr.sum()
    )

    gondola, mayorista = datos_modelo(con)
    g = gondola["GBA"]
    regimenes = [
        {"par_id": r} | fila
        for r in g.columns.intersection(mayorista["industria"].columns)
        for fila in estimar_por_regimen(g[r], mayorista["industria"][r], r in ESTACIONALES)
    ]
    pd.DataFrame(regimenes).to_csv(salida / "traslado_regimen.csv", index=False)

    moviles = {
        r: traslado_movil(g[r], mayorista["industria"][r])
        for r in g.columns.intersection(mayorista["industria"].columns)
    }
    pd.DataFrame(moviles).rename_axis("fecha").to_csv(salida / "traslado_movil.csv")

    irfs = []
    for rubro in CADENA:
        resp, _ = cadena(mayorista["primaria"][rubro], mayorista["industria"][rubro], g[rubro])
        irfs.append(resp.assign(par_id=rubro))
    pd.concat(irfs).to_csv(salida / "cadena.csv", index=False)
    log.info("listo, resultados en %s", Path(salida).relative_to(RAIZ))


if __name__ == "__main__":
    main()
