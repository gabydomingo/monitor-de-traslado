"""Pronostico de la inflacion del mes que viene por rubro y region.

Cada fila es un mes objetivo T. El pronostico se hace cuando sale el mayorista de T-1 (desde
2018 entre el 14 y el 23 de T). Para ese momento se conoce: el ipc y el mayorista de T-1, el rem
de fines de T-1 y el dolar del 1 al 13 de T. Nada mas.
"""

import hashlib
import json
import logging
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats

from monitor import analisis as a
from monitor.config import RAIZ

log = logging.getLogger(__name__)

FEATURES = [
    "par_id",
    "region",
    "mes",
    "y_l1",
    "y_l2",
    "y_l3",
    "y_l12",
    "y_m12",
    "may_l1",
    "may_l2",
    "gen_l1",
    "gen_m12",
    "genmay_l1",
]
# del bcra: dolar del mes anterior, dolar del 1 al 13 del mes y rem
FEATURES_BCRA = ["tc_l1", "tc_inicio_mes", "rem_l1"]
FEATURES = [*FEATURES, *FEATURES_BCRA]
CATEGORICAS = ["par_id", "region"]
ARBOLES = 300
PARAMS = {
    "objective": "regression",
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_data_in_leaf": 30,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "feature_fraction": 0.8,
    "seed": 0,
    "deterministic": True,
    "verbose": -1,
}


def features_bcra(bcra: pd.DataFrame | None, fechas: pd.DatetimeIndex) -> pd.DataFrame:
    """bcra: fct_bcra_mensual con la fecha de indice. Sin datos del bcra quedan vacios."""
    if bcra is None:
        return pd.DataFrame(np.nan, index=fechas, columns=FEATURES_BCRA)
    b = bcra.reindex(bcra.index.union(fechas))
    tc = np.log(b["tc_promedio"])
    out = pd.DataFrame(
        {
            "tc_l1": tc.diff().shift(1),
            # lo que se movio el dolar del 1 al 13 contra el promedio del mes anterior
            "tc_inicio_mes": np.log(b["tc_inicio_mes"]) - tc.shift(1),
            # el rem es inflacion esperada a 12 meses, la paso a mensual
            "rem_l1": np.log1p(b["rem_12m"].shift(1) / 100) / 12,
        }
    )
    return out.reindex(fechas)


