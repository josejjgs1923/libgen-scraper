#!/usr/bin/env python

# import fitz
from pathlib import Path

import argparse

from PIL import Image
from pypdf import PdfReader
from warnings import warn


def iterar_rutas(rutas: list[Path]):
    for ruta in rutas:
        if ruta.is_dir():
            for ruta_int in ruta.iterdir():
                if ruta_int.is_file():

                    yield ruta_int.resolve()

            continue

        yield ruta.resolve()


def hilar(opts):
    imgs = iterar_rutas(opts.imagenes)

    primera_img = next(imgs)

    arch_salida = opts.salida or primera_img

    arch_salida = arch_salida.with_suffix(".pdf")

    with Image.open(primera_img) as img:
        img.save(
            arch_salida,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=[Image.open(ruta) for ruta in imgs],
        )


def transformar(ruta: Path, destino: Path):
    with Image.open(ruta) as img:

        img = img.transpose(Image.Transpose.ROTATE_270)

        img = img.crop((897, 32, 3316, 1870))

        img.save(destino / ruta.name)


def obtener_imagenes_archivo(arch):
    lector = PdfReader(arch)

    for idx, pagina in enumerate(lector.pages):

        try:
            for img in pagina.images:
                yield img
        except ValueError:
            warn(
                f"saltando imagenes en la pagina {idx} de {arch}, por problemas de lectura."
            )
            continue


def extraer(opts):
    archivos = iterar_rutas(opts.imagenes)

    nombre_dir = opts.nombre or opts.imagenes[0].stem

    if opts.salida is None:

        opts.salida = Path(nombre_dir)

        opts.salida.mkdir(exist_ok=True)
    else:
        if not opts.salida.is_dir():
            raise ValueError(f"{opts.salida} tiene que ser una carpeta.")

    if opts.nombre is None:

        def obtener_ruta_img(img, num):

            ruta_img = opts.salida / img.name

            ruta_img = ruta_img.with_stem(f"{ruta_img.stem} {num:03d}")

            return ruta_img

    else:

        def obtener_ruta_img(img, num):

            ruta_img = Path(img.name)

            ruta_img = opts.salida / ruta_img.with_stem(f"{opts.nombre} {num:03d}")

            return ruta_img

    tot_img = 0

    for arch in archivos:

        for idx, img in enumerate(obtener_imagenes_archivo(arch), 1):

            ruta_img = obtener_ruta_img(img, tot_img + idx)

            with ruta_img.open("wb") as wfb:

                wfb.write(img.data)

        tot_img += idx


def conseguir_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="metodos")

    compartidas = argparse.ArgumentParser(add_help=False)

    compartidas.add_argument("imagenes", type=Path, nargs="+")

    compartidas.add_argument("-o", "--out", "--salida", dest="salida", type=Path)

    parser_hilar = subparsers.add_parser(
        "hilar",
        description="juntar imagenes escaneadas en un PDF.",
        parents=[compartidas],
    )

    parser_extraer = subparsers.add_parser(
        "extraer",
        description="extraer todas las imagenes desde un PDF.",
        parents=[compartidas],
    )

    parser_extraer.add_argument("-n", dest="nombre")

    parser_transformar = subparsers.add_parser(
        "transformar",
        description="aplicar transformaciones a conjuntos de imagenes.",
        parents=[compartidas],
    )

    parser_hilar.set_defaults(func=hilar)

    parser_extraer.set_defaults(func=extraer)

    parser_transformar.set_defaults(func=transformar)

    return parser


def main():
    parser = conseguir_parser()

    opts = parser.parse_args()

    opts.func(opts)


if __name__ == "__main__":
    main()
