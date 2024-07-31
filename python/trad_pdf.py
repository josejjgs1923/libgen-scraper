#!/usr/bin/env python

import argparse
from pypdf import PdfReader
import logging
from system_admin.files import Rutas
from deep_translator import GoogleTranslator
from re import compile

from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT, TA_LEFT, TA_CENTER

# from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from pprint import pprint as pp
# from reportlab.lib.units import inch

# argumentos line a de comandos
parser = argparse.ArgumentParser()

parser.add_argument("pagina", type=int, default=0)

args = parser.parse_args()

logger = logging.getLogger("pypdf")
logger.setLevel(logging.ERROR)

traductor = GoogleTranslator(source="english", target="spanish")

carpeta = Rutas.DOC.value / "libros traducir"
libro_obj = carpeta / "Resource Accounting for Sustainability Assessment.pdf"
libro_res = carpeta / "traducido.pdf"

FONT = "times-roman"
SIZE = 12

re_sep = compile(r"\n{2,}")
re_linea = compile(r"\n")

re_numeracion = compile(r"^\d\.")

re_num_pagina = compile(r"\d+$")

re_bulletin = compile(r"^•")
re_lista_bulletin = compile(r"\n(?=•)")

re_num_titulo = compile(r"^(\d+(\.)?)+")
re_lista_num = compile(r"\n(?=\d+)")

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(name="Justify", alignment=TA_JUSTIFY))

estilo_justificar = styles["Justify"]
estilo_justificar.fontName = FONT

estilo_primario = styles[f"Heading1"]
estilo_primario.fontName = FONT
estilo_primario.alignment = TA_CENTER

estilo_secundario = styles[f"Heading2"]
estilo_secundario.fontName = FONT
estilo_secundario.alignment = TA_CENTER

estilo_terciario = styles[f"Heading3"]
estilo_terciario.fontName = FONT


def crear_parrafo(texto):
    yield Paragraph(texto, estilo_justificar)
    yield Spacer(1, 12)


def crear_titulo_terciario(texto, alineacion):
    estilo_terciario.alignment = alineacion
    texto = f"<i>{texto}</i>"
    yield Paragraph(texto, estilo_terciario)
    yield Spacer(1, 12)


def crear_titulo(texto, nivel=1):
    estilo = styles[f"Heading{nivel}"]
    yield Paragraph(texto, estilo)
    yield Spacer(1, 12)


def prueba_lista(texto, regex_detec, regex_split):
    return regex_detec.search(texto) and regex_split.search(texto)


def crear_lista(texto, regex_split):
    for item in regex_split.split(texto):
        yield from crear_parrafo(item)


def determinar_layout(texto):

    texto = texto.strip()

    if re_linea.search(texto):

        posible_titulo, parrafo = re_linea.split(texto, 1)

        if posible_titulo == "Resumen":

            yield from crear_titulo_terciario(posible_titulo, TA_LEFT)

            texto = parrafo

        if re_numeracion.search(posible_titulo):

            yield from crear_titulo_terciario(posible_titulo, TA_LEFT)

            texto = parrafo

        elif re_num_pagina.search(posible_titulo):

            yield from crear_titulo_terciario(posible_titulo, TA_RIGHT)

            texto = parrafo

        if prueba_lista(texto, re_bulletin, re_lista_bulletin):
            yield from crear_lista(texto, re_lista_bulletin)

        elif prueba_lista(texto, re_num_titulo, re_lista_num):
            yield from crear_lista(texto, re_lista_num)

        else:

            yield from crear_parrafo(texto)

    else:

        yield from crear_titulo(texto)


def _main():

    reader = PdfReader(libro_obj)

    portada = reader.pages[args.pagina]

    cont = portada.get_contents()

    pp(cont)



def main():
    reader = PdfReader(libro_obj)

    portada = reader.pages[args.pagina]

    texto = portada.extract_text(
        extraction_mode="layout", layout_mode_space_vertical=False
    )

    texto_traducido = traductor.translate(texto)

    # print(re_sep.split(texto_traducido))

    doc = SimpleDocTemplate(
        str(libro_res),
        pagesize=LETTER,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    flowables = []

    contenido = re_sep.split(texto_traducido)

    # print(contenido)

    if len(contenido) > 1:

        posible_titulo, posible_parrafo = contenido[:2]

        if len(re_linea.findall(posible_titulo)) > 1:


        else:

            flowables.extend(crear_titulo(posible_titulo))

            if re_num_pagina.search(posible_titulo):

                flowables.extend(crear_titulo_terciario(posible_titulo, TA_RIGHT))

            elif re_num_titulo.search(posible_titulo):

                flowables.extend(crear_titulo(posible_titulo))
            else:

                flowables.extend(crear_titulo(posible_titulo))

    else:

        if re_linea.search(contenido[0]):

            flowables.extend(crear_parrafo(contenido[0]))
        else:

            flowables.extend(crear_titulo(contenido[0]))

    for texto in contenido[2:]:
        flowables.extend(determinar_layout(texto))

    # pp(flowables)
    # doc.build(flowables)

if __name__ == "__main__":
    main()