def armar_panel(
    gondola: dict,
    mayorista: pd.DataFrame,
    general: pd.DataFrame,
    bcra: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """gondola: {region: df fecha x rubro} con var log nominal. mayorista: fecha x rubro.
    general: fecha x region, mas la columna 'mayorista'. bcra: fct_bcra_mensual por fecha.
    Agrega una fila para el mes que viene con y vacio, que es la que despues se pronostica."""
    ultimo = max(g.index.max() for g in gondola.values())
    fechas = pd.date_range(
        min(g.index.min() for g in gondola.values()), ultimo + pd.offsets.MonthBegin(1), freq="MS"
    )
    general = general.reindex(fechas)
    mayorista = mayorista.reindex(fechas)
    externos = features_bcra(bcra, fechas)
    partes = []
    for region, g in gondola.items():
        g = g.reindex(fechas)
        gen = general[region]
        for rubro in g.columns:
            y = g[rubro]
            may = mayorista[rubro] if rubro in mayorista else pd.Series(np.nan, index=fechas)
            partes.append(
                pd.DataFrame(
                    {
                        "par_id": rubro,
                        "region": region,
                        "fecha": fechas,
                        "mes": fechas.month,
                        "y": y.to_numpy(),
                        "y_l1": y.shift(1).to_numpy(),
                        "y_l2": y.shift(2).to_numpy(),
                        "y_l3": y.shift(3).to_numpy(),
                        "y_l12": y.shift(12).to_numpy(),
                        "y_m12": y.shift(1).rolling(12, min_periods=6).mean().to_numpy(),
                        "may_l1": may.shift(1).to_numpy(),
                        "may_l2": may.shift(2).to_numpy(),
                        "gen_l1": gen.shift(1).to_numpy(),
                        "gen_m12": gen.shift(1).rolling(12, min_periods=6).mean().to_numpy(),
                        "genmay_l1": general["mayorista"].shift(1).to_numpy(),
                        **{c: externos[c].to_numpy() for c in externos},
                    }
                )
            )
    panel = pd.concat(partes, ignore_index=True)
    for c in CATEGORICAS:
        panel[c] = panel[c].astype("category")
    # sin al menos un mes previo no hay nada que pronosticar
    return panel[panel["y_l1"].notna() | (panel["fecha"] == fechas[-1])].reset_index(drop=True)


# modelos. todos reciben train y test y devuelven la prediccion para test


def naive(train, test):
    return test["y_l1"].to_numpy()


def media3(train, test):
    return test[["y_l1", "y_l2", "y_l3"]].mean(axis=1).to_numpy()


def estacional(train, test):
    # mismo mes del anio anterior; si no hay, el ultimo dato
    return test["y_l12"].fillna(test["y_l1"]).to_numpy()


def arx(train, test):
    """Una regresion lineal por serie: inercia, mayorista, inflacion general y dolar."""
    cols = ["y_l1", "may_l1", "may_l2", "gen_l1", "tc_l1", "tc_inicio_mes"]
    pred = test["y_l1"].to_numpy(dtype=float).copy()
    # todo en numpy: con pandas se iba casi todo el tiempo en indexar, no en las cuentas
    X_tr, y_tr = train[cols].to_numpy(dtype=float), train["y"].to_numpy(dtype=float)
    X_te = test[cols].to_numpy(dtype=float)
    series = train.groupby(["par_id", "region"], observed=True).indices
    for clave, pos_te in test.groupby(["par_id", "region"], observed=True).indices.items():
        pos_tr = series.get(clave)
        if pos_tr is None or len(pos_tr) < 24:
            continue
        usar = ~np.isnan(X_tr[pos_tr]).any(axis=0) & ~np.isnan(X_te[pos_te]).any(axis=0)
        X = np.c_[np.ones(len(pos_tr)), X_tr[np.ix_(pos_tr, usar)]]
        coef = np.linalg.lstsq(X, y_tr[pos_tr], rcond=None)[0]
        pred[pos_te] = np.c_[np.ones(len(pos_te)), X_te[np.ix_(pos_te, usar)]] @ coef
    return pred


def entrenar(train, alpha=None) -> lgb.Booster:
    params = PARAMS | ({"objective": "quantile", "alpha": alpha} if alpha else {})
    tr = train.dropna(subset=["y"])
    datos = lgb.Dataset(tr[FEATURES], tr["y"], categorical_feature=CATEGORICAS)
    return lgb.train(params, datos, num_boost_round=ARBOLES)


def lgbm(train, test, alpha=None):
    return entrenar(train, alpha).predict(test[FEATURES])


MODELOS = {"naive": naive, "media3": media3, "estacional": estacional, "arx": arx, "lgbm": lgbm}


def combinar(lgbm_pred, arx_pred):
    # promedio simple, sin pesos ajustados. los arboles no pueden pronosticar mas alla de lo que
    # vieron (un salto del dolar nunca visto) y la regresion lineal si; al reves, los arboles
    # captan lo no lineal. mitad y mitad para no sobreajustar el peso a la validacion
    return (np.asarray(lgbm_pred) + np.asarray(arx_pred)) / 2


EVALUADOS = [*MODELOS, "combinado"]


def un_mes(con_y: pd.DataFrame, mes, intervalo: bool = True) -> pd.DataFrame:
    train = con_y[con_y["fecha"] < mes]
    test = con_y[con_y["fecha"] == mes].reset_index(drop=True)
    out = test[["par_id", "region", "fecha", "y"]].copy()
    for nombre, f in MODELOS.items():
        out[nombre] = f(train, test)
    if {"lgbm", "arx"} <= set(out):
        out["combinado"] = combinar(out["lgbm"], out["arx"])
    if intervalo:
        out["lgbm_q10"] = lgbm(train, test, 0.1)
        out["lgbm_q90"] = lgbm(train, test, 0.9)
        if "combinado" in out:
            out[["lgbm_q10", "lgbm_q90"]] = centrar(out, out["combinado"])
    return out


def centrar(df: pd.DataFrame, punto) -> np.ndarray:
    """Los cuantiles salen de lightgbm pero el numero que se publica es el combinado: corro el
    intervalo para que quede alrededor de ese numero. Despues conformal ajusta el ancho."""
    corrimiento = np.asarray(punto) - df["lgbm"].to_numpy()
    return np.c_[df["lgbm_q10"] + corrimiento, df["lgbm_q90"] + corrimiento]


def _un_hilo():
    # con varios procesos a la vez conviene que cada lightgbm use un solo hilo
    PARAMS["num_threads"] = 1


def backtest(
    panel: pd.DataFrame, meses: int = 36, intervalo: bool = True, procesos: int = 1
) -> pd.DataFrame:
    """Origen movil: para cada mes de prueba se entrena solo con lo anterior y se predice ese
    mes. Nunca se mezcla el orden. Cada mes es independiente, asi que se pueden repartir
    entre procesos."""
    con_y = panel[panel["y"].notna()]
    prueba = sorted(con_y["fecha"].unique())[-meses:]
    if procesos > 1:
        # spawn y no fork: lightgbm usa openmp y con fork los procesos se traban
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(procesos, mp_context=ctx, initializer=_un_hilo) as ex:
            salidas = list(ex.map(un_mes, repeat(con_y), prueba, repeat(intervalo)))
    else:
        salidas = [un_mes(con_y, mes, intervalo) for mes in prueba]
    return pd.concat(salidas, ignore_index=True)


def puntajes(pred: pd.DataFrame) -> pd.Series:
    # cuanto le falto al intervalo para contener el dato (negativo si lo contenia)
    return np.maximum(pred["lgbm_q10"] - pred["y"], pred["y"] - pred["lgbm_q90"])


def ajuste_conformal(puntajes_previos: pd.Series, alfa: float = 0.2) -> float:
    n = len(puntajes_previos)
    return float(np.quantile(puntajes_previos, min(1.0, (1 - alfa) * (n + 1) / n)))


def ajustes(previos: pd.DataFrame, alfa: float = 0.2, grupo: str = "par_id") -> pd.Series:
    """Ensanche conformal por rubro. Uno solo para todos dejaba verduras cubriendo 67% y
    pan 88%: el promedio daba bien pero cada rubro por separado no."""
    s = puntajes(previos)
    return s.groupby(previos[grupo].astype(str)).apply(lambda x: ajuste_conformal(x, alfa))


def aplicar_ajuste(df: pd.DataFrame, aj: pd.Series, grupo: str = "par_id") -> np.ndarray:
    # un rubro sin historia (no deberia pasar) se lleva el ensanche mas grande
    return df[grupo].astype(str).map(aj).fillna(aj.max()).to_numpy(dtype=float)


def calibrar(pred: pd.DataFrame, ventana: int = 12, minimo: int = 6, alfa: float = 0.2):
    """Para cada mes ensancho el intervalo segun cuanto se quedo corto cada rubro en los
    `ventana` meses anteriores. Solo usa el pasado."""
    pred = pred.copy()
    pred["ajuste"] = np.nan
    meses = sorted(pred["fecha"].unique())
    for i, mes in enumerate(meses):
        anteriores = meses[max(0, i - ventana) : i]
        if len(anteriores) < minimo:
            continue
        ahora = pred["fecha"] == mes
        aj = ajustes(pred[pred["fecha"].isin(anteriores)], alfa)
        pred.loc[ahora, "ajuste"] = aplicar_ajuste(pred[ahora], aj)
    pred["lgbm_inf"] = pred["lgbm_q10"] - pred["ajuste"]
    pred["lgbm_sup"] = pred["lgbm_q90"] + pred["ajuste"]
    return pred


def escala_mase(panel: pd.DataFrame, hasta) -> pd.Series:
    """Error medio del naive en la historia previa a la prueba, por serie (para el MASE)."""
    h = panel[(panel["fecha"] < hasta) & panel["y"].notna()]
    err = (h["y"] - h["y_l1"]).abs()
    return err.groupby([h["par_id"], h["region"]], observed=True).mean()


def metricas(pred: pd.DataFrame, escala: pd.Series) -> pd.DataFrame:
    filas = []
    esc = pred.set_index(["par_id", "region"]).index.map(escala).to_numpy(dtype=float)
    for nombre in EVALUADOS:
        e = pred["y"] - pred[nombre]
        filas.append(
            {
                "modelo": nombre,
                "mae_pp": 100 * e.abs().mean(),
                "rmse_pp": 100 * np.sqrt((e**2).mean()),
                "mase": np.nanmean(e.abs() / esc),
            }
        )
    tabla = pd.DataFrame(filas).set_index("modelo")
    tabla["vs_naive"] = tabla["mae_pp"] / tabla.loc["naive", "mae_pp"]  # < 1 es mejor
    if "lgbm_q10" in pred:
        tabla.loc["combinado", "cobertura_80_cruda"] = (
            pred["y"].between(pred["lgbm_q10"], pred["lgbm_q90"]).mean()
        )
    if "lgbm_inf" in pred:
        tabla.loc["combinado", "cobertura_80_calibrada"] = (
            pred["y"].between(pred["lgbm_inf"], pred["lgbm_sup"]).mean()
        )
    return tabla


def diebold_mariano(pred: pd.DataFrame, a: str, b: str) -> dict:
    """a mejor que b? Promedio por mes del error absoluto (para no tratar como independientes
    las series de un mismo mes) y test con la correccion de Harvey-Leybourne-Newbold."""
    d = ((pred["y"] - pred[a]).abs() - (pred["y"] - pred[b]).abs()).groupby(pred["fecha"]).mean()
    n = len(d)
    stat = d.mean() / np.sqrt(d.var(ddof=1) / n)
    stat *= np.sqrt((n - 1) / n)  # hln con horizonte 1
    p = 2 * stats.t.sf(abs(stat), df=n - 1)
    return {"a": a, "b": b, "dif_mae_pp": 100 * d.mean(), "estadistico": stat, "p_valor": p}


def importancia(panel: pd.DataFrame) -> pd.Series:
    """Promedio del valor absoluto de las contribuciones shap (las calcula lightgbm)."""
    tr = panel.dropna(subset=["y"])
    contrib = entrenar(tr).predict(tr[FEATURES], pred_contrib=True)[:, :-1]
    return pd.Series(np.abs(contrib).mean(axis=0) * 100, index=FEATURES).sort_values()


def pronosticar_proximo(panel: pd.DataFrame, aj: pd.Series) -> pd.DataFrame:
    """aj: el ensanche conformal por rubro que sale de los ultimos meses del backtest."""
    ultimo = panel["fecha"].max()
    train, test = panel[panel["y"].notna()], panel[panel["fecha"] == ultimo].reset_index(drop=True)
    out = test[["par_id", "region", "fecha"]].copy()
    q = pd.DataFrame(
        {
            "lgbm": lgbm(train, test),
            "lgbm_q10": lgbm(train, test, 0.1),
            "lgbm_q90": lgbm(train, test, 0.9),
        }
    )
    out["pronostico"] = combinar(q["lgbm"], arx(train, test))
    q10, q90 = centrar(q, out["pronostico"]).T
    ensanche = aplicar_ajuste(test, aj)
    out["inf"] = q10 - ensanche
    out["sup"] = q90 + ensanche
    # son modelos separados: me aseguro de que el pronostico quede dentro de su intervalo
    out["inf"] = np.minimum(out["inf"], out["pronostico"])
    out["sup"] = np.maximum(out["sup"], out["pronostico"])
    for c in ["pronostico", "inf", "sup"]:
        out[c] = 100 * np.expm1(out[c])  # en % mensual
    return out


def datos(con) -> pd.DataFrame:
    precios = a.cargar_precios(con)
    general = a.inflacion_general(con)
    gondola = {r: a.serie_por_rubro(precios, "gondola", r) for r in a.REGIONES}
    # frutas y verduras no tienen industria, uso el productor
    industria = a.serie_por_rubro(precios, "industria")
    primaria = a.serie_por_rubro(precios, "primaria")
    mayorista = industria.combine_first(primaria[primaria.columns.difference(industria.columns)])
    bcra = con.execute("select * from fct_bcra_mensual").df()
    bcra = bcra.assign(fecha=pd.to_datetime(bcra["fecha"])).set_index("fecha")
    return armar_panel(gondola, mayorista, general, bcra)


def version_modelo() -> str:
    # cambia si cambian las variables o los parametros: sirve para saber con que modelo
    # se hizo cada pronostico del registro
    texto = json.dumps({"features": FEATURES, "params": PARAMS, "arboles": ARBOLES}, sort_keys=True)
    return hashlib.sha256(texto.encode()).hexdigest()[:8]


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    salida = RAIZ / "data" / "resultados"
    salida.mkdir(parents=True, exist_ok=True)
    panel = datos(a.conectar())
    # 48 meses de backtest: los primeros 12 solo sirven para calibrar los intervalos
    pred = calibrar(backtest(panel, meses=48, procesos=os.cpu_count() or 1))
    pred = pred[pred["ajuste"].notna()]
    pred = pred[pred["fecha"] >= sorted(pred["fecha"].unique())[-36]]
    pred.to_csv(salida / "pronostico_backtest.csv", index=False)
    tabla = metricas(pred, escala_mase(panel, pred["fecha"].min()))
    tabla.to_csv(salida / "pronostico_metricas.csv")
    log.info("metricas del backtest:\n%s", tabla.round(3))
    ultimos = pred[pred["fecha"] >= sorted(pred["fecha"].unique())[-12]]
    prox = pronosticar_proximo(panel, ajustes(ultimos))
    prox.to_csv(salida / "pronostico_proximo.csv", index=False)
    log.info("pronostico para %s guardado", f"{prox['fecha'].iloc[0]:%m-%Y}")
    return tabla, prox


if __name__ == "__main__":
    main()
