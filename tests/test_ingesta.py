import pandas as pd
import pytest

from monitor.cliente import ClienteIndec, ErrorApi
from monitor.ingesta import ingerir, main, restar_meses

from fakes import SesionFalsa


@pytest.mark.parametrize(
    ("periodo", "n", "esperado"),
    [(202610, 5, 202605), (202603, 5, 202510), (202601, 1, 202512), (202612, 0, 202612)],
)
def test_restar_meses(periodo, n, esperado):
    assert restar_meses(periodo, n) == esperado


def cliente_falso(filas):
    sesion = SesionFalsa(filas)
    return ClienteIndec("https://api.test/v1", "tok", session=sesion, dormir=lambda s: None), sesion


def test_reciente_baja_solo_los_ultimos_meses(filas_ipc, conf_ipc, tmp_path):
    cliente, sesion = cliente_falso(filas_ipc)
    r = ingerir(cliente, "ipc", conf_ipc, "reciente", 2, tmp_path)
    assert (r.periodo_desde, r.periodo_hasta) == (202609, 202610)
    assert r.filas == 12 * 7 * 2
    assert any(ll["params"].get("periodo") == "gte.202609" for ll in sesion.llamadas)


def test_completo_baja_todo(filas_ipc, conf_ipc, tmp_path):
    cliente, _ = cliente_falso(filas_ipc)
    r = ingerir(cliente, "ipc", conf_ipc, "completo", 2, tmp_path)
    assert r.filas == len(filas_ipc)
    assert r.guardado


def test_dos_corridas_iguales_guardan_una_sola_version(filas_ipc, conf_ipc, tmp_path):
    for _ in range(2):
        cliente, _ = cliente_falso(filas_ipc)
        ingerir(cliente, "ipc", conf_ipc, "reciente", 6, tmp_path)
    assert len(pd.read_csv(tmp_path / "manifest.csv")) == 1


def test_si_faltan_filas_no_guarda(filas_ipc, conf_ipc, tmp_path):
    cliente, _ = cliente_falso(filas_ipc)
    cliente.bajar = lambda *a, **k: filas_ipc[:-1]  # el indec publico a mitad
    with pytest.raises(ErrorApi, match="se esperaban"):
        ingerir(cliente, "ipc", conf_ipc, "completo", 6, tmp_path)
    assert not (tmp_path / "manifest.csv").exists()


def test_main_sigue_si_falla_un_dataset(monkeypatch, filas_ipc, tmp_path):
    llamados = []

    def ingerir_falso(cliente, nombre, *a, **k):
        llamados.append(nombre)
        raise ErrorApi("caida")

    monkeypatch.setenv("INDEC_API_TOKEN", "tok")
    monkeypatch.setattr("monitor.ingesta.ingerir", ingerir_falso)
    monkeypatch.setattr("monitor.ingesta.ingerir_bcra", ingerir_falso)
    codigo = main(["--modo", "reciente", "--salida", str(tmp_path)])
    assert codigo == 1
    assert llamados == ["ipc", "mayorista", "bcra"]


def test_main_rechaza_dataset_desconocido(monkeypatch):
    monkeypatch.setenv("INDEC_API_TOKEN", "tok")
    with pytest.raises(SystemExit):
        main(["--dataset", "pobreza"])


def test_main_sigue_si_un_dataset_rompe_de_forma_inesperada(monkeypatch, tmp_path):
    # un KeyError en uno (la api cambio la forma de la respuesta) no frena a los demas
    llamados = []

    def ingerir_falso(cliente, nombre, *a, **k):
        llamados.append(nombre)
        raise KeyError("periodo")

    monkeypatch.setenv("INDEC_API_TOKEN", "tok")
    monkeypatch.setattr("monitor.ingesta.ingerir", ingerir_falso)
    monkeypatch.setattr("monitor.ingesta.ingerir_bcra", ingerir_falso)
    assert main(["--modo", "reciente", "--salida", str(tmp_path)]) == 1
    assert llamados == ["ipc", "mayorista", "bcra"]
