#!/usr/bin/env python

"""
utilidad para automatizar la creacion de scripts y proyectos de varios lenguages de programacion.
abre o crea los scripts o proyectos dados en la linea de comandos.
"""
from pathlib import Path
from re import compile
from recetas.recetas_argparse import ParserArgumentosSeguidores
from stat import S_IEXEC
from typing import Any, Optional
from shutil import copy2
from subprocess import run
from system_admin.files import CrearScripts, RutasStandardScripts, nvim


DIRECTORIO_ACTUAL = Path(".")

SALTOS_LINEA_INCIAL = "\n" * 3

CAMBIAR_SHEBANG = compile(CrearScripts.INICIO_SHEBANG.value + r"(.*)")


def escribir_script(
    ruta_script: Path, plantilla: Optional[Path], shebang: Optional[str]
):
    """
    escribir script a la memoria, ya sea copiando plantilla o escribiendo datos nuevos.
    """

    match (plantilla, shebang):

        case (Path(), str()):

            texto = plantilla.read_text()

            ruta_script.write_text(
                CAMBIAR_SHEBANG.sub(
                    CrearScripts.INICIO_SHEBANG.value + " " + shebang, texto
                )
            )

        case (Path(), None):
            copy2(plantilla, ruta_script)

        case (None, str()):

            ruta_script.write_text(
                CrearScripts.INICIO_SHEBANG.value + " " + shebang + SALTOS_LINEA_INCIAL,
                "utf-8",
            )

        case _:

            ruta_script.write_text("", "utf-8")

    ruta_script.chmod(ruta_script.stat().st_mode | S_IEXEC)


def definir_info_script(ruta_script: Path, ruta_padre: Optional[Path]):
    """
    definir ruta absoluta, contenido script a partir del nombre, y devolver.
    """
    if (ruta_padre is not None) and (ruta_padre == DIRECTORIO_ACTUAL):
        ruta_padre = ruta_padre.absolute()

    extension = ruta_script.suffix.replace(".", "").upper()

    try:
        ruta_standard_script = RutasStandardScripts[extension].value

    except KeyError:

        ruta_script = (ruta_padre or DIRECTORIO_ACTUAL.absolute()) / ruta_script

        plantilla = None

    else:

        ruta_script = (ruta_padre or ruta_standard_script) / ruta_script

        plantilla = ruta_standard_script / (
            CrearScripts.NOMBRE_PLANTILLA.value + ruta_script.suffix
        )

        if not plantilla.exists():
            plantilla = None

    return ruta_script, plantilla


def crear_symlink(ruta_script: Path, opciones: dict[str, Any]):
    """
    crear link simbolico ya sea con un nombre o nombre del script sin extension.
    """
    match opciones:

        case {"crear_symlink_con_nombre": Path() as nombre_sym}:

            if nombre_sym.parent == DIRECTORIO_ACTUAL:

                symlink = CrearScripts.SYM.value / nombre_sym

            else:

                symlink = nombre_sym

        case {"crear_symlink": True}:

            symlink = CrearScripts.SYM.value / ruta_script.stem

        case _:

            return False

    symlink.symlink_to(ruta_script)

    return True


def crear_lista_nuevo_alias(alias: Optional[str], ruta_script: Path):
    if alias is not None:

        return ["New-Alias", alias, str(ruta_script), ";"]


def exportar_aliases(aliases_nuevos: list[str], comandos_aliases: list[str]):
    comando = ["pwsh", "-c"] + comandos_aliases

    comando += [
        "export-alias",
        "-Name",
        "(" + ", ".join('"' + alias + '"' for alias in aliases_nuevos) + ")",
        "-Append",
        "-as",
        "csv",
        str(CrearScripts.PWSH_SCRIPTS.value / "aliases.ps1"),
    ]

    run(comando)


def renombrar_script(ruta_script: Path, nuevo_nombre: str):
    """
    renombrar script con el nuevo nombre.
    """

    ruta_script = ruta_script.rename(ruta_script.with_stem(nuevo_nombre))

    return ruta_script


def copiar_script(ruta_script: Path, ruta_copia: Path):
    """
    copiar script en la nueva ruta.
    """

    if ruta_copia.parent == DIRECTORIO_ACTUAL:

        ruta_copia = ruta_script.with_stem(ruta_copia.stem)

    else:
        ruta_copia = ruta_copia.with_suffix(ruta_script.suffix)

    copy2(ruta_script, ruta_copia)

    return ruta_copia


def definir_variables_globales(globales, opciones):
    ruta_padre = opciones.pop("ruta") or globales.ruta_global

    shebang_final = opciones.pop("shebang") or globales.shebang_global

    ocultar = opciones.pop("ocultar") or globales.ocultar_global

    return ruta_padre, shebang_final, ocultar


