from datetime import UTC, datetime

import pandas as pd

from monitor import mensual


def e(ipc, may, dolar):
    return {"ipc": pd.Timestamp(ipc), "mayorista": pd.Timestamp(may), "dolar": pd.Timestamp(dolar)}


def test_listo_cuando_salio_el_mayorista_y_pasaron_15_dias():
    objetivo, faltan = mensual.que_falta(e("2026-10-01", "2026-10-01", "2026-11-19"))
    assert objetivo == pd.Timestamp("2026-11-01")
    assert faltan == []


def test_espera_al_mayorista():
    # salio el ipc de octubre pero el mayorista sigue en septiembre
    _, faltan = mensual.que_falta(e("2026-10-01", "2026-09-01", "2026-11-19"))
    assert faltan == ["el mayorista de 10-2026"]


def test_espera_el_dolar_hasta_el_13():
    _, faltan = mensual.que_falta(e("2026-10-01", "2026-10-01", "2026-11-12"))
    assert faltan == ["el dolar hasta el 13 de 11-2026"]


def test_registro_no_se_pisa(tmp_path, monkeypatch):
    registro = tmp_path / "registro.csv"
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(
        {"dataset": ["ipc", "ipc", "bcra"], "hash": ["a" * 64, "b" * 64, "c" * 64]}
    ).to_csv(manifest, index=False)
    monkeypatch.setattr(mensual, "MANIFEST", manifest)
    prox = pd.DataFrame({"par_id": ["pan"], "region": ["GBA"], "fecha": ["2026-11-01"]})
    assert not mensual.ya_pronosticado(pd.Timestamp("2026-11-01"), registro)
    mensual.registrar(prox, registro, ahora=datetime(2026, 11, 19, tzinfo=UTC))
    assert mensual.ya_pronosticado(pd.Timestamp("2026-11-01"), registro)
    fila = pd.read_csv(registro).iloc[0]
    # se queda con el ultimo archivo de cada dataset
    assert fila["datos"] == f"bcra:{'c' * 12};ipc:{'b' * 12}"


def test_registro_con_columnas_nuevas_no_queda_corrido(tmp_path, monkeypatch):
    registro = tmp_path / "registro.csv"
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame({"dataset": ["ipc"], "hash": ["a" * 64]}).to_csv(manifest, index=False)
    monkeypatch.setattr(mensual, "MANIFEST", manifest)
    viejo = pd.DataFrame(
        {"par_id": ["pan"], "region": ["GBA"], "fecha": ["2026-11-01"], "inf": [1.0]}
    )
    mensual.registrar(viejo, registro)
    nuevo = viejo.assign(fecha="2026-12-01", inf=2.0, inf_90=0.5)
    mensual.registrar(nuevo, registro)
    df = pd.read_csv(registro)
    assert df["inf"].tolist() == [1.0, 2.0]
    assert df["inf_90"].isna().tolist() == [True, False]
    assert len(df) == 2


def test_registro_suma_series_nuevas_sin_repetir(tmp_path, monkeypatch):
    registro = tmp_path / "registro.csv"
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame({"dataset": ["ipc"], "hash": ["a" * 64]}).to_csv(manifest, index=False)
    monkeypatch.setattr(mensual, "MANIFEST", manifest)
    pan = pd.DataFrame(
        {"par_id": ["pan"], "region": ["GBA"], "fecha": ["2026-11-01"], "inf": [1.0]}
    )
    mensual.registrar(pan, registro)
    # se vuelve a correr el mismo mes con el nivel general agregado: pan no se pisa
    otra = pd.concat([pan.assign(inf=9.0), pan.assign(par_id="nivel_general", inf=2.0)])
    mensual.registrar(otra, registro)
    df = pd.read_csv(registro)
    assert df.set_index("par_id")["inf"].to_dict() == {"pan": 1.0, "nivel_general": 2.0}
    mensual.registrar(otra, registro)
    assert len(pd.read_csv(registro)) == 2


def test_registro_mantiene_un_solo_formato_de_fecha(tmp_path, monkeypatch):
    # paso de verdad: el registro tenia fechas como texto y el pronostico llego como timestamp,
    # y al reescribir quedaron filas con "00:00:00" que despues no se podian leer juntas
    registro = tmp_path / "registro.csv"
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame({"dataset": ["ipc"], "hash": ["a" * 64]}).to_csv(manifest, index=False)
    monkeypatch.setattr(mensual, "MANIFEST", manifest)
    viejo = pd.DataFrame(
        {"par_id": ["pan"], "region": ["GBA"], "fecha": ["2026-11-01"], "inf": [1.0]}
    )
    mensual.registrar(viejo, registro)
    nuevo = pd.DataFrame(
        {
            "par_id": ["nivel_general", "pan"],
            "region": ["GBA", "GBA"],
            "fecha": pd.to_datetime(["2026-11-01", "2026-12-01"]),
            "inf": [2.0, 3.0],
            "inf_90": [1.5, 2.5],  # columna nueva: fuerza la reescritura
        }
    )
    mensual.registrar(nuevo, registro)
    df = pd.read_csv(registro, dtype=str)
    assert set(df["fecha"]) == {"2026-11-01", "2026-12-01"}
    assert len(df) == 3
    assert mensual.ya_pronosticado(pd.Timestamp("2026-12-01"), registro)


def test_cambio_de_anio():
    # con el ipc de diciembre el objetivo es enero del anio siguiente
    objetivo, faltan = mensual.que_falta(e("2026-12-01", "2026-12-01", "2027-01-13"))
    assert objetivo == pd.Timestamp("2027-01-01")
    assert faltan == []
    _, faltan = mensual.que_falta(e("2026-12-01", "2026-12-01", "2027-01-12"))
    assert faltan == ["el dolar hasta el 13 de 01-2027"]
