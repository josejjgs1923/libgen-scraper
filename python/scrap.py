#!/usr/bin/env python
"""
Programa de escrapeo web. capaz de descargar imagenes u obtener sus links desde
varias paginas web. diseñado para funcionar en ciertas paginas web especificas.
"""

from collections.abc import Callable
from itertools import count
from math import log, ceil
from pathlib import Path
from re import compile
from typing import Any, Iterator, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
import requests
from tqdm import tqdm

from recetas.recetas_argparse import ParserArgumentosSeguidores
from system_admin.files import Rutas

nombre_sitio = compile(r"https:\/\/(?:www\.)?([^\/]*)\..*\/")

numeros_iniciales = compile(r"^\d+")


# clases principales para descargar imagenes y procesar el html


class Descargador:
    verdadero_suffix = compile(r"\.\w+")

    def __init__(self, headers=None):

        self.headers = (
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
            }
            if headers is None
            else headers
        )

    def get(self, url: str):

        resp = requests.get(url, headers=self.headers)

        resp.raise_for_status()

        return resp

    def __call__(self, url: str, nombre: str, ruta: Path):

        resp = self.get(url)

        try:
            contenido = resp.headers["Content-Type"]

            verdadero_suffix = "." + contenido.split("/")[1]

        except KeyError:
            ruta_provisional = Path(url)

            verdadero_suffix = self.verdadero_suffix.search(ruta_provisional.suffix)
            if verdadero_suffix is None:

                raise ValueError(
                    f"el link {url} no pudo ser conseguido: no tiene tipo contenido o extension valida."
                )

            verdadero_suffix = verdadero_suffix[0]

        finally:
            ruta_imagen = ruta / (nombre + verdadero_suffix)

        with ruta_imagen.open("wb") as wf:

            wf.write(resp.content)


class _RaspadorBasico:
    eliminar_extra_espacios = compile(r" {2,}")
    eliminar_caracteres_indeseados = compile(r"[.<>:\"/\\|?*]")

    def __init__(
        self,
        url: str,
        simular: bool,
        nombre: Optional[str],
        crear_carpeta: bool,
        ruta: Path,
    ):

        self.nombre: Optional[str] = nombre
        self.url: str = url
        self.sopa: Optional[BeautifulSoup] = None
        self.es_simulacion = simular
        self.crear_carpeta: bool = crear_carpeta
        self.ruta: Path = ruta

        self.descargador = Descargador()

    @staticmethod
    def numero_cifras(num: int):

        return ceil(log(num, 10))

    def conseguir_nombre(self) -> str:

        raise NotImplementedError(
            "se debe heredar, e implementar metodo de conseguir_nombre"
        )

    def simular(self):

        raise NotImplementedError("se debe heredar, e implementar metodo de simular")

    def descargar_iterable(self, iterable: Iterator[str]):
        imagenes = tuple(iterable)

        cifras = self.numero_cifras(len(imagenes))

        assert self.nombre is not None

        formato_nombre = self.nombre + " {" + f":0{cifras}d" + "}"  # type: ignore

        barra_progreso = tqdm(imagenes, desc=f"descargando: {self.url}", unit="img")

        for idx, url in enumerate(barra_progreso, 1):

            url_resuelta = urljoin(self.url, url)

            self.descargador(url_resuelta, formato_nombre.format(idx), self.ruta)

    def descargar_imagenes(self):

        raise NotImplementedError(
            "se debe heredar, e implementar metodo de descargar_imagenes"
        )

    def definir_nombre(self) -> None:

        if self.nombre is None:

            nombre_crudo = self.conseguir_nombre().strip()

            nombre_crudo = self.eliminar_caracteres_indeseados.sub("", nombre_crudo)

            nombre_crudo = self.eliminar_extra_espacios.sub(" ", nombre_crudo)

            self.nombre = nombre_crudo

    def conseguir_sopa(self, url: str) -> BeautifulSoup:

        resp = self.descargador.get(url)

        return BeautifulSoup(resp.content, "html.parser")

    def definir_carpeta(self):
        if self.crear_carpeta:

            self.ruta = self.ruta / self.nombre  # type: ignore

            self.ruta.mkdir(exist_ok=True)

    def definir_info_pagina(self):

        self.definir_nombre()

    def run(self):

        self.sopa = self.conseguir_sopa(self.url)

        self.definir_info_pagina()

        if self.es_simulacion:

            self.simular()

        else:
            self.definir_carpeta()

            self.descargar_imagenes()


