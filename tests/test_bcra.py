from datetime import date

import pandas as pd
import pytest

from monitor.cliente import ClienteBcra, ErrorApi
from monitor.ingesta import ingerir_bcra, main

from fakes import Respuesta

CONF = {
    "fuente": "bcra",
    "desde": "2015-01-01",
    "variables": {5: "tipo_cambio_mayorista", 29: "rem_12m"},
    "clave": ["id_variable", "fecha"],
    "columnas": ["id_variable", "variable", "fecha", "periodo", "valor"],
}


class SesionBcra:
    """La api del bcra devuelve de la fecha mas nueva a la mas vieja, paginado con offset."""

    def __init__(self, series, como_dict=False, mentir_total=0):
        self.series = series  # {id: [(fecha, valor), ...]}
        self.como_dict = como_dict
        self.mentir_total = mentir_total
        self.headers = {}
        self.llamadas = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.llamadas.append({"url": url, "params": params})
        id_variable = int(url.rsplit("/", 1)[1])
        datos = [
            {"fecha": f, "valor": v}
            for f, v in sorted(self.series[id_variable], reverse=True)
            if params["desde"] <= f <= params["hasta"]
        ]
        pagina = datos[params["offset"] : params["offset"] + params["limit"]]
        resultado = {"idVariable": id_variable, "detalle": pagina}
        meta = {"count": len(datos) + self.mentir_total, "offset": params["offset"]}
        return Respuesta(
            {
                "status": 200,
                "metadata": {"resultset": meta},
                "results": resultado if self.como_dict else [resultado],
            }
        )


def dias(desde, n, valor=100.0):
    return [(f"{d:%Y-%m-%d}", valor + i) for i, d in enumerate(pd.date_range(desde, periods=n))]


def cliente(series, **kw):
    sesion = SesionBcra(series, **{k: kw.pop(k) for k in ["como_dict", "mentir_total"] if k in kw})
    c = ClienteBcra("https://api.test/v4.0", session=sesion, dormir=lambda s: None, **kw)
    return c, sesion


def test_pagina_hasta_traer_todo():
    c, sesion = cliente({5: dias("2026-01-01", 25)}, limite_filas=10)
    filas = c.serie(5, "2026-01-01", "2026-12-31")
    assert len(filas) == 25
    assert len(sesion.llamadas) == 3


@pytest.mark.parametrize("como_dict", [True, False])
def test_results_puede_venir_como_lista_o_como_objeto(como_dict):
    c, _ = cliente({5: dias("2026-01-01", 5)}, como_dict=como_dict)
    assert len(c.serie(5, "2026-01-01", "2026-12-31")) == 5


def test_si_faltan_filas_frena():
    c, _ = cliente({5: dias("2026-01-01", 5)}, mentir_total=3)
    with pytest.raises(ErrorApi, match="se esperaban"):
        c.serie(5, "2026-01-01", "2026-12-31")


def test_ingesta_completa_arma_el_periodo_y_guarda(tmp_path):
    series = {5: dias("2025-12-20", 20), 29: [("2025-12-31", 20.5), ("2026-01-31", 20.1)]}
    c, _ = cliente(series)
    r = ingerir_bcra(c, "bcra", CONF, "completo", 6, tmp_path, hoy=date(2026, 2, 10))
    assert r.guardado
    assert (r.periodo_desde, r.periodo_hasta) == (202512, 202601)
    df = pd.read_parquet(tmp_path / r.archivo)
    assert set(df["variable"]) == {"tipo_cambio_mayorista", "rem_12m"}
    assert len(df) == 22


def test_reciente_pide_solo_los_ultimos_meses(tmp_path):
    c, sesion = cliente({5: dias("2026-06-01", 40), 29: [("2026-06-30", 20.0)]})
    ingerir_bcra(c, "bcra", CONF, "reciente", 6, tmp_path, hoy=date(2026, 11, 26))
    assert {ll["params"]["desde"] for ll in sesion.llamadas} == {"2026-05-26"}
    assert {ll["params"]["hasta"] for ll in sesion.llamadas} == {"2026-11-26"}


def test_dos_corridas_iguales_guardan_una_sola_version(tmp_path):
    for _ in range(2):
        c, _ = cliente({5: dias("2026-01-01", 10), 29: [("2026-01-31", 20.0)]})
        ingerir_bcra(c, "bcra", CONF, "completo", 6, tmp_path, hoy=date(2026, 2, 1))
    assert len(pd.read_csv(tmp_path / "manifest.csv")) == 1


def test_main_baja_el_bcra_sin_token_del_indec(monkeypatch, tmp_path):
    monkeypatch.setattr("monitor.ingesta.token_indec", lambda: pytest.fail("pidio el token"))
    monkeypatch.setattr(
        ClienteBcra, "serie", lambda self, i, d, h: [{"fecha": "2026-10-31", "valor": 1.0}]
    )
    assert main(["--dataset", "bcra", "--salida", str(tmp_path)]) == 0
