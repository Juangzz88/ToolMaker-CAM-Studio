"""
Repara texto UTF-8 dañado (ej. 'ConfiguraciÃ³n' -> 'Configuración').

Uso (desde la raíz del proyecto, con el .venv activado):
    pip install ftfy
    python arreglar_codificacion.py

Antes de modificar cualquier archivo, guarda una copia en la carpeta
_backup_codificacion/ conservando la misma estructura.
"""
import pathlib
import shutil

import ftfy

EXTENSIONES = {".html", ".js", ".css", ".py"}
CARPETAS = ["templates", "static", "engineering", "routes", "validation"]
BACKUP = pathlib.Path("_backup_codificacion")
SALTAR = {"arreglar_codificacion.py"}


def leer_texto(ruta: pathlib.Path) -> str:
    datos = ruta.read_bytes()
    try:
        return datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Archivo guardado en Windows-1252: se decodifica así para no perder texto
        return datos.decode("cp1252", errors="replace")


def main():
    archivos = [pathlib.Path("app.py")]
    for carpeta in CARPETAS:
        base = pathlib.Path(carpeta)
        if base.exists():
            archivos += [p for p in base.rglob("*") if p.is_file() and p.suffix in EXTENSIONES]

    corregidos = 0
    for ruta in archivos:
        if not ruta.exists() or ruta.name in SALTAR:
            continue
        original = leer_texto(ruta)
        arreglado = ftfy.fix_encoding(original)
        if arreglado != original:
            destino = BACKUP / ruta
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ruta, destino)
            ruta.write_bytes(arreglado.encode("utf-8"))
            print("Corregido:", ruta)
            corregidos += 1

    print(f"\nListo. Archivos corregidos: {corregidos}")
    if corregidos:
        print(f"Copias originales en: {BACKUP}/")


if __name__ == "__main__":
    main()