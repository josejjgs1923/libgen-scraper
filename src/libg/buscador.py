#!/usr/bin/env python
"""
Clase BuscadorLibgen, encargada de Descargar y procesar el html,
y descargar los links encontrados
"""

# from asyncio import get_event_loop
from pathlib import Path
from re import compile
from typing import Any, Optional
from urllib.parse import urljoin
from iterfzf import iterfzf

from bs4 import BeautifulSoup

from system_admin.files import Rutas
from scrapear import Descargador

numeros_iniciales = compile(r"^\d+")

CATEGORIAS_BUSQUEDA = (
    "author",
    "title",
    "publisher",
    "year",
    "isbn",
    "language",
    "md5",
    "tags",
    "extension",
)

CATEGORIAS_SORTEO = (
    "id",
    "author",
    "title",
    "publisher",
    "year",
    "pages",
    "language",
    "filesize",
    "extension",
)



class BuscadorLibgen:
    CARACTERES_ESPACIO_RE = compile(r"\r")

    MIRROR = "https://libgen.li"

    ENLACE_BUSQUEDA = MIRROR + "/" + "index.php"

    ENLACE_DESCARGA = "https://libgen.li"

    CATEGORIAS_BUSQUEDA = CATEGORIAS_BUSQUEDA

    CATEGORIAS_SORTEO = CATEGORIAS_SORTEO 

    ATTR_RESULTADOS = (
        "titulo",
        "autor",
        "publicador",
        "fecha",
        "idioma",
        "paginas",
        "tamaño",
        "extension",
        "links",
    )

    SEP_FIELD = "\t"

    def __init__(
        self,
        desde_archivo: Optional[Path] = None,
    ):
        self.desc = Descargador()

        self.EXTRA_FZF = (
            "-d",
            self.SEP_FIELD,
            "--with-nth",
            "1",
            "--preview-window",
            "up,40%",
        )

        if desde_archivo is not None:
            with desde_archivo.open("rb") as rfile:
                self.sopa = BeautifulSoup(rfile.read(), "html.parser")

            self.resp = None

    @staticmethod
    def definir_opciones_busqueda(
        query: list[str],
        columna_busqueda: str = "title",
        orden_sorteo: bool = True,
        cantidad_resultados: int = 100,
        sorteo: str = "title",
        pagina: Optional[int] = None,
        **_,
    ):
        opciones = {
            "req": " ".join(query),
            "columns": columna_busqueda,
            "res": cantidad_resultados,
            "sort": sorteo,
            "sortmode": "ASC" if orden_sorteo else "DESC",
        }

        if pagina is not None:
            opciones["page"] = pagina

        return opciones

    def buscar(self, opciones_busqueda: dict[str, Any]):
        self.resp = self.desc.get(self.ENLACE_BUSQUEDA, opciones_busqueda)

        self.sopa: BeautifulSoup = BeautifulSoup(self.resp.content, "html.parser")

    def yield_entradas(self):
        self.resultados = []

        tbodys = self.sopa.find_all("tbody")

        if len(tbodys) == 0:
            raise SystemExit("No hay resultados para la busqueda.")
        if len(tbodys) > 1:
            seccion_res = tbodys[1]
        else:
            seccion_res = tbodys[0]

        for tr in seccion_res.find_all("tr"):
            resultados = dict()

            titulo_con, *attr_cons, links_con = tr.find_all("td")

            atag_posible = titulo_con.find("a", recursive=False)

            try:
                resultados[self.ATTR_RESULTADOS[0]] = "".join(atag_posible.strings)

            except AttributeError:
                atags = titulo_con.find_all("a")

                resultados[self.ATTR_RESULTADOS[0]] = "".join(
                    "".join(atag.strings).strip() for atag in atags
                ).strip()

            for atr, con in zip(self.ATTR_RESULTADOS[1:-1], attr_cons):
                resultados[atr] = con.string

            resultados[self.ATTR_RESULTADOS[-1]] = urljoin(
                self.ENLACE_BUSQUEDA, links_con.find("a")["href"]
            )

            self.resultados.append(resultados)

            yield resultados

    def formato_presentacion(self, atributos: dict[str, Any]):
        for atr in self.ATTR_RESULTADOS[:-1]:
            valor = atributos[atr]

            if valor is None:
                yield ""

                continue

            valor = self.CARACTERES_ESPACIO_RE.sub("", valor.strip())

            yield f"{atr:<10}: {valor}"

    def yield_entradas_formato(self):
        for idx, entrada in enumerate(self.yield_entradas(), 1):
            pres = "\\n".join(self.formato_presentacion(entrada))

            yield self.CARACTERES_ESPACIO_RE.sub(
                "", f"{idx:03d} {entrada['titulo']:.30s}... | {entrada['autor']}"
            ) + self.SEP_FIELD + pres

    def lanzar_fzf(self):
        seleccion = iterfzf(
            self.yield_entradas_formato(),
            multi=True,
            preview="echo {2}",
            __extra__=self.EXTRA_FZF,
        )

        if seleccion is None:
            raise SystemExit("Nada Seleccionado")

        enlaces = []

        for entrada in seleccion:
            idx = int(entrada[:3]) - 1  # type: ignore

            res = self.resultados[idx]

            resp = self.desc.get(res["links"])

            sopa = BeautifulSoup(resp.content, "html.parser")

            try:
                enlace = urljoin(
                    self.ENLACE_DESCARGA, sopa.find("tr").a["href"]  # type:ignore
                )

            except AttributeError:
                print(f"enlace descarga no hallado para {res['links']}")

                continue

            else:
                enlaces.append(enlace)

                try:
                    self.desc(enlace, Rutas.DL.value / res["titulo"])

                except KeyboardInterrupt:
                    print("descarga interrumpida. Enlaces obtenidos hasta ahora:")

                    for enlace in enlaces:
                        print(enlace)



if __name__ == "__main__":
    pass