class RasparTablero(_RaspadorBasico):
    def conseguir_imagenes(self) -> Iterator[str]:

        raise NotImplementedError(
            "se debe heredar, e implementar metodo de conseguir_imagenes"
        )

    def simular(self):

        print("el nombre conseguido es:", self.nombre, flush=True)

        if self.crear_carpeta:

            assert self.nombre is not None

            ruta_simulada = self.ruta / self.nombre

            print(
                f"se crearia una carpeta con el nombre: {ruta_simulada.name}, en {ruta_simulada!r}"
            )

        print("link conseguidos:", flush=True)

        contador = 0

        for url in self.conseguir_imagenes():

            print(urljoin(self.url, url), flush=True)

            contador += 1

        print(f"total imagenes: {contador}")

    def descargar_imagenes(self):

        self.descargar_iterable(self.conseguir_imagenes())


class RasparConjuntoTableros(_RaspadorBasico):
    def raspar_pagina_inicial(self) -> bool:

        return True

    def seguir_pagina(
        self,
        base_url: str,
        url: str,
        conseguir_urls: Callable[[str, BeautifulSoup], Iterator[str]],
    ):

        url_resuelta = urljoin(base_url, url)

        sopa = self.conseguir_sopa(url_resuelta)

        yield from conseguir_urls(url_resuelta, sopa)

    def conseguir_tableros(self) -> Iterator[str]:

        raise NotImplementedError(
            "se debe heredar e implementar metodo conseguir_tableros"
        )

    def conseguir_contenido_tableros(self):

        if self.raspar_pagina_inicial():

            yield self.url, self.sopa

        for url in self.conseguir_tableros():

            url_resuelta = urljoin(self.url, url)

            sopa = self.conseguir_sopa(url_resuelta)

            yield url_resuelta, sopa

    @staticmethod
    def conseguir_imagenes(
        contenido: BeautifulSoup,
    ) -> Iterator[str]:  # type: ignore

        raise NotImplementedError(
            "se debe heredar y crear un metodo de conseguir_imagenes_tablero"
        )

    def simular(self):

        print("el nombre conseguido es:", self.nombre, flush=True)

        if self.crear_carpeta:
            assert self.nombre is not None

            ruta_simulada = self.ruta / self.nombre

            print(
                f"se crearia una carpeta con el nombre: {ruta_simulada.name}, en {ruta_simulada!r}"
            )

        print("link conseguidos:", flush=True)

        contador = 0

        for base_url, contenido in self.conseguir_contenido_tableros():

            for url in self.conseguir_imagenes(contenido):  # type: ignore

                print(urljoin(base_url, url), flush=True)

                contador += 1

        print(f"total imagenes: {contador}")

    def conseguir_imagenes_completas(self):
        for base_url, contenido in self.conseguir_contenido_tableros():
            try:

                for url in self.conseguir_imagenes(contenido):  # type: ignore
                    yield urljoin(base_url, url)

            except TypeError:
                continue

    def descargar_imagenes(self):

        self.descargar_iterable(self.conseguir_imagenes_completas())


# descargadores especificos de paginas:


