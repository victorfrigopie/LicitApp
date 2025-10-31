#!/usr/bin/env python3
"""
Sincronizador de licitaciones de la Plataforma de Contratación del Sector Público.

Este script descarga los ficheros comprimidos (ZIP) de la sindicación 643 de
PLACSP, que contienen archivos Atom con las licitaciones completas de los
perfiles del contratante desde 2012 hasta la fecha actual. Recorre cada
archivo Atom, extrae las licitaciones, deduplica por identificador y genera
tres salidas:

* ``data/tenders-active.json``: lista de licitaciones activas (vigentes y con
  fecha límite en el futuro o sin especificar).
* ``data/tenders.ndjson``: archivo NDJSON con todas las licitaciones
  históricas (una entrada por línea).

La variable de entorno ``LICITAI_START_YEAR`` permite ajustar el año de
inicio de descarga (por defecto 2012). La variable ``LICITAI_ACTIVE_ONLY``
determina si se genera también la lista de licitaciones activas (por defecto
``true``).

Uso:

    python scripts/placsp_sync.py

Nota: Este script está pensado para ejecutarse como parte de una GitHub
Action. No necesita argumentos de línea de comandos.
"""

import io
import json
import os
import re
import zipfile
import datetime as dt
from urllib.parse import urljoin

import requests
import xml.etree.ElementTree as ET


# Base de la sindicación para licitaciones de perfiles del contratante
BASE_URL = "https://contrataciondelestado.es/sindicacion/sindicacion_643/"

# Patrones de nombres de fichero ZIP. A lo largo del tiempo han cambiado
# ligeramente. El script probará cada patrón hasta encontrar un ZIP válido.
ZIP_PATTERNS = [
    "licitacionesPerfilesContratanteCompleto3_{ym}.zip",
    "licitacionesPerfilesContratanteCompleta3_{ym}.zip",
    "licitacionesPerfilesContratanteCompleto_{ym}.zip",
    "licitacionesPerfilesContratanteCompleta_{ym}.zip",
]

HEADERS = {"User-Agent": "LicitApp-sync/1.0"}


def month_range(start_year: int) -> list:
    """Genera una lista de cadenas AAAAMM desde start_year hasta el mes actual."""
    today = dt.date.today()
    current_year, current_month = today.year, today.month
    months = []
    for year in range(start_year, current_year + 1):
        for month in range(1, 13):
            if year == current_year and month > current_month:
                break
            months.append(f"{year}{month:02d}")
    return months


def find_existing_zip(ym: str) -> str | None:
    """Dada una cadena AAAAMM devuelve la URL del ZIP que existe, probando patrones."""
    for pattern in ZIP_PATTERNS:
        url = urljoin(BASE_URL, pattern.format(ym=ym))
        try:
            r = requests.head(url, headers=HEADERS, timeout=30, allow_redirects=True)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return None


