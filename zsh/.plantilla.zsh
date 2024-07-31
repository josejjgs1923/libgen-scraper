#!/usr/bin/env zsh

MODULOS=~/programacion/modulos/sh
. $MODULOS/funciones_error.sh

ayuda() {
  less -FEXR <<- HELP
  uso: ${ZSH_ARGZERO:t}
HELP
	exit "$1"
}

error(){
  echo "$1" 1>&2 && exit 1
}


zparseopts -F -E -D h=_ayuda -help=_ayuda || ayuda 1

[[ -n "${_ayuda:+1}" ]] && ayuda 0