class E621(RasparConjuntoTableros):
    regex_pagina = compile(r"(.*)page=(\d+)")

    def conseguir_tags_comunes(self):
        assert self.sopa is not None

        self.posts_container = self.sopa.find("div", id="posts-container")

        self.div_parent_child = self.sopa.find("div", {"class": "parent-children"})

        self.span_pool_name = self.sopa.find("span", {"class": "pool-name"})

        self.attrs_parent = {"class": "notice notice-child"}

        self.attrs_child = {"class": "notice notice-parent"}

    def raspar_pagina_inicial(self):

        if self.posts_container is None:

            if self.div_parent_child is None:

                if self.span_pool_name is None:
                    return True

            return False

        return False

    @staticmethod
    def conseguir_imagenes(
        contenido: Optional[BeautifulSoup],
    ) -> Iterator[str]:
        assert contenido is not None

        container = contenido.find("section", {"id": "image-container"})

        yield container.img["src"]  # type: ignore

    def conseguir_nombre(self) -> str:
        assert self.sopa is not None

        if self.posts_container is None:

            if self.span_pool_name is None:

                section_tag = self.sopa.find("section", id="tag-list")

                atag = section_tag.find("a", {"class": "search-tag"})  # type: ignore

                return atag.string  # type: ignore

            else:

                return self.span_pool_name.a.string.replace("Pool: ", "")  # type: ignore

        else:

            div = self.sopa.find("div", id="a-show")

            assert div is not None

            return div.h2.a.string  # type: ignore

    @staticmethod
    def conseguir_posts_pool(url: str, sopa: BeautifulSoup):
        container = sopa.find("div", id="posts-container")

        if container is not None:

            for atag in container.find_all("a"):  # type: ignore

                yield atag["href"]

    def conseguir_paginas_pool(self, sopa: BeautifulSoup):
        paginador = sopa.find("div", {"class": "paginator"})

        assert paginador is not None

        menu = paginador.find("menu")

        assert menu is not None

        pagina_actual = menu.find("li", {"class": "current-page"})  # type: ignore

        # print(f"{menu=}")
        # print(f"{pagina_actual=}")

        if pagina_actual is not None:

            # print("si se encontro pagina_actual")

            paginas_numeradas = menu.find_all(  # type: ignore
                "li", {"class": "numbered-page"}
            )  # type: ignore

            if paginas_numeradas:

                # print("se encontro paginas numeradas")

                puntos_mas = menu.find("li", {"class": "more"})  # type: ignore

                for li in paginas_numeradas[:-1]:
                    yield li.a["href"]

                if puntos_mas is None:
                    yield paginas_numeradas[-1].a["href"]
                else:
                    plantilla_pagina = paginas_numeradas[0].a["href"]

                    numero_penultima_numerada = int(paginas_numeradas[-2].a.string)

                    numero_ultima_numerada = int(paginas_numeradas[-1].a.string)

                    for numero in range(
                        numero_penultima_numerada + 1,
                        numero_ultima_numerada + 1,
                    ):

                        yield self.regex_pagina.sub(
                            r"\1page=" + str(numero), plantilla_pagina
                        )

    def encontrar_parent_posts(self, url_child: str, tag: Tag):
        articulo = tag.find("article")

        assert articulo is not None

        yield urljoin(url_child, articulo.a["href"])  # type: ignore

    def encontrar_child_posts(self, url_parent: str, tag: Tag):
        for articulo in tag.find_all("article"):

            yield urljoin(url_parent, articulo.a["href"])

    def encontrar_sibling_posts(self, url: str, url_parent: str, tag: Tag):
        for url_sibling in self.encontrar_child_posts(url_parent, tag):

            url_unida = urljoin(url_parent, url_sibling)

            if url not in url_unida:

                yield url_unida

        # print(urls_sibling)

        # print(url)

    def conseguir_parent_posts(self, url: str, sopa: BeautifulSoup):
        div_parent = sopa.find("div", self.attrs_parent)

        if div_parent is not None:

            for url_parent in self.encontrar_parent_posts(url, div_parent):  # type: ignore

                sopa_parent = self.conseguir_sopa(url_parent)

                div_child_from_parent = sopa_parent.find("div", self.attrs_child)

                yield from self.conseguir_parent_posts(url_parent, sopa_parent)

                yield url_parent

                yield from self.encontrar_sibling_posts(
                    url, url_parent, div_child_from_parent  # type: ignore
                )

    def conseguir_child_posts(self, url: str, sopa: BeautifulSoup):
        div_child = sopa.find("div", self.attrs_child)

        if div_child is not None:

            for url_child in self.encontrar_child_posts(url, div_child):  # type: ignore

                sopa_child = self.conseguir_sopa(url_child)

                yield url_child

                yield from self.conseguir_child_posts(url_child, sopa_child)

    def conseguir_posts_relacionados(self, url: str, sopa: BeautifulSoup):
        yield from self.conseguir_parent_posts(url, sopa)

        yield url

        yield from self.conseguir_child_posts(url, sopa)

    def conseguir_pool_completa(self, url: str, primera_sopa_pool: BeautifulSoup):
        yield from self.conseguir_posts_pool("", primera_sopa_pool)

        for url in self.conseguir_paginas_pool(primera_sopa_pool):

            yield from self.seguir_pagina(self.url, url, self.conseguir_posts_pool)

    def conseguir_tableros(self) -> Iterator[str]:
        assert self.sopa is not None

        if self.posts_container is None:

            if self.span_pool_name is None:

                if self.div_parent_child is not None:

                    yield from self.conseguir_posts_relacionados(self.url, self.sopa)

            else:

                yield from self.seguir_pagina(
                    self.url,
                    self.span_pool_name.a["href"],  # type: ignore
                    self.conseguir_pool_completa,
                )

        else:

            yield from self.conseguir_pool_completa("", self.sopa)

    def definir_info_pagina(self):
        self.conseguir_tags_comunes()

        super().definir_info_pagina()


