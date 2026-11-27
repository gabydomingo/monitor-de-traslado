import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from monitor import web

RAIZ = Path(__file__).resolve().parents[1]


def test_pct_pasa_de_log_a_porcentaje():
    assert web.pct(np.log(1.025)) == 2.5
    assert web.lista(pd.Series([np.nan, 1.0])) == [None, 1.0]


def test_json_en_camel_case():
    p = web.Pronostico(
        region="GBA", rubro="pan", valor=2.0, banda80=(1, 3), banda90=(0.5, 3.5), ultimo=None
    )
    d = json.loads(p.model_dump_json(by_alias=True))
    assert set(d) == {"region", "rubro", "valor", "banda80", "banda90", "ultimo"}
    t = web.Traslado(
        region="GBA",
        rubro="pan",
        etapa="industria",
        largo_plazo=0.5,
        intervalo=(0.1, 0.9),
        significativo=True,
        por_mes=(0.3, 0.2, 0, 0),
        n=100,
    )
    assert "largoPlazo" in json.loads(t.model_dump_json(by_alias=True))


def test_el_contrato_rechaza_datos_mal_formados():
    with pytest.raises(ValidationError):
        web.Traslado(
            region="GBA",
            rubro="pan",
            etapa="gondola",  # no es una etapa del mayorista
            largo_plazo=0.5,
            intervalo=(0.1, 0.9),
            significativo=True,
            por_mes=(0.3, 0.2, 0, 0),
            n=100,
        )


def test_proximo_ipc_sale_del_calendario():
    pub = pd.DataFrame(
        {
            "dataset": ["ipc"] * 3 + ["mayorista"],
            "fecha": pd.to_datetime(["2026-08-01", "2026-09-01", "2026-10-01", "2026-10-01"]),
            "publicado": pd.to_datetime(["2026-09-11", "2026-10-14", "2026-11-12", "2026-11-17"]),
        }
    )
    p = web.proximo_ipc(pub, pd.Timestamp("2026-10-01"))
    assert (p.mes, p.publicacion, p.dia_desde, p.dia_hasta) == ("2026-11", "2026-12", 11, 14)


def bt_falso():
    fechas = pd.date_range("2025-01-01", periods=6, freq="MS")
    filas = []
    for par in ["pan", web.NG]:
        for i, f in enumerate(fechas):
            y = 0.02 + 0.001 * i
            filas.append(
                {
                    "par_id": par,
                    "region": "GBA",
                    "fecha": f,
                    "y": y,
                    "naive": y - 0.002,
                    "arx": y + 0.001,
                    "lgbm": y - 0.001,
                    "combinado": y,
                    "lgbm_inf": y - 0.01,
                    "lgbm_sup": y + 0.01,
                    "lgbm_inf_90": y - 0.02,
                    "lgbm_sup_90": y + 0.02,
                }
            )
    return pd.DataFrame(filas)


def test_metricas_separan_rubros_y_nivel_general():
    metricas, anual = web.armar_metricas(bt_falso())
    assert [m.grupo for m in metricas] == ["rubros", "nivel_general"]
    m = metricas[0]
    assert m.combinado == 0 and m.naive == 0.2 and m.cobertura80 == 1
    assert {(x.grupo, x.anio) for x in anual} == {("rubros", 2025), ("nivel_general", 2025)}


def test_backtest_alinea_los_meses():
    bt = bt_falso()
    bt = bt.drop(bt.index[0])  # a pan le falta el primer mes
    b = web.armar_backtest(bt)
    assert len(b.meses) == 6
    pan = next(s for s in b.series if s.rubro == "pan")
    assert len(pan.real) == 6 and pan.real[0] is None


def test_esquema_tiene_los_tres_archivos():
    defs = web.esquema()["$defs"]
    assert {"Resumen", "Series", "Backtest", "Historial"} <= set(defs)
    assert "largoPlazo" in defs["Traslado"]["properties"]


@pytest.mark.parametrize("nombre", list(web.ARCHIVOS))
def test_los_json_subidos_cumplen_el_contrato(nombre):
    # los genera la action: si alguien cambia el contrato y no los regenera, falla aca
    ruta = RAIZ / "data" / "web" / f"{nombre}.json"
    if not ruta.exists():
        pytest.skip("todavia no se genero data/web")
    web.ARCHIVOS[nombre].model_validate_json(ruta.read_text(encoding="utf-8"))


def test_proximo_pronostico_segun_en_que_punto_del_mes_estamos():
    pub = pd.DataFrame(
        {
            "dataset": ["mayorista"] * 2,
            "fecha": pd.to_datetime(["2026-09-01", "2026-10-01"]),
            "publicado": pd.to_datetime(["2026-10-16", "2026-11-19"]),
        }
    )
    oct_, nov, dic = (pd.Timestamp(f"2026-{m}-01") for m in (10, 11, 12))
    # ya esta pronosticado noviembre y el ultimo ipc es octubre: el que sigue es diciembre
    p = web.proximo_pronostico(pub, oct_, nov)
    assert (p.mes, p.publicacion, p.dia_desde, p.dia_hasta) == ("2026-12", "2026-12", 16, 19)
    # salio el ipc de noviembre y todavia no el pronostico de diciembre: tambien diciembre
    assert web.proximo_pronostico(pub, nov, nov).mes == "2026-12"
    # el pronostico de diciembre ya se hizo: el que sigue es enero
    assert web.proximo_pronostico(pub, nov, dic).mes == "2027-01"
