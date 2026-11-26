"""Bajada de datos del INDEC.

Uso:
    uv run python -m monitor.ingesta --modo reciente     # ultimos meses (corre todos los dias)
    uv run python -m monitor.ingesta --modo completo     # toda la historia (una vez por mes)
    uv run python -m monitor.ingesta --modo reciente --dataset ipc --salida data/prueba
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd

from monitor.almacenamiento import Resultado, guardar
from monitor.cliente import ClienteIndec, ErrorApi
from monitor.config import RAIZ, cargar_config, token_indec
from monitor.validacion import ErrorValidacion, validar

log = logging.getLogger("monitor.ingesta")


def restar_meses(periodo: int, n: int) -> int:
    """restar_meses(202603, 5) -> 202510"""
    anio, mes = divmod(periodo, 100)
    total = anio * 12 + (mes - 1) - n
    return (total // 12) * 100 + total % 12 + 1


def ingerir(
    cliente: ClienteIndec,
    nombre: str,
    conf: dict,
    modo: str,
    meses_recientes: int,
    carpeta: Path,
) -> Resultado:
    endpoint = conf["endpoint"]
    filtros = {}
    if modo == "reciente":
        ultimo = cliente.ultimo_periodo(endpoint)
        filtros["periodo"] = f"gte.{restar_meses(ultimo, meses_recientes - 1)}"

    esperado = cliente.contar(endpoint, filtros)
    filas = cliente.bajar(endpoint, filtros, conf["clave"], esperado)
    if len(filas) != esperado:
        # puede pasar si el INDEC publica justo mientras bajamos: mejor no guardar algo a medias
        raise ErrorApi(f"{endpoint}: se esperaban {esperado} filas y llegaron {len(filas)}")

    df = validar(pd.DataFrame(filas), conf, nombre)
    return guardar(df, nombre, modo, conf["clave"], carpeta)


def escribir_resumen(resultados: list[Resultado], errores: list[str]) -> None:
    lineas = ["| dataset | ventana | filas | periodos | nueva version |", "|---|---|---|---|---|"]
    for r in resultados:
        nueva = f"si ({r.archivo})" if r.guardado else "no, sin cambios"
        periodos = f"{r.periodo_desde}-{r.periodo_hasta}"
        lineas.append(f"| {r.dataset} | {r.ventana} | {r.filas} | {periodos} | {nueva} |")
    lineas += [f"\n**Error:** {e}" for e in errores]
    texto = "\n".join(lineas)
    log.info("Resumen:\n%s", texto)
    # en GitHub Actions el resumen aparece en la pagina de la corrida
    ruta = os.getenv("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baja datos de la API del INDEC")
    parser.add_argument("--modo", choices=["reciente", "completo"], default="reciente")
    parser.add_argument("--dataset", help="uno solo (por defecto, todos)")
    parser.add_argument("--salida", help="carpeta de salida (por defecto, la de config.yaml)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = cargar_config()
    datasets = config["datasets"]
    if args.dataset and args.dataset not in datasets:
        parser.error(f"dataset desconocido: {args.dataset}. Opciones: {list(datasets)}")

    carpeta = Path(args.salida) if args.salida else RAIZ / config["ingesta"]["carpeta_raw"]
    cliente = ClienteIndec(token=token_indec(), **config["api"])

    resultados, errores = [], []
    for nombre in [args.dataset] if args.dataset else list(datasets):
        log.info("== %s (%s)", nombre, args.modo)
        try:
            resultados.append(
                ingerir(
                    cliente,
                    nombre,
                    datasets[nombre],
                    args.modo,
                    config["ingesta"]["meses_recientes"],
                    carpeta,
                )
            )
        except (ErrorApi, ErrorValidacion) as e:
            # sigo con el resto: que falle uno no tiene por que frenar al otro
            log.error("%s: %s", nombre, e)
            errores.append(f"{nombre}: {e}")

    escribir_resumen(resultados, errores)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