class U18Chan(RasparTablero):
    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        div_user = self.sopa.find("div", {"class": "UserDetails"})

        assert div_user is not None

        span = div_user.find("span", {"class": "Subject"})  # type: ignore

        assert span is not None

        return span.string  # type: ignore

    def conseguir_imagenes(self) -> Iterator[str]:

        assert self.sopa is not None

        primera = self.sopa.find("div", id="FirstPost")

        assert primera is not None

        yield primera.a["href"]  # type: ignore

        for td in self.sopa.find_all("td", {"class": "ReplyContentOuterImage"}):

            assert td is not None

            yield td.a["href"]


class Xlecx(RasparTablero):
    re_src = compile(r"src")

    def conseguir_nombre(self) -> str:
        assert self.sopa is not None

        h1 = self.sopa.find("h1")

        assert h1 is not None

        return h1.string  # type: ignore

    def conseguir_imagenes(self) -> Iterator[str]:
        assert self.sopa is not None

        try:

            div_content = self.sopa.find("div", align="center")

            imgs_tags = div_content.find_all("img")  # type: ignore

            assert len(imgs_tags) > 0

            for tag in imgs_tags:

                attri = next(
                    (key for key in tag.attrs.keys() if self.re_src.search(key)), None
                )

                if attri is None:
                    raise TypeError(
                        f"no se encontro source attribute in {self.__class__}"
                    )

                yield tag[attri]

        except (AttributeError, AssertionError):

            div_centers = self.sopa.find_all("div", style=compile(r"text-align:(.*);"))

            for div in div_centers:

                atags = div.find_all("a")

                for atag in atags:

                    assert atag is not None

                    yield atag["href"]


class Yiffer(RasparTablero):
    parte_estatica_url = "https://static.yiffer.xyz/comics/"

    def conseguir_nombre(self) -> str:

        nombre_solo = nombre_sitio.sub("", self.url)

        nombre = nombre_solo.replace("%20", " ")

        return nombre

    def descargar_imagenes(self):

        formato_url = f"{self.parte_estatica_url}{self.nombre}" + "/{:03d}.jpg"

        formato_nombre = f"{self.nombre} " + "{:03d}"

        for idx in count(1):

            try:

                self.descargador(
                    formato_url.format(idx),
                    formato_nombre.format(idx),
                    self.ruta,
                )

            except requests.HTTPError:
                break

    def simular(self):

        print("el nombre conseguido es:", self.nombre, flush=True)

        print("link conseguidos:", flush=True)

        print(f"plantilla para imagenes: {self.parte_estatica_url}{self.nombre}//.jpg")

    def run(self):

        self.definir_nombre()

        self.definir_carpeta()

        if self.es_simulacion:

            self.simular()

        else:

            self.descargar_imagenes()


class Welqum(RasparTablero):
    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        div_title = self.sopa.find("div", id="comicTitle")

        assert div_title is not None

        return div_title.h1.string  # type: ignore

    def conseguir_imagenes(self) -> Iterator[str]:

        assert self.sopa is not None

        maincontent: Tag = self.sopa.find("div", id="mainContentComic")  # type: ignore

        assert maincontent is not None

        for img in maincontent.find_all("img"):

            assert img is not None

            yield img["src"]


