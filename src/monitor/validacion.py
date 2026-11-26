"""Chequeos sobre lo que devuelve la api antes de guardarlo."""

import logging
import unicodedata

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaError, SchemaErrors

log = logging.getLogger(__name__)


class ErrorValidacion(ValueError):
    pass


def sin_tildes(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normal if not unicodedata.combining(c))


def esquema(conf: dict) -> pa.DataFrameSchema:
    clave = conf["clave"]
    columnas = {c: pa.Column(nullable=True) for c in conf["columnas"]}
    for c in clave:
        columnas[c] = pa.Column(str, nullable=False, coerce=True)
    columnas["periodo"] = pa.Column(
        int,
        checks=[
            pa.Check.in_range(201001, 210012),
            pa.Check(lambda s: s.mod(100).between(1, 12), error="mes fuera de 1-12"),
        ],
        nullable=False,
        coerce=True,
    )
    columnas["valor"] = pa.Column(float, nullable=True, coerce=True)
    return pa.DataFrameSchema(columnas, unique=clave, strict=False)


def validar(df: pd.DataFrame, conf: dict, nombre: str = "") -> pd.DataFrame:
    if df.empty:
        raise ErrorValidacion(f"{nombre}: la API devolvio 0 filas")

    faltan = set(conf["columnas"]) - set(df.columns)
    if faltan:
        raise ErrorValidacion(f"{nombre}: faltan columnas {sorted(faltan)}")

    conocidas = set(conf["columnas"]) | set(conf.get("columnas_extra", []))
    nuevas = set(df.columns) - conocidas
    if nuevas:
        log.warning("%s: columnas nuevas en la API: %s", nombre, sorted(nuevas))

    # pandera se rompe con indices repetidos, lo reseteo antes
    df = df.reset_index(drop=True)
    try:
        df = esquema(conf).validate(df, lazy=True)
    except (SchemaError, SchemaErrors) as e:
        raise ErrorValidacion(f"{nombre}: no pasa el esquema\n{e}") from e

    # un valor nuevo no frena, solo aviso. comparo sin tildes porque el indec no es parejo
    for col, valores in conf.get("valores_conocidos", {}).items():
        conocidos = {sin_tildes(v) for v in valores}
        aparecen = {v for v in df[col].dropna().unique() if sin_tildes(v) not in conocidos}
        if aparecen:
            log.warning("%s: valores nuevos en %s: %s", nombre, col, sorted(aparecen))

    return df
