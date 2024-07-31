#!/usr/bin/env zsh
# shellcheck --shell=bash

MODULOS=~/programacion/modulos/sh
DIR_SITIOS=$MODULOS/datos/verpn/sitios.sh
DIR_VIDEOS=/sdcard/Documents/Leer/videos

ayuda() {
  less -FEXR <<- HELP
 uso: ${ZSH_ARGZERO:t} comando [opciones] args

  abrir/organizar sitios, libros, y videos pn
   comandos y opciones:

   web [opciones]                                   abrir sitio web dado por el alias.
   [-m/--modificar alias ruta] [-b/--borrar alias]  borra, modifica,inserta aliases de sitios
   video             abrir video por medio de selector.
   carpeta [ruta]    abrir imagenes de carpeta, con selector
HELP
exit "$1"
}

comandos=( help -h --help web video carpeta )

comando_crudo="$1"

[[ -z "$comando_crudo" ]] && ayuda 1 

comando="${comandos[(r)${comando_crudo}*]}" 

shift 

. $MODULOS/funciones_error.sh

case "$comando" in
  -h|--help)
    ayuda 0
    ;;
  web)
    #web
    . $MODULOS/funciones_dicc.sh
    . $DIR_SITIOS
    zparseopts -F -E -D m:=accion -modificar:=accion b=accion -borrar=accion || ayuda 1

    _alias="$1" 

    case "${accion[1]}" in
      -m|--modificar)
        { modificar_entrada sitios "$_alias" "${accion[2]}" } || 
        { error_exit "valor vacio de llave." }

        salvar_dict sitios $DIR_SITIOS
        
        ;;
      -b|--borrar)

        { eliminar_entrada sitios "$_alias" } || 
        { error_exit "no se encontro entrada para '$_alias.'" }

        salvar_dict sitios $DIR_SITIOS

        ;;
      *)
        if [[ -z "$_alias" ]]
        then
          print_tabla sitios "->"
          return 0
        fi

        pagina=$( encontrar_valor_llave_mas_similar sitios "$_alias" ) || 
        { error_exit "no se encontro sitio para '$_alias'." }

        termux-open "$pagina"
    esac
    ;;
  video)
    #videos
    pushd -q $DIR_VIDEOS

    eza -1 --no-quotes | fzf --cycle --bind="enter:execute( termux-open "{}" )"

    popd -q

    ;;
  carpeta)
    # carpeta
    
    ruta="$1"

    pushd -q "$ruta"

    fzf --prompt "elegir:" --cycle  --bind="enter:execute( termux-open {} )"

    popd -q
    
    ;;

  *)
    error "no se reconoce comando '$comando_crudo'"
    ayuda 1
    ;;
esac



