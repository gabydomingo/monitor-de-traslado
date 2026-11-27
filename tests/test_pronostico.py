import numpy as np
import pandas as pd
import pytest

from monitor import pronostico as p

FECHAS = pd.date_range("2016-12-01", periods=80, freq="MS")


def datos_falsos(seed=0):
    # la gondola sigue al mayorista del mes anterior: algo que un modelo puede aprender
    rng = np.random.default_rng(seed)
    may = pd.DataFrame({r: rng.normal(0.02, 0.01, 80) for r in ["carnes", "pan"]}, index=FECHAS)
    general = pd.DataFrame(
        {"GBA": rng.normal(0.02, 0.005, 80), "Cuyo": rng.normal(0.02, 0.005, 80)}, index=FECHAS
    )
    general["mayorista"] = may.mean(axis=1)
    gondola = {
        reg: pd.DataFrame(
            {r: 0.8 * may[r].shift(1).fillna(0.02) + rng.normal(0, 0.002, 80) for r in may},
            index=FECHAS,
        )
        for reg in ["GBA", "Cuyo"]
    }
    return p.armar_panel(gondola, may, general)


@pytest.fixture(scope="module")
def panel():
    return datos_falsos()


def test_features_salen_del_mes_anterior(panel):
    s = panel[(panel.par_id == "carnes") & (panel.region == "GBA")].set_index("fecha")
    assert s["y_l1"].iloc[5] == s["y"].iloc[4]
    assert s["y_l12"].iloc[20] == s["y"].iloc[8]
    assert s["y_m12"].iloc[20] == pytest.approx(s["y"].iloc[8:20].mean())


def test_hay_fila_para_el_mes_que_viene(panel):
    ultima = panel[panel.fecha == panel.fecha.max()]
    assert ultima["fecha"].iloc[0] == FECHAS[-1] + pd.offsets.MonthBegin(1)
    assert ultima["y"].isna().all()
    assert ultima["y_l1"].notna().all()
    assert len(ultima) == 4  # 2 rubros x 2 regiones


def test_rubro_sin_mayorista_queda_vacio():
    g = {"GBA": pd.DataFrame({"x": np.linspace(0, 1, 20)}, index=FECHAS[:20])}
    general = pd.DataFrame({"GBA": 0.01, "mayorista": 0.01}, index=FECHAS[:20])
    panel = p.armar_panel(g, pd.DataFrame(index=FECHAS[:20]), general)
    assert panel["may_l1"].isna().all()


def test_backtest_no_mira_el_futuro(panel, monkeypatch):
    vistos = []

    def espia(train, test):
        vistos.append((train["fecha"].max(), test["fecha"].min()))
        return test["y_l1"].to_numpy()

    monkeypatch.setattr(p, "MODELOS", {"naive": espia})
    pred = p.backtest(panel, meses=6, intervalo=False)
    assert len(vistos) == 6
    assert all(ultimo_train < mes for ultimo_train, mes in vistos)
    assert pred["fecha"].nunique() == 6


def test_baselines(panel):
    test = panel.dropna(subset=["y"]).tail(4)
    assert (p.naive(None, test) == test["y_l1"]).all()
    assert p.media3(None, test) == pytest.approx(test[["y_l1", "y_l2", "y_l3"]].mean(axis=1))


def test_modelos_le_ganan_al_naive(panel):
    pred = p.backtest(panel, meses=12, intervalo=False)
    tabla = p.metricas(pred, p.escala_mase(panel, pred["fecha"].min()))
    assert tabla.loc["naive", "vs_naive"] == 1
    assert tabla.loc["arx", "vs_naive"] < 0.7
    assert tabla.loc["lgbm", "vs_naive"] < 1
    assert tabla.loc["combinado", "vs_naive"] < 1


def test_combinado_es_el_promedio():
    assert p.combinar([1.0, 3.0], [3.0, 5.0]).tolist() == [2.0, 4.0]