class Allporncomic(RasparConjuntoTableros):
    def raspar_pagina_inicial(self) -> bool:
        return False

    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        h1 = self.sopa.find("h1")

        assert h1 is not None

        return h1.string  # type: ignore

    @staticmethod
    def conseguir_imagenes(
        contenido: Optional[BeautifulSoup],
    ) -> Iterator[str]:

        content = contenido.find("div", {"class": "reading-content"})  # type: ignore

        assert content is not None

        for img in content.find_all("img"):  # type: ignore

            assert img is not None

            yield img["data-src"]

    def conseguir_tableros(self) -> Iterator[str]:

        assert self.sopa is not None

        botones = self.sopa.find("div", id="init-links")

        if botones is None:
            selector = self.sopa.find(
                "select", {"class": "selectpicker single-chapter-select"}
            )

            if selector is not None:
                for option in reversed(tuple(selector.find_all("option"))):  # type: ignore

                    yield option["data-redirect"]

        else:
            div_listing = self.sopa.find(
                "div", {"class": "page-content-listing single-page"}
            )

            assert div_listing is not None

            for atag in reversed(
                tuple(atag for atag in div_listing.find_all("a"))  # type: ignore
            ):

                yield atag["href"]


class Theyiffgallery(RasparConjuntoTableros):
    def raspar_pagina_inicial(self) -> bool:
        return False

    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        img = self.sopa.find("img", id="theMainImage")

        if img is None:
            h2 = self.sopa.find("h2")

            assert h2 is not None

            lista_lugares = tuple(atag.string for atag in h2.find_all("a"))  # type: ignore

        else:

            browse = self.sopa.find("div", {"class": "browsePath"})

            lista_lugares = tuple(atag.string for atag in browse.find_all("a"))  # type: ignore

        return lista_lugares[-1]

    @staticmethod
    def conseguir_imagenes(contenido: BeautifulSoup) -> Iterator[str]:

        img = contenido.find("img", id="theMainImage")

        assert img is not None

        yield img["src"]  # type: ignore

    @staticmethod
    def conseguir_paginas_capitulo(url: str, sopa: BeautifulSoup):

        posible_lista_posts = sopa.find("ul", id="thumbnails")

        if posible_lista_posts is not None:

            for atag in posible_lista_posts.find_all("a"):  # type: ignore

                yield atag["href"]

    def conseguir_tableros(self) -> Iterator[str]:

        assert self.sopa is not None

        posible_lista_capitulos = self.sopa.find(
            "ul", {"class": "thumbnailCategories thumbnails nowrap"}
        )

        if posible_lista_capitulos is None:

            img = self.sopa.find("img", id="theMainImage")

            if img is None:

                yield from self.conseguir_paginas_capitulo("", self.sopa)

            else:
                browse = self.sopa.find("div", {"class": "browsePath"})

                lista_lugares = tuple(atag for atag in browse.find_all("a"))  # type: ignore

                yield from self.seguir_pagina(
                    self.url,
                    lista_lugares[-1]["href"],
                    self.conseguir_paginas_capitulo,
                )

        else:

            for atag in posible_lista_capitulos.find_all("a"):  # type: ignore#type: ignore

                yield from self.seguir_pagina(
                    self.url, atag["href"], self.conseguir_paginas_capitulo
                )


class Ilikecomix(RasparTablero):
    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        h1 = self.sopa.find("h1")

        return h1.string  # type: ignore

    def conseguir_imagenes(self) -> Iterator[str]:

        assert self.sopa is not None

        contenido = self.sopa.find("div", id="dgwt-jg-1")

        assert contenido is not None

        for atag in contenido.find_all("a"):  # type: ignore

            yield atag["href"]


class Vercomicsporno(RasparTablero):
    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        h2 = self.sopa.find("h2")

        assert h2 is not None

        return h2.string  # type: ignore

    def conseguir_imagenes(self):

        assert self.sopa is not None

        columna = self.sopa.find("div", {"class": "main-col-inner"})

        for div in columna.find_all("div", {"class": "wp-block-image"}):  # type: ignore

            yield div.img["src"]


class Mult34(RasparTablero):
    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        h1 = self.sopa.find("h1")

        return h1.string  # type: ignore

    def conseguir_imagenes(self) -> Iterator[str]:

        assert self.sopa is not None

        div_galeria = self.sopa.find("div", id="gallery-2")

        assert div_galeria is not None

        for dl in div_galeria.find_all("dl"):  # type: ignore

            yield dl.dt.img["src"]