def abrir_o_crear_script(globales, opciones: dict[str, Any]):
    """
    decidir si abrir script, crear un nuevo script, o realizar tareas de administracion:
    renombrar, copiar, crear aliases y crear symlinks para los scripts.
    """
    # revisar opciones si debe ser especifica o global


    ruta_padre, shebang_final, ocultar = definir_variables_globales(globales, opciones)

    # opciones que si deben ser individuales

    nombre_script = Path(opciones.pop("nombre"))

    ruta_script, plantilla = definir_info_script(nombre_script, ruta_padre)

    if ruta_script.exists():

        match opciones:

            case {"probar_existencia": True}:

                print(f"el script: {ruta_script.name} existe en {ruta_script.parent}.")

                return None, None

            case {"borrar": True, "copiar": Path() as ruta_copia}:

                ruta_copia = copiar_script(ruta_script, ruta_copia)

                ruta_script.unlink()

                if ocultar:
                    return None, None

                return ruta_copia, None

            case {"borrar": True}:

                ruta_script = ruta_script.unlink()

                return None, None

            case _:

                if nuevo_nombre := opciones.pop("renombrar"):
                    ruta_script = renombrar_script(ruta_script, nuevo_nombre)

                saltar = crear_symlink(ruta_script, opciones)

                lista_alias = crear_lista_nuevo_alias(
                    opciones.pop("alias"), ruta_script
                )

                saltar = saltar or (lista_alias is not None)

                if ruta_copia := opciones.pop("copiar"):
                    ruta_script = copiar_script(ruta_script, ruta_copia)

                ocultar = saltar or ocultar

                if ocultar:

                    return None, lista_alias

                return ruta_script, lista_alias

    else:

        match opciones:

            case (
                {"borrar": True}
                | {"probar_existencia": True}
                | {"renombrar": str()}
                | {"alias": str()}
                | {"crear_symlink": True}
                | {"crear_symlink_con_nombre": str()}
                | {"copiar": str()}
            ):
                print(f"no existe un script con el nombre '{ruta_script.name}'.")

                return None, None

            case _:

                escribir_script(ruta_script, plantilla, shebang_final)

                if ocultar:

                    print(
                        f"Se ha creado el Script '{ruta_script.name}' en '{ruta_script.parent}'"
                    )

                    return None, None

                return ruta_script, None


def conseguir_parser():
    """
    parser del script.
    """

    parser = ParserArgumentosSeguidores(
        nombre_posicionales="nombre", description=__doc__
    )

    # opciones globales
    parser.add_argument(
        "--sh-global",
        dest="shebang_global",
        default=None,
        general=True,
        help="Shebang global para usar en todos los scripts dados.",
    )

    parser.add_argument(
        "--d-global",
        dest="ruta_global",
        general=True,
        default=None,
        help="Ruta global de para guardar todos los scripts.",
    )

    parser.add_argument(
        "--o-global",
        dest="ocultar_global",
        general=True,
        action="store_true",
        help="Opcion global de para no abrir todos los scripts.",
    )
    # opciones individuales

    parser.add_argument(
        "-a",
        "--alias",
        dest="alias",
        default=None,
        help="Crear alias para el script, se creara alias de powershell.",
    )

    parser.add_argument(
        "-o",
        dest="ocultar",
        action="store_true",
        help="No abre el script en el editor, lo crea solamente si no existe.",
    )

    parser.add_argument(
        "--sh",
        dest="shebang",
        default=None,
        help="Indicar un shebang para el script, diferente del global o del guardado para el tipo de script.",
    )

    parser.add_argument(
        "-d",
        dest="ruta",
        type=Path,
        default=None,
        help="Ruta para guardar el script. por defecto es la global si se da; o la guardada para el tipo de script.",
    )

    parser.add_argument(
        "-b",
        "--borrar",
        dest="borrar",
        action="store_true",
        help="Borrar el Script dado, si existe.",
    )

    parser.add_argument(
        "-s",
        dest="crear_symlink",
        action="store_true",
        help="Indica si crear un link simbolico para el script. se crear un link con el nombre sin la extension.",
    )

    parser.add_argument(
        "--sym",
        dest="crear_symlink_con_nombre",
        type=Path,
        default=None,
        help="Indica si crear un link simbolico para el script. esta opcion permite pasar un nombre personalizado para el symlink.",
    )

    parser.add_argument(
        "-r",
        dest="renombrar",
        default=None,
        help="Indica que se debe renombrar el script con el nombre dado. Error si el script no existe.",
    )

    parser.add_argument(
        "-c",
        dest="copiar",
        type=Path,
        default=None,
        help="Indica que se debe copiar el script con el nombre dado. Error si el script no existe.",
    )

    parser.add_argument(
        "-p",
        dest="probar_existencia",
        action="store_true",
        help="Imprime si el script indicado existe o no. Salta todas las demas opciones.",
    )

    return parser


def main():
    parser = conseguir_parser()

    script_opts = parser.parse_args()

    scripts_abrir = []

    aliases_nuevos = []

    comandos_aliases = []

    for conjunto_opciones in script_opts.nombre:

        ruta_script, lista_alias = abrir_o_crear_script(script_opts, conjunto_opciones)

        if ruta_script is not None:

            scripts_abrir.append(ruta_script)

        if lista_alias is not None:

            aliases_nuevos.append(lista_alias[1])

            comandos_aliases += lista_alias

    if aliases_nuevos:
        exportar_aliases(aliases_nuevos, comandos_aliases)

    if scripts_abrir:
        nvim(*scripts_abrir)


if __name__ == "__main__":
    main()
