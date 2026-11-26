"""Validacion de lo que devuelve la API antes de guardarlo.

Si cambia algo grave (faltan columnas, tipos rotos, filas repetidas) frena con error.
Si aparece algo nuevo pero inofensivo (una columna o un valor que no conociamos) solo avisa.
"""

import logging

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaError, SchemaErrors

log = logging.getLogger(__name__)


class ErrorValidacion(ValueError):
    pass


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

    # indice limpio: con indices repetidos pandera falla por dentro en vez de reportar
    df = df.reset_index(drop=True)
    try:
        df = esquema(conf).validate(df, lazy=True)
    except (SchemaError, SchemaErrors) as e:
        raise ErrorValidacion(f"{nombre}: no pasa el esquema\n{e}") from e

    for col, valores in conf.get("valores_conocidos", {}).items():
        aparecen = set(df[col].dropna().unique()) - set(valores)
        if aparecen:
            log.warning("%s: valores nuevos en %s: %s", nombre, col, sorted(aparecen))

    return df
