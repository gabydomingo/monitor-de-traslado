import numpy as np
import pandas as pd
import pytest

from monitor.traslado import (
    armar_datos,
    cadena,
    corregir_fdr,
    estimar,
    estimar_por_regimen,
    largo_plazo,
    regimen,
    traslado_movil,
)

N = 400
FECHAS = pd.date_range("1990-01-01", periods=N, freq="MS")


def series(b0=0.5, b1=0.3, phi=0.0, seed=0):
    # y = b0 x + b1 x(-1) + phi y(-1) + ruido. el traslado de largo plazo es (b0+b1)/(1-phi)
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, N)
    y = np.zeros(N)
    for t in range(1, N):
        y[t] = b0 * x[t] + b1 * x[t - 1] + phi * y[t - 1] + rng.normal(0, 0.3)
    return pd.Series(y, index=FECHAS), pd.Series(x, index=FECHAS)


def test_regimen():
    fechas = pd.to_datetime(["2016-12-01", "2017-06-01", "2019-01-01", "2023-12-01", "2026-01-01"])
    assert list(regimen(fechas).fillna("-")) == ["-", "baja", "media", "alta", "baja"]


def test_armar_datos():
    y, x = series()
    d = armar_datos(y, x, estacional=True)
    assert {"y", "x0", "x3", "y2", "mes_2", "mes_12"} <= set(d.columns)
    assert "mes_1" not in d.columns  # enero queda como base
    assert not d.isna().any().any()
    assert len(d) == N - 3


def test_recupera_el_traslado():
    y, x = series(0.5, 0.3)
    r = estimar(y, x)
    assert r["rezagos_x"] == 1
    assert r["acumulado"] == pytest.approx(0.8, abs=0.05)
    assert r["ic_inf"] < 0.8 < r["ic_sup"]
    assert r["p_valor"] < 0.001


def test_largo_plazo_con_inercia():
    y, x = series(0.4, 0.0, phi=0.5, seed=1)
    r = estimar(y, x)
    assert r["rezagos_y"] >= 1
    assert r["impacto"] == pytest.approx(0.4, abs=0.05)
    # el largo plazo es un cociente y amplifica el error de la inercia: pido que el
    # intervalo contenga el valor real, no que la estimacion puntual le pegue
    assert r["ic_inf"] < 0.8 < r["ic_sup"]


def test_sin_relacion_no_es_significativo():
    rng = np.random.default_rng(2)
    y = pd.Series(rng.normal(0, 1, N), index=FECHAS)
    x = pd.Series(rng.normal(0, 1, N), index=FECHAS)
    assert estimar(y, x)["p_valor"] > 0.01


def test_largo_plazo_casi_raiz_unitaria():
    class Falso:
        params = pd.Series({"const": 0.0, "x0": 0.5, "y1": 0.95})

        def cov_params(self):
            return pd.DataFrame(np.eye(3), index=self.params.index, columns=self.params.index)

    lp, ee = largo_plazo(Falso(), 0, 1)
    assert np.isnan(lp) and np.isnan(ee)


def test_fdr():
    p = pd.Series([0.001, 0.01, 0.04, 0.5, np.nan])
    assert list(corregir_fdr(p)) == [True, True, False, False, False]


def test_traslado_movil():
    y, x = series(0.5, 0.3)
    movil = traslado_movil(y, x, ventana=60, k=1)
    assert len(movil) == N - 3 - 60 + 1
    assert movil.median() == pytest.approx(0.8, abs=0.1)


def test_por_regimen_mantiene_los_rezagos():
    fechas = pd.date_range("2016-12-01", periods=119, freq="MS")
    y, x = series(0.5, 0.3)
    y, x = y.iloc[:119].set_axis(fechas), x.iloc[:119].set_axis(fechas)
    filas = estimar_por_regimen(y, x)
    assert {f["regimen"] for f in filas} == {"baja", "media", "alta"}
    assert len({f["rezagos_x"] for f in filas}) == 1


def test_cadena():
    rng = np.random.default_rng(3)
    p = rng.normal(0, 1, N)
    i = 0.6 * p + rng.normal(0, 0.5, N)
    # la gondola sigue a la industria un mes despues
    g = np.r_[0, 0.5 * i[:-1]] + rng.normal(0, 0.3, N)
    resp, _ = cadena(*(pd.Series(v, index=FECHAS) for v in (p, i, g)))
    ind = resp[resp.origen == "industria"].set_index("mes")
    assert ind.loc[0, "respuesta"] == pytest.approx(0.0, abs=0.1)
    assert ind.loc[2, "respuesta"] == pytest.approx(0.5, abs=0.1)
    assert ind.loc[2, "ic_inf"] < 0.5 < ind.loc[2, "ic_sup"]
