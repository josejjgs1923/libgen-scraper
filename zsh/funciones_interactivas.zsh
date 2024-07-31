#!/usr/bin/env zsh
# shellcheck --shell=bash

MODULOS=~/programacion/modulos/sh
DIR_SITIOS=$MODULOS/datos/verpn/sitios.sh
DIR_VIDEOS=/sdcard/Documents/Leer/videos

ayuda() {
	printf "uso: ${ZSH_ARGZERO:t} "
	exit "$1"
}


comando="$1" 

shift 


case "$comando" in
  -h|--help)
    ayuda 0
    ;;
  w*)
    #web
    . $MODULOS/funciones_dicc.sh
    . $DIR_SITIOS
    zparseopts -F -E -D m:=accion -modificar:=accion b=accion -borrar=accion || ayuda 1

    _alias="$1" 

    case "${accion[1]}" in
      -m|--modificar)
        { modificar_entrada sitios "$_alias" "${accion[2]}" } || 
        { echo "valor vacio de llave."  1>&2 && return 1 }

        salvar_dict sitios $DIR_SITIOS
        
        ;;
      -b|--borrar)

        { eliminar_entrada sitios "$_alias" } || 
        { echo "no se encontro entrada para '$_alias.'" 1>&2 &&  return 1 }

        salvar_dict sitios $DIR_SITIOS

        ;;
      *)
        if [[ -z "$_alias" ]]
        then
          max=0

          for llave in ${(k)sitios}
          do
            long=${#llave}
            max=$(( $long > $max ? $long : $max ))
          done

          printf "%-${max}s -> %s\n" ${(kv)sitios}

          return 0
        fi

        pagina=$( encontrar_valor_llave_mas_similar sitios "$_alias" ) || 
        { echo "no se encontro sitio para '$_alias'." 1>&2 && return 1 }

        termux-open "$pagina"
    esac
    ;;
  v*)
    #videos
    cd $DIR_VIDEOS

    eza --no-quotes | fzf --bind="enter:become( termux-open "{}" )"

    ;;
  *)
    echo "no se reconoce comando '$comando'" 1>&2 
    return 1
    ;;
esac



