# Primera mirada a la api antes de armar el pipeline: que codigos trae el ipc y el
# mayorista, desde cuando hay datos y si hay algo de versiones. Deja todo en exploracion/

import json
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("INDEC_API_TOKEN")
if not TOKEN:
    raise SystemExit("Falta INDEC_API_TOKEN en el .env")

BASE = "https://api.indec.gob.ar/v1"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
SALIDA = "exploracion"
os.makedirs(SALIDA, exist_ok=True)

DATASETS = {
    "ipc_nacional": {"codigo": "codigo", "orden": "clasificador,codigo,region,tipo_de_indicador"},
    "sipm_precios_mayoristas": {
        "codigo": "codigo_apertura",
        "orden": "indicador,clasificador,codigo_apertura,region,tipo_de_indicador",
    },
}

resumen = []


def anotar(*partes):
    linea = " ".join(str(p) for p in partes)
    print(linea)
    resumen.append(linea)


def pedir(endpoint, params, extra_headers=None):
    headers = {**HEADERS, **(extra_headers or {})}
    for _ in range(3):
        r = requests.get(f"{BASE}/{endpoint}", headers=headers, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(10)
            continue
        return r
    raise SystemExit("La API sigue tirando 429, probar mas tarde")


def pedir_todo(endpoint, params, orden):
    # mismo orden en todas las paginas
    base = {**params, "order": orden}
    prueba = pedir(endpoint, {**base, "limit": 1})
    if prueba.status_code == 400:
        anotar("  (el orden", orden, "dio 400, sigo sin orden)")
        base = dict(params)
    filas = []
    offset = 0
    while True:
        r = pedir(endpoint, {**base, "limit": 1000, "offset": offset})
        r.raise_for_status()
        pagina = r.json()
        filas += pagina
        if len(pagina) < 1000:
            return pd.DataFrame(filas)
        offset += 1000


# la raiz de postgrest devuelve el openapi con todos los endpoints
r = pedir("", {})
if r.ok and "json" in r.headers.get("Content-Type", ""):
    with open(f"{SALIDA}/openapi.json", "w", encoding="utf-8") as f:
        json.dump(r.json(), f, ensure_ascii=False, indent=2)
    anotar("OpenAPI guardado en exploracion/openapi.json")
else:
    anotar("La raiz no devolvio OpenAPI (status", r.status_code, ")")

for endpoint, conf in DATASETS.items():
    anotar("\n==========", endpoint, "==========")

    # total de filas y headers, por si hay algo de versiones
    r = pedir(endpoint, {"limit": 1}, {"Prefer": "count=exact"})
    r.raise_for_status()
    anotar("Total de filas:", r.headers.get("Content-Range", "sin dato"))
    for h in ["Last-Modified", "ETag", "Cache-Control", "Date"]:
        if h in r.headers:
            anotar(f"Header {h}:", r.headers[h])
    otros = [h for h in r.headers if h.lower().startswith("x-")]
    if otros:
        anotar("Otros headers:", {h: r.headers[h] for h in otros})

    columnas = list(r.json()[0].keys())
    anotar("Columnas:", ", ".join(columnas))
    sospechosas = [
        c
        for c in columnas
        if any(p in c.lower() for p in ["fecha", "version", "publica", "vintage", "actualiz"])
    ]
    anotar("Columnas que podrian ser de version/publicacion:", sospechosas or "ninguna")

    primero = pedir(endpoint, {"select": "periodo", "order": "periodo.asc", "limit": 1}).json()
    ultimo = pedir(endpoint, {"select": "periodo", "order": "periodo.desc", "limit": 1}).json()
    periodo = ultimo[0]["periodo"]
    anotar("Primer periodo:", primero[0]["periodo"], "| Ultimo periodo:", periodo)

    # con el ultimo mes alcanza para ver todos los codigos
    df = pedir_todo(endpoint, {"periodo": f"eq.{periodo}"}, conf["orden"])
    df.to_csv(f"{SALIDA}/{endpoint}_ultimo_mes.csv", index=False, encoding="utf-8")
    anotar("Filas del ultimo mes:", len(df))

    for col in df.columns:
        if col in ("valor", conf["codigo"], "descripcion", "periodo", "anio", "mes"):
            continue
        valores = df[col].value_counts(dropna=False)
        if len(valores) <= 40:
            anotar(f"\n  {col} ({len(valores)} valores):")
            for v, n in valores.items():
                anotar(f"    {v!r}: {n}")

    cols_cat = [
        c
        for c in ["indicador", "clasificador", "nivel", conf["codigo"], "descripcion"]
        if c in df.columns
    ]
    catalogo = df[cols_cat].drop_duplicates().sort_values(cols_cat)
    catalogo.to_csv(f"{SALIDA}/{endpoint}_catalogo.csv", index=False, encoding="utf-8")
    destino = f"exploracion/{endpoint}_catalogo.csv"
    anotar(f"\nCatalogo: {len(catalogo)} combinaciones distintas -> {destino}")

with open(f"{SALIDA}/resumen.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(resumen))
print("\nListo. Pasale la carpeta exploracion/ a Claude.")