class Muses(RasparConjuntoTableros):

    re_fin_url = compile(r"\/([^\/]*)$")

    re_numerado = compile(r"\s\d+")

    def conseguir_tags_comunes(self):

        assert self.sopa is not None

        self.seccion_paginador = self.sopa.find("section", id="pagination-page-top")

        self.galeria = self.sopa.find("div", {"class": "gallery"})

        if self.galeria is not None:

            self.atags: Iterator[Tag] = (atag for atag in self.galeria.find_all("a"))  # type: ignore

            self.primer_atag = next(self.atags)

            self.primer_div = self.primer_atag.div

    def raspar_pagina_inicial(self):
        return False

    def conseguir_nombre(self) -> str:

        if self.galeria is None:

            re_numerado = compile(r"-\d+")

            partes = self.url.split("/")

            partes.pop()

            if re_numerado.search(partes[-1]):

                return " ".join(parte.strip() for parte in partes[-2:])

            else:

                return partes[-1]

        else:

            div_menu = self.sopa.find("div", {"class": "top-menu-breadcrumb"})  # type: ignore

            posibles_nombres = [atag.string for atag in div_menu.find_all("a")]  # type: ignore

            if (not self.primer_div.has_attr("itemtype")) and self.re_numerado.search(posibles_nombres[-1]):  # type: ignore

                return " ".join(nombre.strip() for nombre in posibles_nombres[-2:])

            else:

                return posibles_nombres[-1]

    def conseguir_imagenes(self, contenido: BeautifulSoup):  # type: ignore

        galeria = contenido.find("div", {"class": "gallery"})

        assert galeria is not None

        for img in galeria.find_all("img"):  # type: ignore

            url_cruda = img["src"]

            encontrado = self.re_fin_url.search(url_cruda)

            if encontrado is not None:

                if encontrado[0] != "/":

                    yield self.re_fin_url.sub(
                        "/" + encontrado[1].replace("th", "full"), url_cruda
                    )

    @staticmethod
    def conseguir_paginas(url: str, contenido: BeautifulSoup):

        nav = contenido.find("nav", {"class": "pagination"})

        if nav is not None:
            spans = nav.find_all("span")  # type: ignore

            spans.pop()
            spans.pop()

            spans.pop(0)
            spans.pop(0)

            for span in spans:

                atag = span.a

                if atag is None:

                    yield url

                else:

                    yield atag["href"]
        else:

            yield url

    def conseguir_tableros(self) -> Iterator[str]:

        assert self.sopa is not None

        if self.seccion_paginador is None:

            assert self.primer_div is not None

            assert self.atags is not None

            assert self.primer_atag is not None

            if self.primer_div.has_attr("itemtype"):

                yield self.primer_atag["href"]  # type: ignore

                for atag in self.atags:

                    yield atag["href"]  # type: ignore

            else:

                yield from self.seguir_pagina("", self.url, self.conseguir_paginas)
        else:

            url_tablero = self.re_fin_url.sub("", self.url).replace(
                "picture/", "album/"
            )

            yield from self.seguir_pagina(self.url, url_tablero, self.conseguir_paginas)

    def definir_info_pagina(self):

        self.conseguir_tags_comunes()

        super().definir_info_pagina()


