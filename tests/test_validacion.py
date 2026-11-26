import logging

import pytest

from monitor.validacion import ErrorValidacion, validar


def test_datos_buenos_pasan(df_ipc, conf_ipc):
    df = validar(df_ipc, conf_ipc, "ipc")
    assert len(df) == len(df_ipc)
    assert df["periodo"].dtype.kind == "i"
    assert df["valor"].dtype.kind == "f"


def test_vacio_frena(df_ipc, conf_ipc):
    with pytest.raises(ErrorValidacion, match="0 filas"):
        validar(df_ipc.iloc[0:0], conf_ipc)


def test_falta_columna_frena(df_ipc, conf_ipc):
    with pytest.raises(ErrorValidacion, match="valor"):
        validar(df_ipc.drop(columns="valor"), conf_ipc)


def test_filas_repetidas_frenan(df_ipc, conf_ipc):
    with pytest.raises(ErrorValidacion):
        validar(df_ipc.head(3).pipe(lambda d: d.loc[[0, 0, 1]]), conf_ipc)


def test_mes_invalido_frena(df_ipc, conf_ipc):
    df_ipc.loc[0, "periodo"] = 202613
    with pytest.raises(ErrorValidacion):
        validar(df_ipc, conf_ipc)


def test_valor_no_numerico_frena(df_ipc, conf_ipc):
    df_ipc["valor"] = df_ipc["valor"].astype(object)
    df_ipc.loc[0, "valor"] = "abc"
    with pytest.raises(ErrorValidacion):
        validar(df_ipc, conf_ipc)


def test_clave_nula_frena(df_ipc, conf_ipc):
    df_ipc.loc[0, "region"] = None
    with pytest.raises(ErrorValidacion):
        validar(df_ipc, conf_ipc)


def test_valor_nuevo_avisa_pero_no_frena(df_ipc, conf_ipc, caplog):
    df_ipc.loc[0, "region"] = "Antartida"
    with caplog.at_level(logging.WARNING):
        validar(df_ipc, conf_ipc, "ipc")
    assert "Antartida" in caplog.text


def test_columna_nueva_avisa_pero_no_frena(df_ipc, conf_ipc, caplog):
    df_ipc["fecha_publicacion"] = "2026-11-12"
    with caplog.at_level(logging.WARNING):
        validar(df_ipc, conf_ipc, "ipc")
    assert "fecha_publicacion" in caplog.text
