import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]


def cargar_config(ruta: Path | None = None) -> dict:
    ruta = ruta or RAIZ / "config.yaml"
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def token_indec() -> str:
    load_dotenv(RAIZ / ".env")
    token = os.getenv("INDEC_API_TOKEN")
    if not token:
        raise RuntimeError("Falta INDEC_API_TOKEN (en el .env o en los secrets de GitHub)")
    return token
