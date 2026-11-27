"""Saca de los informes de prensa del INDEC la variacion mensual tal como se publico.

Solo usa re y pdfplumber, sin pandas: asi se puede correr en cualquier maquina que tenga
los pdf, aunque no tenga el entorno del proyecto.

    python -m monitor.extraer_pdf data/informes/pdf data/informes/primeros_datos.csv
    python -m monitor.extraer_pdf data/informes/pdf salida_ipm.csv "ipm_*.pdf"
"""

import csv
import re
import sys
import unicodedata
from pathlib import Path

import pdfplumber

MESES = {
    m: i + 1
    for i, m in enumerate(
        [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]
    )
}
# un numero con coma decimal, o lo que pone el indec cuando no hay dato. en el ipc de 2017
# el cero se escribia con dos rayas largas y el negativo "raya 0,6", por eso eso va primero.
# en el mayorista un guion comun solo es cero ("Tabaco - - -" son tres ceros)
NUM = r"\u2013\s\u2013|(?:[-\u2013\u2212]\s?)?\d+,\d+|///|\.\.\.|[\u2013-]"
REGIONES_IPC = ["Nacional", "GBA", "Pampeana", "Noreste", "Noroeste", "Cuyo", "Patagonia"]
COLUMNAS = ["archivo", "dataset", "periodo", "indicador", "region", "nombre", "valor"]


def normalizar(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", texto)
    sin = "".join(c for c in sin if not unicodedata.combining(c))
    sin = re.sub(r"\(\d\)", "", sin)  # notas al pie: "Recreacion y cultura (1)"
    return re.sub(r"\s+", " ", sin).strip().lower()


def numero(texto: str) -> float | None:
    t = texto.replace("\u2013", "-").replace("\u2212", "-").replace(" ", "")
    if t in ("-", "--"):
        return 0.0  # en los signos del indec la raya sola es "dato igual a cero"
    if t in ("///", "...", ""):
        return None
    return float(t.replace(",", "."))


def mes_del_titulo(texto: str) -> int | None:
    """'Octubre de 2026' -> 202610. Toma la primera fecha que aparece."""
    m = re.search(r"\b(" + "|".join(MESES) + r")\s+de\s+(\d{4})", texto, re.IGNORECASE)
    return int(m.group(2)) * 100 + MESES[m.group(1).lower()] if m else None


def filas_con_numeros(lineas: list[str], cantidad: int) -> list[tuple[str, list[str]]]:
    """Lineas 'nombre n1 n2 ...'. Si el nombre se partio en dos renglones (pasa con
    'Vivienda, agua, electricidad, gas y otros / combustibles'), lo junta."""
    patron = re.compile(rf"^(.*?)\s*((?:(?:{NUM})\s+){{{cantidad - 1}}}(?:{NUM}))\s*$")
    salida = []
    for i, linea in enumerate(lineas):
        m = patron.match(linea.strip())
        if not m:
            continue
        nombre, valores = m.group(1).strip(), re.findall(NUM, m.group(2))
        if len(valores) != cantidad:
            continue
        if not nombre:
            anterior = lineas[i - 1].strip() if i > 0 else ""
            siguiente = lineas[i + 1].strip() if i + 1 < len(lineas) else ""
            sigue_sin_numeros = siguiente and not re.search(r"\d", siguiente)
            nombre = f"{anterior} {siguiente}" if sigue_sin_numeros else anterior
        salida.append((nombre, valores))
    return salida


def leer_mayorista(paginas, archivo: str) -> list[dict]:
    """Cuadro 2: variacion respecto al mes anterior por division, para IPIM, IPIB e IPP."""
    for texto in paginas:
        plano = re.sub(r"\s+", " ", texto)
        titulo = re.search(
            r"Cuadro 2\. Sistema de .ndices de precios mayoristas\. Variaci.n "
            r"porcentual respecto al mes anterior\. (\w+ de \d{4})",
            plano,
            re.I,
        )
        if not titulo or "Nivel general y divisiones" not in texto:
            continue
        periodo = mes_del_titulo(titulo.group(1))
        lineas = texto.splitlines()
        desde = next(i for i, ln in enumerate(lineas) if ln.startswith("Nivel general y div"))
        filas = []
        for nombre, valores in filas_con_numeros(lineas[desde:], 3):
            for indicador, v in zip(["IPIM", "IPIB", "IPP"], valores, strict=True):
                filas.append(
                    {
                        "archivo": archivo,
                        "dataset": "mayorista",
                        "periodo": periodo,
                        "indicador": indicador,
                        "region": "Total del pais",
                        "nombre": normalizar(nombre),
                        "valor": numero(v),
                    }
                )
            if normalizar(nombre) == "productos importados":
                break
        return filas
    return []


def leer_ipc(paginas, archivo: str) -> list[dict]:
    """Cuadro 1: variacion respecto al mes anterior por division, nacional y 6 regiones.
    Los informes de principios de 2017 son solo de GBA con otras categorias: se saltean."""
    for texto in paginas:
        # en 2017 la region se llamaba "Patagonica"
        if not re.search(r"Cuadro 1\.", texto) or "Patag" not in texto:
            continue
        # en 2021 el encabezado sale partido: "Nivel general y / Nacional / divisiones"
        if not re.search(r"Nivel general y\s+(?:Nacional\s+)?divisiones", texto):
            continue
        cabecera = re.search(r".ndice de precios al consumidor\s*\n\s*(\w+ de \d{4})", texto, re.I)
        periodo = mes_del_titulo(cabecera.group(1) if cabecera else texto)
        lineas = texto.splitlines()
        desde = next(i for i, ln in enumerate(lineas) if ln.startswith("Nivel general y"))
        hasta = next(
            (i for i, ln in enumerate(lineas) if i > desde and ln.startswith(("Fuente", "(1)"))),
            len(lineas),
        )
        filas = []
        for nombre, valores in filas_con_numeros(lineas[desde:hasta], 7):
            # en diciembre abajo viene la variacion del anio con el mismo formato: corto ahi
            if normalizar(nombre) == "nivel general" and filas:
                break
            for region, v in zip(REGIONES_IPC, valores, strict=True):
                filas.append(
                    {
                        "archivo": archivo,
                        "dataset": "ipc",
                        "periodo": periodo,
                        "indicador": "IPC",
                        "region": region,
                        "nombre": normalizar(nombre),
                        "valor": numero(v),
                    }
                )
        return filas
    return []


def leer(ruta: Path) -> list[dict]:
    lector = leer_mayorista if ruta.name.startswith(("ipm_", "sipm_")) else leer_ipc
    with pdfplumber.open(ruta) as pdf:
        # pagina por pagina: el cuadro esta al principio y los graficos tardan mucho en leerse
        paginas = (p.extract_text() or "" for p in pdf.pages)
        return lector(paginas, ruta.name)


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    carpeta, salida = Path(args[0]), Path(args[1])
    patron = args[2] if len(args) > 2 else "*.pdf"  # para correrlo por partes
    filas, vacios = [], []
    for ruta in sorted(carpeta.glob(patron)):
        leidas = leer(ruta)
        filas += leidas
        if not leidas:
            vacios.append(ruta.name)
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} filas de {len(list(carpeta.glob(patron))) - len(vacios)} informes")
    print(f"sin cuadro reconocible: {len(vacios)} {vacios}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