def test_ajuste_conformal():
    puntajes = pd.Series(np.arange(1, 11, dtype=float))
    # con n=10 y alfa=0.2 el nivel es 0.8 * 11 / 10 = 0.88
    assert p.ajuste_conformal(puntajes) == pytest.approx(np.quantile(puntajes, 0.88))


def test_calibrar_solo_usa_el_pasado():
    meses = pd.date_range("2024-01-01", periods=10, freq="MS")
    pred = pd.DataFrame(
        {
            "fecha": np.repeat(meses, 5),
            "par_id": "carnes",
            "y": 1.0,
            "lgbm_q10": 0.0,
            "lgbm_q90": np.r_[
                np.full(25, 0.5), np.full(25, 2.0)
            ],  # los primeros 5 meses quedan cortos
        }
    )
    cal = p.calibrar(pred, ventana=4, minimo=3)
    por_mes = cal.groupby("fecha")["ajuste"].first()
    assert por_mes.iloc[:3].isna().all()
    assert por_mes.iloc[3] == pytest.approx(0.5)  # aprendio de los meses que fallaron
    assert por_mes.iloc[-1] < 0  # cuando el intervalo sobra, lo achica


def test_calibra_cada_rubro_por_separado():
    meses = pd.date_range("2024-01-01", periods=8, freq="MS")
    pred = pd.DataFrame(
        {
            "fecha": np.repeat(meses, 2),
            "par_id": ["verduras", "pan"] * 8,
            "y": [5.0, 1.0] * 8,
            "lgbm_q10": 0.0,
            "lgbm_q90": 2.0,  # a verduras siempre le falta 3, a pan le sobra 1
        }
    )
    ultimo = p.calibrar(pred, ventana=4, minimo=3).query("fecha == fecha.max()")
    aj = ultimo.set_index("par_id")["ajuste"]
    assert aj["verduras"] == pytest.approx(3.0)
    assert aj["pan"] == pytest.approx(-1.0)


def test_rubro_sin_historia_se_lleva_el_ensanche_mas_grande():
    aj = pd.Series({"pan": 0.1, "verduras": 0.5})
    df = pd.DataFrame({"par_id": ["pan", "nuevo"]})
    assert p.aplicar_ajuste(df, aj).tolist() == [0.1, 0.5]


def test_diebold_mariano():
    rng = np.random.default_rng(0)
    fechas = np.repeat(pd.date_range("2023-01-01", periods=36, freq="MS"), 10)
    y = rng.normal(0, 1, len(fechas))
    pred = pd.DataFrame(
        {
            "fecha": fechas,
            "y": y,
            "bueno": y + rng.normal(0, 0.1, len(y)),
            "malo": y + rng.normal(0, 1, len(y)),
        }
    )
    r = p.diebold_mariano(pred, "bueno", "malo")
    assert r["dif_mae_pp"] < 0
    assert r["p_valor"] < 0.001


def test_pronostico_dentro_del_intervalo(panel):
    prox = p.pronosticar_proximo(panel, pd.Series({"cualquiera": 0.0}))
    assert len(prox) == 4
    assert (prox["inf_90"] <= prox["inf"]).all()
    assert (prox["inf"] <= prox["pronostico"]).all()
    assert (prox["pronostico"] <= prox["sup"]).all()
    assert (prox["sup"] <= prox["sup_90"]).all()


def test_features_del_bcra_solo_usan_lo_que_se_sabe():
    fechas = pd.date_range("2023-09-01", periods=4, freq="MS")
    bcra = pd.DataFrame(
        {
            "tc_promedio": [350.0, 350.0, 360.0, 700.0],
            "tc_inicio_mes": [350.0, 350.0, 355.0, 400.0],
            "rem_12m": [100.0, 120.0, 150.0, 200.0],
        },
        index=fechas,
    )
    f = p.features_bcra(bcra, fechas)
    dic = f.loc["2023-12-01"]
    assert dic["tc_l1"] == pytest.approx(np.log(360 / 350))  # noviembre contra octubre
    assert dic["tc_inicio_mes"] == pytest.approx(np.log(400 / 360))  # 1 al 13 de dic vs nov
    assert dic["rem_l1"] == pytest.approx(np.log(2.5) / 12)  # el rem de fines de noviembre
    # el promedio de todo diciembre (700) no puede aparecer en la fila de diciembre
    assert not np.isclose(f.loc["2023-12-01"].to_numpy(), np.log(700 / 360)).any()


