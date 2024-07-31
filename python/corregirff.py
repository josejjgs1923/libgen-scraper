#!/usr/bin/env python
"""
eliminar los ssltos de linea de windows, que contienen caracteres de retorno, en archivos.
"""
from pathlib import Path
import argparse


def eliminar_CR(arch: Path):
    with arch.open("rb+") as rfile:

        contenido = rfile.read()

        rfile.seek(0)

        rfile.write(contenido.replace(b"\r", b""))

        rfile.truncate()


def conseguir_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "ruta",
        type=Path,
        nargs="+",
        help="nombre de archivo o de carpeta. si es una carpeta, se iterara sobre los archivos y se eliminara el salto de retorno.",
    )

    return parser


def main():
    parser = conseguir_parser()

    opts = parser.parse_args()

    for ruta in opts.ruta:

        if ruta.is_dir():

            for arch in ruta.iterdir():

                eliminar_CR(arch)

        else:

            eliminar_CR(ruta)


if __name__ == "__main__":
    main()
