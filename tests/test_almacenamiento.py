import os
from datetime import UTC, datetime

import pandas as pd

from monitor.almacenamiento import guardar, hash_contenido

CLAVE = ["clasificador", "nivel", "codigo", "region", "tipo_de_indicador", "periodo"]
T1 = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
T2 = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)


def test_hash_no_depende_del_orden(df_ipc):
    mezclado = df_ipc.sample(frac=1, random_state=0)[df_ipc.columns[::-1]]
    assert hash_contenido(df_ipc, CLAVE) == hash_contenido(mezclado, CLAVE)


def test_hash_igual_en_windows_y_en_linux(df_ipc, monkeypatch):
    # paso de verdad: la misma descarga daba otro hash en windows y en actions
    linux = hash_contenido(df_ipc, CLAVE)
    monkeypatch.setattr(os, "linesep", "\r\n")
    assert hash_contenido(df_ipc, CLAVE) == linux


def test_hash_cambia_si_cambia_un_valor(df_ipc):
    otro = df_ipc.copy()
    otro.loc[0, "valor"] += 0.01
    assert hash_contenido(df_ipc, CLAVE) != hash_contenido(otro, CLAVE)


def test_primera_vez_guarda(df_ipc, tmp_path):
    r = guardar(df_ipc, "ipc", "reciente", CLAVE, tmp_path, T1)
    assert r.guardado
    assert (tmp_path / r.archivo).exists()
    assert r.archivo.startswith("ipc/reciente/20261126T120000Z_")
    guardado = pd.read_parquet(tmp_path / r.archivo)
    assert len(guardado) == len(df_ipc)
    assert {"_descargado_utc", "_ventana"} <= set(guardado.columns)


def test_mismo_contenido_no_guarda_de_nuevo(df_ipc, tmp_path):
    guardar(df_ipc, "ipc", "reciente", CLAVE, tmp_path, T1)
    r = guardar(df_ipc.iloc[::-1], "ipc", "reciente", CLAVE, tmp_path, T2)
    assert not r.guardado
    assert len(list((tmp_path / "ipc" / "reciente").glob("*.parquet"))) == 1
    assert len(pd.read_csv(tmp_path / "manifest.csv")) == 1


def test_revision_guarda_version_nueva(df_ipc, tmp_path):
    guardar(df_ipc, "ipc", "reciente", CLAVE, tmp_path, T1)
    revisado = df_ipc.copy()
    revisado.loc[0, "valor"] = 999.0
    r = guardar(revisado, "ipc", "reciente", CLAVE, tmp_path, T2)
    assert r.guardado
    manifest = pd.read_csv(tmp_path / "manifest.csv")
    assert len(manifest) == 2
    assert list(manifest["fecha_utc"]) == ["2026-11-26T12:00:00+00:00", "2026-11-27T12:00:00+00:00"]


def test_ventanas_y_datasets_se_versionan_por_separado(df_ipc, tmp_path):
    guardar(df_ipc, "ipc", "reciente", CLAVE, tmp_path, T1)
    assert guardar(df_ipc, "ipc", "completo", CLAVE, tmp_path, T1).guardado
    assert guardar(df_ipc, "mayorista", "reciente", CLAVE, tmp_path, T1).guardado