class Rule34(RasparConjuntoTableros):

    es_palabra = compile(r"\w")

    dominio_sitio = compile(r"https:\/\/[^\/]*\.([^\/]*)\/")

    tipos_video = ("video/mp4", "video/webm")

    def raspar_pagina_inicial(self) -> bool:

        return self.lista_posts is None

    def conseguir_tags_comunes(self):

        encontrado = self.dominio_sitio.search(self.url)

        if encontrado is None:

            raise ValueError(f"version desconocida de Rule34: {self.url}")

        match encontrado[1]:

            case "xxx":

                clase_container = "image-list"

                tag_contenido = ("div", "flexi", True, True)

                tag_container = (
                    "ul",
                    ({"id": "tag-sidebar"},),
                    "li",
                    "class",
                    "a",
                )

                lista_tags_attrs = (
                    "tag-type-character",
                    "tag-type-copyright",
                    "tag-type-artist",
                    "tag-type-general",
                )

            case "us":

                clase_container = "thumbail-container"

                tag_contenido = ("div", "content_push", False, False)

                tag_container = (
                    "ul",
                    ({"id": "tag-list "}, {"class": "tag-list-left"}),
                    "li",
                    "class",
                    "a",
                )

                lista_tags_attrs = (
                    "character-tag",
                    "copyright-tag",
                    "artist-tag",
                    "general-tag",
                )

            case "xyz":

                clase_container = "col-xl-9 col-md-8 col-sm-12"

                tag_contenido = (
                    "app-post-image",
                    "post-image ng-star-inserted",
                    True,
                    False,
                )

                tag_container = (
                    "app-tag-set",
                    (
                        {"class": "ng-star-inserted"},
                        {"_ngcontent-serverapp-c112": ""},
                    ),
                    "mat-chip",
                    "style",
                    "h4",
                )

                lista_tags_attrs = (
                    "background:#33691e;",
                    "background:#ad1457;",
                    "background:#d32f2f;",
                    "background:#3f51b5;",
                )
            case _:

                raise ValueError(f"version desconocida de Rule34: {self.url}")

        self.tag_contenido = tag_contenido

        self.lista_posts = self.sopa.find("div", {"class": clase_container})  # type: ignore

        self.tag_container = tag_container

        self.lista_tags_attrs = lista_tags_attrs

    def conseguir_nombre(self) -> str:  # type: ignore

        assert self.sopa is not None

        (
            contenedor,
            attrs_contenedor,
            elementos_tag,
            attr_relevante_tag,
            contenedor_string,
        ) = self.tag_container

        for attr_especifico in attrs_contenedor:

            tagsidebar = self.sopa.find(contenedor, attr_especifico)

            if tagsidebar is not None:
                break

        else:

            raise ValueError(f"no se pudo encontrar nombre para {self.url}")

        for clase in self.lista_tags_attrs:

            try:
                tag = tagsidebar.find(
                    elementos_tag, {attr_relevante_tag: clase}  # type: ignore
                )

                for sub_tag in tag.find_all(contenedor_string):  # type: ignore

                    posible_nombre: str = sub_tag.string

                    if self.es_palabra.search(posible_nombre) is not None:

                        return posible_nombre

            except AttributeError:

                continue

    def conseguir_imagenes(self, contenido: BeautifulSoup):  # type: ignore

        (
            tag_contenido,
            clase_contenido,
            imagen_recursiva,
            video_recursivo,
        ) = self.tag_contenido

        contenedor = contenido.find(tag_contenido, {"class": clase_contenido})

        assert contenedor is not None

        try:

            imagen_tag = contenedor.find("img", recursive=imagen_recursiva)  # type: ignore

            yield imagen_tag["src"]  # type: ignore

        except TypeError:

            video_tag: Tag = contenedor.find(  # type: ignore
                "video", recursive=video_recursivo  # type: ignore
            )

            for nombre_tipo in self.tipos_video:

                source_tag: Tag = video_tag.find(  # type: ignore
                    "source", {"type": nombre_tipo}
                )

                if source_tag is not None:

                    yield source_tag["src"]

                    break

    def conseguir_tableros(self):
        assert self.sopa is not None

        if self.lista_posts is not None:

            for atag in self.lista_posts.find_all("a"):  # type: ignore

                yield atag["href"]

    def definir_info_pagina(self):

        self.conseguir_tags_comunes()

        super().definir_info_pagina()


class Nhentai(RasparConjuntoTableros):
    reformar_url = compile(r"(\d+)t(.*)$")

    def conseguir_tags_comunes(self):
        assert self.sopa is not None

        self.div_back_to_gallery = self.sopa.find("div", {"class": "back-to-gallery"})

        if self.div_back_to_gallery is not None:

            self.url = urljoin(self.url, self.div_back_to_gallery.a["href"])  # type: ignore

            self.sopa = self.conseguir_sopa(self.url)

    def definir_info_pagina(self):

        self.conseguir_tags_comunes()

        super().definir_info_pagina()

    def conseguir_nombre(self) -> str:

        assert self.sopa is not None

        div_info = self.sopa.find("div", id="info")

        eliminar_parentesis = compile(r"\(.*?\)")
        eliminar_corchetes = compile(r"\[.*?\]")

        raw_nombre: str = div_info.h1.string  # type: ignore

        if "[English]" in raw_nombre:

            try:

                raw_nombre = raw_nombre.split("|")[1]

            except IndexError:
                pass

            else:

                raw_nombre = raw_nombre.split("[English]")[0]

        raw_nombre = eliminar_parentesis.sub("", raw_nombre)

        raw_nombre = eliminar_corchetes.sub("", raw_nombre)

        return raw_nombre

    def conseguir_imagenes(self, contenido: BeautifulSoup):  # type: ignore

        contenedor = contenido.find("div", id="thumbnail-container")

        for img in contenedor.find_all(  # type: ignore
            "img", {"class": "lazyload"}
        ):  # type: ignore

            yield self.reformar_url.sub(r"\1\2", img["data-src"])

    def raspar_pagina_inicial(self):

        return True

    def conseguir_tableros(self) -> Iterator[str]:

        return
        yield


