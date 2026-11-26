import pytest

from monitor.config import cargar_config, token_indec


def test_config_tiene_lo_basico():
    config = cargar_config()
    assert config["api"]["base_url"].startswith("https://")
    assert config["api"]["limite_filas"] == 1000
    assert set(config["datasets"]) == {"ipc", "mayorista"}


def test_cada_dataset_tiene_endpoint_y_orden():
    for dataset in cargar_config()["datasets"].values():
        assert dataset["endpoint"]
        # el orden fijo es lo que evita filas repetidas o perdidas al paginar
        assert "periodo" in dataset["orden"]


def test_token_falta(monkeypatch):
    monkeypatch.setenv("INDEC_API_TOKEN", "")
    monkeypatch.setattr("monitor.config.load_dotenv", lambda *a, **k: None)
    with pytest.raises(RuntimeError):
        token_indec()


def test_token_presente(monkeypatch):
    monkeypatch.setenv("INDEC_API_TOKEN", "abc")
    monkeypatch.setattr("monitor.config.load_dotenv", lambda *a, **k: None)
    assert token_indec() == "abc"