def iter_atom_entries_from_zip(zip_bytes: bytes):
    """Itera sobre las entradas de los ficheros Atom dentro del ZIP."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        # Buscar el fichero Atom principal (termina en .atom o .xml)
        atom_name = None
        for name in z.namelist():
            if name.endswith(".atom") or name.endswith(".xml"):
                atom_name = name
                break
        if not atom_name:
            return
        content = z.read(atom_name)
        root = ET.fromstring(content)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        # Recorrer las entradas
        for entry in root.findall("a:entry", ns):
            yield entry, ns
        # Si hay paginación, seguir los enlaces "next"
        next_link = root.find("a:link[@rel='next']", ns)
        if next_link is not None:
            next_href = next_link.get("href")
            if next_href:
                try:
                    with z.open(next_href) as next_atom:
                        next_content = next_atom.read()
                    next_root = ET.fromstring(next_content)
                    for entry in next_root.findall("a:entry", ns):
                        yield entry, ns
                except KeyError:
                    pass


def extract_text(elem, tag: str, ns: dict) -> str:
    """Obtiene el texto de la etiqueta tag dentro del elemento XML, devolviendo cadena vacía si no existe."""
    found = elem.find(tag, ns)
    return (found.text or "").strip() if found is not None else ""


def parse_entry(entry, ns: dict) -> dict:
    """Extrae los campos de una entrada Atom en un diccionario."""
    titulo = extract_text(entry, "a:title", ns)
    link_elem = entry.find("a:link", ns)
    enlace = link_elem.get("href") if link_elem is not None else ""
    summary = extract_text(entry, "a:summary", ns)

    def rex(pattern: str) -> str:
        m = re.search(pattern, summary, re.I)
        return m.group(1).strip() if m else ""

    ident = rex(r"Identificador:\s*([^\n<]+)") or enlace or titulo
    organo = rex(r"Órgano de Contratación:\s*([^\n<]+)")
    estado = rex(r"Estado:\s*([^\n<]+)")
    importe = rex(r"Importe(?:\s+de\s+Licitación)?:\s*([0-9\.,]+)")
    cpv = rex(r"CPV:\s*([0-9\- ]+)")
    tipo = rex(r"Tipo de Contrato:\s*([^\n<]+)")
    ccaa = rex(r"CCAA:\s*([^\n<]+)")
    provincia = rex(r"Provincia:\s*([^\n<]+)")
    fpub = rex(r"Fecha de Publicación:\s*([0-9/\-]+)")
    ffin = rex(r"Fecha Límite de Presentación:\s*([0-9/\-: ]+)")

    def to_float(x: str):
        if not x:
            return None
        x = x.replace(".", "").replace(",", ".")
        try:
            return float(x)
        except ValueError:
            return None

    return {
        "id": ident,
        "titulo": titulo,
        "organo": organo,
        "estado": estado,
        "importe": to_float(importe),
        "cpv": cpv,
        "tipo": tipo,
        "ccaa": ccaa,
        "provincia": provincia,
        "fechaPublicacion": fpub,
        "fechaLimite": ffin,
        "enlace": enlace,
        "fuente": "PLACSP",
    }


def is_active(lic: dict) -> bool:
    """Determina si una licitación está activa basada en su estado y fecha límite."""
    estado = (lic.get("estado") or "").lower()
    if "anulada" in estado or "suspend" in estado:
        return False
    # Evaluar fecha límite si está presente
    ffin = lic.get("fechaLimite") or ""
    # Intenta parsear dd/mm/yyyy o similar
    if ffin:
        parts = re.findall(r"\d+", ffin)
        if len(parts) >= 3:
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                fin_date = dt.date(y, m, d)
                if fin_date < dt.date.today():
                    return False
            except Exception:
                pass
    return True


def main():
    start_year = int(os.getenv("LICITAI_START_YEAR", "2012"))
    active_only = os.getenv("LICITAI_ACTIVE_ONLY", "true").lower() == "true"
    out_dir = os.path.join(os.path.dirname(__file__), os.pardir, "data")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    licitaciones = {}
    total_raw = 0

    print(f"Descargando licitaciones desde el año {start_year}…")
    for ym in month_range(start_year):
        url = find_existing_zip(ym)
        if not url:
            continue
        print(f"Descargando {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=120)
            resp.raise_for_status()
            for entry, ns in iter_atom_entries_from_zip(resp.content):
                lic = parse_entry(entry, ns)
                if not lic["id"]:
                    continue
                licitaciones[lic["id"]] = lic
                total_raw += 1
        except Exception as exc:
            print(f"Error al procesar {url}: {exc}")
            continue

    print(f"Total entradas crudas: {total_raw}")
    all_lics = list(licitaciones.values())
    print(f"Total licitaciones únicas: {len(all_lics)}")

    # Guardar NDJSON completo
    ndjson_path = os.path.join(out_dir, "tenders.ndjson")
    with open(ndjson_path, "w", encoding="utf-8") as f:
        for lic in all_lics:
            f.write(json.dumps(lic, ensure_ascii=False) + "\n")
    print(f"Guardado {ndjson_path}")

    if active_only:
        active_lics = [lic for lic in all_lics if is_active(lic)]
        json_path = os.path.join(out_dir, "tenders-active.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(active_lics, f, ensure_ascii=False)
        print(f"Guardado {json_path} con {len(active_lics)} licitaciones activas")


if __name__ == "__main__":
    main()