# codigo principal corre el scraper


def conseguir_scrapers():
    from inspect import getmembers, isclass

    from sys import modules

    current_module = modules[__name__]

    scrapers = {
        nombre.lower(): cls
        for nombre, cls in getmembers(current_module, isclass)
        if nombre
        not in (
            "BeautifulSoup",
            "Descargador",
            "_RaspadorBasico",
            "Path",
            "RasparConjuntoTableros",
            "RasparTablero",
        )
    }

    return scrapers


def conseguir_parser():
    # opciones generales

    parser = ParserArgumentosSeguidores(nombre_posicionales="url", description=__doc__)

    # opciones globales

    parser.add_argument(
        "-p",
        "--ruta-global",
        type=Path,
        default=Rutas.DL.value,
        general=True,
        help="ruta global para guardar las imagenes. puede ser cambiada por las opcion -r para cualquier url individual. Por defecto la carpeta de descarga de windows.",
    )

    # opciones individuales

    parser.add_argument(
        "-n",
        "--nombre",
        default=None,
        help="nombre dado a las imagenes a descargar. si se omite, se escrapea un nombre del sitio.",
    )

    parser.add_argument(
        "-r",
        "--ruta",
        type=Path,
        help="opcion para sobreescribir la ruta de descarga de la url que le sigue. por defecto es la misma que la global.",
    )

    parser.add_argument(
        "-c",
        "--crear-carpeta",
        action="store_true",
        help="indica si debe de crearse una carpeta para guardar las imagenes. se creara dentro de la carpeta de ruta",
    )

    parser.add_argument(
        "-s",
        "--simular",
        action="store_true",
        help="hace que el programa se salte la descarga, y en su lugar imprima las urls de las imagenes obtenidas, y del nombre obtenido si no se indico.",
    )

    return parser


def obtener_nombre_sitio(url: str) -> Optional[str]:
    encontrado = nombre_sitio.search(url)

    if encontrado is not None:

        sitio: str = encontrado[1]

        sitio = numeros_iniciales.sub("", sitio)

        return sitio

    return None


def procesar_conjuntos_args(
    scrapers: dict[str, type], lista_conjuntos: list[dict[str, Any]], opts
):
    for conjunto_arg in lista_conjuntos:

        url = conjunto_arg["url"]

        if conjunto_arg["ruta"] is None:

            conjunto_arg["ruta"] = opts.ruta_global

        sitio_encontrado = obtener_nombre_sitio(url)

        if sitio_encontrado is None:

            print(f"no se encontro nombre de sitio para url: {url}")

            continue

        try:

            cls_raspador = scrapers[sitio_encontrado]

            raspador = cls_raspador(**conjunto_arg)

        except KeyError:

            print(
                f"no se encontro raspador para url: {url}, con sitio: {sitio_encontrado}"
            )

            continue

        try:

            # raspador.sopa = raspador.conseguir_sopa(raspador.url)

            # print(list(raspador.conseguir_tableros()))

            raspador.run()

        except (AttributeError, TypeError) as _error: 

            print(
                f"un error ocurrio al parsear {url} de tipo {raspador.__class__.__name__}"
            )

            print(_error.__traceback__)

        except requests.HTTPError:

            print(f"un error de conexion ocurrio al parsear {url}")

            raise

        else:

            print(f"descargado exitosamente: {url}")


def main():
    parser = conseguir_parser()

    # procesar opciones
    opts = parser.parse_args()

    scrapers = conseguir_scrapers()

    procesar_conjuntos_args(scrapers, opts.url, opts)


if __name__ == "__main__":
    main()
