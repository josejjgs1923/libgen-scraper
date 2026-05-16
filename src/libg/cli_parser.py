#!/usr/bin/env python
"""
Parser de opciones cli para la herramienta
"""

from argparse import REMAINDER, SUPPRESS, ArgumentParser

from .buscador import CATEGORIAS_SORTEO, CATEGORIAS_BUSQUEDA


def conseguir_parser():
    parser = ArgumentParser(description=__doc__)

    # opciones globales

    parser.add_argument(
        "-b",
        "--buscar",
        dest="columna_busqueda",
        default=SUPPRESS,
        choices=CATEGORIAS_BUSQUEDA,
        help=f"La query se interpreta como el vslor de este argumento. Categorias validas son: {', '.join(CATEGORIAS_BUSQUEDA)}. por defecto es titulo (title)",
    )

    # opciones individuales

    parser.add_argument(
        "-n",
        "--numero",
        dest="cantidad_resultados",
        default=SUPPRESS,
        type=int,
        help="Numero de resultados maximo por pagina. Por defecto 100.",
    )

    parser.add_argument(
        "-s",
        "--sortear",
        dest="sorteo",
        default=SUPPRESS,
        choices=CATEGORIAS_SORTEO,
        help="Ordenar resultados por la categoria dada. Categorias validas son:"
        + ", ".join(CATEGORIAS_SORTEO)
        + ". Por defecto titulo (title).",
    )

    parser.add_argument(
        "-r",
        "--invertir",
        dest="orden_sorteo",
        action="store_true",
        help="Invertir orden de resultados, orden descendiente.",
    )

    parser.add_argument(
        "-p",
        "-d",
        "--profundidad",
        dest="profundidad",
        default=10,
        type=int,
        help="Cantidad de paginas resultado a recorrer. por defecto 10.",
    )

    parser.add_argument(
        dest="query",
        nargs=REMAINDER,
        help="Terminos de busqueda para iniciar.",
    )

    return parser


if __name__ == "__main__":
    pass
