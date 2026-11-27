"""Los informes tecnicos del INDEC, para saber cual fue el primer dato que se publico.

La API solo tiene el dato vigente. Los informes de prensa quedan online tal como salieron,
asi que comparandolos con la API se ve cuanto corrigio el indec despues.

uv run python -m monitor.informes bajar      (necesita llegar a indec.gob.ar)
uv run python -m monitor.informes procesar   (lee los pdf, tarda unos minutos)
"""

import argparse
import hashlib
import logging
import re
import sys
import time

import pandas as pd
from bs4 import BeautifulSoup

from monitor import extraer_pdf
from monitor.cliente import ClienteHttp
from monitor.config import RAIZ

log = logging.getLogger("monitor.informes")

WEB = "https://www.indec.gob.ar"
LISTADO_URL = "Institucional/Indec/InformesTecnicos/32"  # todos los informes, de todos los temas
CARPETA = RAIZ / "data" / "informes"
CARPETA_PDF = CARPETA / "pdf"
LISTADO = CARPETA / "listado.csv"
PRIMEROS_DATOS = CARPETA / "primeros_datos.csv"

# desde cuando los informes usan la misma base que la api
DESDE = {
    "ipm": "2018-03-01",  # base dic-2015, antes era base 1993
    "ipc": "2017-02-01",  # ipc nacional base dic-2016
}
# dos meses del mayorista estan subidos como sipm_ en vez de ipm_
PATRON_PDF = re.compile(r"/uploads/informesdeprensa/s?(ipm|ipc)_(\d{2})_(\d{2})[A-Za-z0-9]*\.pdf$")


def leer_listado(html: str) -> pd.DataFrame:
    """Cada informe es un div.row con la fecha, el titulo, un resumen y el link al pdf."""
    sopa = BeautifulSoup(html, "html.parser")
    filas = []
    for link in sopa.select("div.row a[href$='.pdf']"):
        m = PATRON_PDF.search(link["href"])
        if not m:
            continue
        bloque = link.find_parent("div", class_="row")
        fecha = re.search(r"\d{2}/\d{2}/\d{4}", bloque.get_text(" "))
        titulo = bloque.select_one("span.font-bold")
        copete = bloque.select_one("span.copete")
        filas.append(
            {
                "tipo": m.group(1),
                "publicado": pd.to_datetime(fecha.group(0), dayfirst=True) if fecha else pd.NaT,
                "titulo": titulo.get_text(strip=True) if titulo else "",
                "resumen": copete.get_text(" ", strip=True) if copete else "",
                "url": link["href"],
                "archivo": link["href"].rsplit("/", 1)[1],
            }
        )
    df = pd.DataFrame(filas).drop_duplicates("archivo")
    desde = df["tipo"].map(DESDE).pipe(pd.to_datetime)
    return df[df["publicado"] >= desde].sort_values(["tipo", "publicado"]).reset_index(drop=True)


def bajar(cliente: ClienteHttp | None = None, pausa: float = 1.0) -> pd.DataFrame:
    cliente = cliente or ClienteHttp(WEB, timeout_seg=120)
    cliente.session.headers.update({"User-Agent": "monitor-de-traslado (proyecto personal)"})
    listado = leer_listado(cliente._get(LISTADO_URL, {}).text)
    log.info("%d informes: %s", len(listado), listado["tipo"].value_counts().to_dict())

    CARPETA_PDF.mkdir(parents=True, exist_ok=True)
    hashes = []
    for i, fila in enumerate(listado.itertuples(), 1):
        destino = CARPETA_PDF / fila.archivo
        if not destino.exists():
            log.info("(%d/%d) %s", i, len(listado), fila.archivo)
            destino.write_bytes(cliente._get(fila.url.lstrip("/"), {}).content)
            time.sleep(pausa)  # sin apuro, es la web del indec
        hashes.append(hashlib.sha256(destino.read_bytes()).hexdigest())
    listado["sha256"] = hashes
    listado.to_csv(LISTADO, index=False)
    log.info("listo, %s", LISTADO.relative_to(RAIZ))
    return listado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Informes tecnicos del INDEC")
    parser.add_argument("paso", choices=["bajar", "procesar"])
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.paso == "bajar":
        bajar()
    else:
        extraer_pdf.main([str(CARPETA_PDF), str(PRIMEROS_DATOS)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
