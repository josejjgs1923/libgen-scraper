#!/usr/bin/python
"""
descargar videos o musica de las urls dadas, formatear por medio de opciones individuales.
"""

from argparse import Action
import json
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor import MetadataParserPP

from recetas.recetas_argparse import ParserArgumentosSeguidores
from system_admin.files import nvim, CrearScripts

# from pprint import pprint


RUTA_OPTS_VIDEO = CrearScripts.DATOS_PY.value / 'video_opts.json'

RUTA_OPTS_MUSICA = CrearScripts.DATOS_PY.value / 'musica_opts.json'


def abrir_json(nombre):
    match nombre:

        case 'v' | 'video':

            archivo = RUTA_OPTS_VIDEO

        case 'm' | 'musica':

            archivo = RUTA_OPTS_MUSICA

        case _:

            archivo = RUTA_OPTS_VIDEO

    nvim(archivo)


def obtener_postprocessor_dict(metadata_dict, opts):
    acciones = [
        (MetadataParserPP.interpretter, valor + ' ', f'%({campo})s')
        for campo, valor in metadata_dict.items()
    ]

    if opts['musica']:

        acciones += [
            (MetadataParserPP.replacer, campo, r'(.|\n)*', '')
            for campo in ('webpage_url', 'description')
        ]

    return {
        'actions': acciones,
        'key': 'MetadataParser',
        'when': 'pre_process',
    }


def procesar_urls(opts_urls, ruta_opts_yt_dlp, global_opts):
    with ruta_opts_yt_dlp.open('r', encoding='utf-8') as rf:
        opts_yt_dlp = json.load(rf)

    if global_opts.destino_global is not None:
        opts_yt_dlp['paths']['home'] = global_opts.destino_global

    plantilla_default = opts_yt_dlp['outtmpl']['default']

    for conjunto in opts_urls:

        nombre = conjunto['nombre']

        opts_yt_dlp['outtmpl']['default'] = (
            plantilla_default if nombre is None else nombre
        )

        metadata = conjunto['metadata']

        if metadata is not None:

            opts_yt_dlp['postprocessors'].append(
                obtener_postprocessor_dict(metadata, conjunto)
            )

            with YoutubeDL(opts_yt_dlp) as ydl:
                ydl.download([conjunto['url']])

            opts_yt_dlp['postprocessors'].pop()

            continue

        with YoutubeDL(opts_yt_dlp) as ydl:
            ydl.download([conjunto['url']])


def conseguir_parser():
    class validar_metadata(Action):

        campos_validos = (
            'title',
            'artist',
            'album',
            'genre',
            'date',
            'album_artist',
        )

        def __call__(self, parser, namespace, values: list[str], option_string=None):  # type: ignore

            campo, valor = values

            if values[0] in self.campos_validos:
                if (
                    hasattr(namespace, self.dest)
                    and getattr(namespace, self.dest) is not None
                ):
                    setattr(
                        namespace,
                        self.dest,
                        getattr(namespace, self.dest) | {campo: valor},
                    )
                else:
                    setattr(namespace, self.dest, {campo: valor})
            else:
                print(
                    f'no se reconoce el campo: {campo}, no se agregara a la metadata.'
                )

    def crear_formato(nombre):

        return f'{nombre}.%(ext)s'

    media_parser = ParserArgumentosSeguidores(
        nombre_posicionales='url', description=__doc__
    )

    # opciones generales
    media_parser.add_argument(
        '-p',
        dest='destino_global',
        general=True,
        help='ruta global para guardar todos los archivos. por defecto carpeta de descarga de windows.',
    )

    media_parser.add_argument(
        '-c',
        '--config',
        dest='config',
        general=True,
        choices=('v', 'm', 'video', 'musica'),
        default=None,
        help='abrir archivo de configuracion asociado.',
    )

    # opciones individuales
    media_parser.add_argument(
        '--meta',
        dest='metadata',
        nargs=2,
        action=validar_metadata,
        default=None,
        help=f"Agregar metadata al archivo, ya sea reemplazando existentes o creando nuevos campos. los valores permitidos de campos son: {', '.join(validar_metadata.campos_validos)}",
    )

    media_parser.add_argument(
        '-m',
        action='store_true',
        dest='musica',
        help='indica que se descargue la url solo como musica, extrayendo unicamente el audio.',
    )

    media_parser.add_argument(
        '-n',
        '--nombre',
        type=crear_formato,
        dest='nombre',
        help="nombre que va a recibir el archivo. por defecto, es el contenido de la tag de metadada 'title'.",
    )

    return media_parser


def main():
    media_parser = conseguir_parser()

    opts = media_parser.parse_args()

    if opts.config is not None:
        abrir_json(opts.config)

        media_parser.exit()

    opts_urls_videos = []
    opts_urls_musica = []

    for conjunto in opts.url:

        if conjunto['musica']:
            opts_urls_musica.append(conjunto)
        else:
            opts_urls_videos.append(conjunto)

    procesar_urls(opts_urls_videos, RUTA_OPTS_VIDEO, opts)

    procesar_urls(opts_urls_musica, RUTA_OPTS_MUSICA, opts)


if __name__ == '__main__':
    main()
