#!/usr/bin/env bash

MODULOS=~/programacion/modulos/sh
. $MODULOS/funciones_error.sh


basic_help() {
  less -FEXR <<- HELP
	uso: $0
HELP
  exit "$1"
}

error(){
  echo "$1" 1>&2 && exit 1
}



# -- PARSE OPTIONS --
while getopts opt; do
	case "$opt" in

		h) basic_help  0 ;;
		\?) basic_help 1 ;;
	esac
done
shift $(( OPTIND-1 ))

