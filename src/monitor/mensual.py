"""Corre los modelos cuando hay un mes nuevo para pronosticar.

El pronostico de cada mes se guarda una sola vez en data/resultados/registro_pronosticos.csv
y no se pisa: es lo que el modelo dijo en su momento, con los datos que habia. Cuando el indec
publique el dato se puede ver cuanto erro de verdad, sin backtest de por medio.

uv run python -m monitor.mensual
uv run python -m monitor.mensual --forzar   (aunque ya este pronosticado)
"""

import argparse
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from monitor import analisis as a
from monitor import pronostico, traslado
from monitor.config import RAIZ

log = logging.getLogger("monitor.mensual")

RESULTADOS = RAIZ / "data" / "resultados"
REGISTRO = RESULTADOS / "registro_pronosticos.csv"
MANIFEST = RAIZ / "data" / "raw" / "manifest.csv"


def estado(con) -> dict:
    """Hasta donde llegan los datos que hay en el warehouse."""
    q = "select max(fecha) from fct_precios where etapa = ?"
    ipc = con.execute(q, ["gondola"]).fetchone()[0]
    may = con.execute(q, ["industria"]).fetchone()[0]
    dolar = con.execute("select max(ultimo_dia) from fct_bcra_mensual").fetchone()[0]
    return {"ipc": pd.Timestamp(ipc), "mayorista": pd.Timestamp(may), "dolar": pd.Timestamp(dolar)}


def que_falta(e: dict) -> tuple[pd.Timestamp, list[str]]:
    """El mes a pronosticar y lo que todavia no se publico para poder hacerlo."""
    objetivo = e["ipc"] + pd.offsets.MonthBegin(1)
    faltan = []
    if e["mayorista"] < e["ipc"]:
        faltan.append(f"el mayorista de {e['ipc']:%m-%Y}")
    if e["dolar"] < objetivo + pd.Timedelta(days=12):
        faltan.append(f"el dolar hasta el 13 de {objetivo:%m-%Y}")
    return objetivo, faltan


def ya_pronosticado(objetivo: pd.Timestamp, registro: Path = REGISTRO) -> bool:
    if not registro.exists():
        return False
    fechas = pd.to_datetime(pd.read_csv(registro, usecols=["fecha"])["fecha"])
    return bool((fechas == objetivo).any())


def version_datos(manifest: Path | None = None) -> str:
    # el ultimo archivo de cada dataset: con eso se puede reconstruir que datos se usaron
    m = pd.read_csv(manifest or MANIFEST, dtype=str)
    ultimos = m.groupby("dataset")["hash"].last()
    return ";".join(f"{d}:{h[:12]}" for d, h in ultimos.items())


def registrar(prox: pd.DataFrame, registro: Path = REGISTRO, ahora: datetime | None = None):
    ahora = ahora or datetime.now(UTC)
    filas = prox.assign(
        generado_utc=ahora.isoformat(timespec="seconds"),
        modelo=pronostico.version_modelo(),
        datos=version_datos(),
    )
    filas.to_csv(registro, mode="a", header=not registro.exists(), index=False)


def resumen(texto: str) -> None:
    log.info(texto)
    ruta = os.getenv("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corre los modelos si hay un mes nuevo")
    parser.add_argument("--forzar", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    e = estado(a.conectar())
    objetivo, faltan = que_falta(e)
    if faltan and not args.forzar:
        resumen(f"Para pronosticar {objetivo:%m-%Y} falta {' y '.join(faltan)}. No corro nada.")
        return 0
    if ya_pronosticado(objetivo) and not args.forzar:
        resumen(f"{objetivo:%m-%Y} ya esta pronosticado. No corro nada.")
        return 0

    traslado.main()
    tabla, prox = pronostico.main()
    if not ya_pronosticado(objetivo):
        registrar(prox)
    gba = prox[prox["region"] == "GBA"].set_index("par_id")["pronostico"].round(1)
    resumen(
        f"Pronostico de {objetivo:%m-%Y} (modelo {pronostico.version_modelo()})\n\n"
        f"Error del backtest, combinado: {tabla.loc['combinado', 'mae_pp']:.2f} pp "
        f"(naive {tabla.loc['naive', 'mae_pp']:.2f})\n\n"
        "| rubro (GBA) | % mensual |\n|---|---|\n"
        + "\n".join(f"| {r} | {v} |" for r, v in gba.items())
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
