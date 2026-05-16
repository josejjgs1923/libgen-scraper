#!/usr/bin/env python
"""
Descargar Libros de la pagina de genesis library,
usando una query y opciones de busqueda.
"""

from .buscador import BuscadorLibgen
from .cli_parser import conseguir_parser


def main():
    parser = conseguir_parser()

    # procesar opciones
    opts = parser.parse_args()

    # ruta = Path().home() / "pagina.html"

    buscador = BuscadorLibgen()

    opciones = buscador.definir_opciones_busqueda(**opts.__dict__)

    buscador.buscar(opciones)

    buscador.lanzar_fzf()


if __name__ == "__main__":
    main()