def test_sin_bcra_las_columnas_quedan_vacias(panel):
    assert panel[["tc_l1", "tc_inicio_mes", "rem_l1"]].isna().all().all()


def test_features_no_cambian_si_borro_el_futuro():
    """La prueba mas fuerte contra la fuga: si armo el panel solo con lo que se sabia al
    pronosticar el mes T, las features de T tienen que dar exactamente igual."""
    rng = np.random.default_rng(5)
    may = pd.DataFrame({r: rng.normal(0.02, 0.01, 80) for r in ["carnes", "pan"]}, index=FECHAS)
    general = pd.DataFrame({"GBA": rng.normal(0.02, 0.005, 80)}, index=FECHAS)
    general["mayorista"] = may.mean(axis=1)
    gondola = {"GBA": may.shift(1).fillna(0.02) * 0.8 + rng.normal(0, 0.002, (80, 2))}
    bcra = pd.DataFrame(
        {
            "tc_promedio": np.exp(np.cumsum(rng.normal(0.02, 0.01, 81))),
            "tc_inicio_mes": np.exp(np.cumsum(rng.normal(0.02, 0.01, 81))),
            "rem_12m": rng.uniform(20, 100, 81),
        },
        index=pd.date_range(FECHAS[0], periods=81, freq="MS"),
    )
    completo = p.armar_panel(gondola, may, general, bcra)
    for t in [FECHAS[20], FECHAS[50], FECHAS[79]]:
        antes = FECHAS[: FECHAS.get_loc(t)]
        b = bcra[bcra.index <= t].copy()
        b.loc[t, ["tc_promedio", "rem_12m"]] = np.nan  # de T solo se conoce el inicio del mes
        trunco = p.armar_panel(
            {"GBA": gondola["GBA"].loc[antes]}, may.loc[antes], general.loc[antes], b
        )

        def fila(d, t=t):
            return d[d.fecha == t].sort_values("par_id")[p.FEATURES[2:]].to_numpy(float)

        np.testing.assert_allclose(fila(completo), fila(trunco), equal_nan=True)


def test_conformal_cubre_80_con_volatilidad_estable():
    rng = np.random.default_rng(0)
    meses = pd.date_range("2020-01-01", periods=30, freq="MS")
    pred = pd.DataFrame(
        [
            {"fecha": m, "par_id": "x", "y": rng.standard_t(4), "lgbm_q10": -0.5, "lgbm_q90": 0.5}
            for m in meses
            for _ in range(114)
        ]
    )
    pred = p.calibrar(pred)
    pred = pred[pred["ajuste"].notna()]
    cobertura = pred["y"].between(pred["lgbm_inf"], pred["lgbm_sup"]).mean()
    assert 0.78 <= cobertura <= 0.82
    cobertura_90 = pred["y"].between(pred["lgbm_inf_90"], pred["lgbm_sup_90"]).mean()
    assert 0.88 <= cobertura_90 <= 0.92
    # la banda del 90 siempre contiene a la del 80
    assert (pred["lgbm_inf_90"] <= pred["lgbm_inf"]).all()
    assert (pred["lgbm_sup_90"] >= pred["lgbm_sup"]).all()


def test_el_intervalo_se_agranda_si_salto_el_dolar():
    aj = pd.Series({"carnes": 0.01})
    df = pd.DataFrame({"par_id": ["carnes", "carnes"], "tc_inicio_mes": [0.0, 0.3]})
    tranquilo, devaluacion = p.aplicar_ajuste(df, aj)
    assert tranquilo == pytest.approx(0.01)
    assert devaluacion == pytest.approx(0.01 * (1 + p.ESCALA_DOLAR * 0.3))
