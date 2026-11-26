from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from monitor.analisis import (
    conectar,
    correlacion_rezagos,
    estacionariedad,
    multiplicador_regional,
    perfil_estacional,
    relativa,
    serie_por_rubro,
)

FECHAS = pd.date_range("2016-12-01", periods=120, freq="MS")


def test_conectar_sin_base_avisa(tmp_path):
    with pytest.raises(FileNotFoundError, match="dbt build"):
        conectar(Path(tmp_path / "no_existe.duckdb"))


def test_correlacion_encuentra_el_rezago():
    rng = np.random.default_rng(0)
    industria = pd.Series(rng.normal(0, 1, 120), index=FECHAS)
    gondola = industria.shift(2) + rng.normal(0, 0.1, 120)  # la gondola copia con 2 meses
    tabla = correlacion_rezagos(gondola.to_frame("carnes"), industria.to_frame("carnes"))
    assert tabla.loc["carnes"].idxmax() == 2
    assert tabla.loc["carnes", 2] > 0.9


def test_correlacion_solo_rubros_en_las_dos():
    a = pd.DataFrame({"x": range(10), "y": range(10)}, dtype=float)
    b = pd.DataFrame({"x": range(10)}, dtype=float)
    assert list(correlacion_rezagos(a, b, 2).index) == ["x"]


def test_relativa_resta_la_general():
    series = pd.DataFrame({"a": [0.05, 0.02], "b": [0.03, 0.01]})
    general = pd.Series([0.03, 0.01])
    assert relativa(series, general).round(10).to_dict("list") == {
        "a": [0.02, 0.01],
        "b": [0.0, 0.0],
    }


def test_perfil_estacional():
    s = pd.Series(np.where(FECHAS.month == 1, 0.01, 0.0), index=FECHAS)
    perfil = perfil_estacional(s.to_frame("frutas"))
    assert perfil.loc["frutas", 1] == pytest.approx(1.0)  # en puntos porcentuales
    assert perfil.loc["frutas", 2] == 0


def test_estacionariedad_ruido_vs_caminata():
    rng = np.random.default_rng(1)
    ruido = pd.Series(rng.normal(0, 1, 200))
    assert estacionariedad(ruido)["estacionaria"]
    assert not estacionariedad(ruido.cumsum())["estacionaria"]


def test_serie_por_rubro_promedia_codigos():
    precios = pd.DataFrame(
        {
            "fecha": [FECHAS[0]] * 3,
            "par_id": ["pan"] * 3,
            "etapa": ["industria"] * 3,
            "region": ["Total del pais"] * 3,
            "var_log": [0.01, 0.03, 0.05],
        }
    )
    assert serie_por_rubro(precios, "industria").loc[FECHAS[0], "pan"] == pytest.approx(0.03)


def test_multiplicador_regional():
    filas = []
    for region in ["GBA", "Pampeana", "Noreste", "Noroeste", "Cuyo", "Patagonia"]:
        filas += [
            {
                "par_id": "pan",
                "etapa": "gondola",
                "region": region,
                "fecha": FECHAS[0],
                "indice": 100.0,
            },
            {
                "par_id": "pan",
                "etapa": "gondola",
                "region": region,
                "fecha": FECHAS[-1],
                "indice": 300.0 if region == "GBA" else 200.0,
            },
        ]
    tabla = multiplicador_regional(pd.DataFrame(filas))
    assert tabla.loc["pan", "GBA"] == 3
    assert tabla.loc["pan", "Cuyo"] == 2
