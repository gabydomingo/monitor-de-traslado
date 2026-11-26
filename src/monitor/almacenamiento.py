"""Crudos versionados: se escribe una version nueva solo si el contenido cambio.

Cada version queda en data/raw/<dataset>/<ventana>/<fecha>_<hash>.parquet y se anota en
data/raw/manifest.csv. Comparando versiones despues sale el historial de revisiones.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

MANIFEST = "manifest.csv"


@dataclass
class Resultado:
    dataset: str
    ventana: str
    filas: int
    periodo_desde: int
    periodo_hasta: int
    hash: str
    guardado: bool
    archivo: str = ""


def hash_contenido(df: pd.DataFrame, clave: list[str]) -> str:
    # mismo contenido, mismo hash, aunque la API devuelva filas o columnas en otro orden
    ordenado = df[sorted(df.columns)].sort_values(clave).reset_index(drop=True)
    return hashlib.sha256(ordenado.to_csv(index=False).encode("utf-8")).hexdigest()


def ultimo_hash(carpeta: Path, dataset: str, ventana: str) -> str | None:
    ruta = carpeta / MANIFEST
    if not ruta.exists():
        return None
    m = pd.read_csv(ruta, dtype=str)
    m = m[(m["dataset"] == dataset) & (m["ventana"] == ventana)]
    return None if m.empty else m.iloc[-1]["hash"]


def guardar(
    df: pd.DataFrame,
    dataset: str,
    ventana: str,
    clave: list[str],
    carpeta: Path,
    ahora: datetime | None = None,
) -> Resultado:
    ahora = ahora or datetime.now(UTC)
    h = hash_contenido(df, clave)
    resultado = Resultado(
        dataset=dataset,
        ventana=ventana,
        filas=len(df),
        periodo_desde=int(df["periodo"].min()),
        periodo_hasta=int(df["periodo"].max()),
        hash=h,
        guardado=h != ultimo_hash(carpeta, dataset, ventana),
    )
    if not resultado.guardado:
        return resultado

    destino = carpeta / dataset / ventana / f"{ahora:%Y%m%dT%H%M%SZ}_{h[:12]}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    # las columnas de control no entran en el hash, solo se guardan
    salida = df.assign(_descargado_utc=ahora.isoformat(timespec="seconds"), _ventana=ventana)
    salida.to_parquet(destino, index=False, compression="zstd")
    resultado.archivo = destino.relative_to(carpeta).as_posix()

    fila = pd.DataFrame(
        [
            {
                "fecha_utc": ahora.isoformat(timespec="seconds"),
                "dataset": dataset,
                "ventana": ventana,
                "filas": resultado.filas,
                "periodo_desde": resultado.periodo_desde,
                "periodo_hasta": resultado.periodo_hasta,
                "hash": h,
                "archivo": resultado.archivo,
            }
        ]
    )
    ruta = carpeta / MANIFEST
    fila.to_csv(ruta, mode="a", header=not ruta.exists(), index=False)
    return resultado
