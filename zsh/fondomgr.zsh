#!/usr/bin/env zsh

RUTA_FONDOS=/sdcard/Pictures/fondos
DIR_FONDOS=~/programacion/modulos/sh/datos/estado_fondos
FONDOS_INICIO=$DIR_FONDOS/fondos_inicio.sh
FONDOS_BLOQUEO=$DIR_FONDOS/fondos_bloqueo.sh
FONDO_MAS_RECIENTE=$DIR_FONDOS/fondo_mas_reciente.sh

# variable global para colocar los vaalores de fondo
# inicio y bloqueo, y poder exportar al mismo tiempo

# variable globar con valor de fondo actual
FONDO=

visualizar_fondos(){
  msg="$2"

  repetir "-" "${#msg}"
  
  echo
  echo $msg 

  repetir "-" "${#msg}"

  echo
  printf "fondo: %s\n" ${(P)1}

}

repetir()
{
  printf "${1}%.0s"  {1.."$2"}
}

pop_random(){

  cant=${#${(P)1}}

  idx=$( shuf -i 1-$cant -n 1 )

  FONDO="${${(P)1}[$idx]}"

  eval "${1}[$idx]=()"

}


gen(){
  eval "$1=( * )"
}

salvar(){  
  declare -p "$1" > "$2"
}

ayuda() {
  less -FERX <<- HELP
  uso:${ZSH_ARGZERO:t} comando [Opciones]

  Script para cambiar diariamente los fondos de pantalla del telefono.

  comandos:
  -h/--help           imprime esta ayuda y sale.
  gen                 llena los arreglos con nombres de archivos de fondos.
  estado [-f/---full] muestra los fondos restantes con formato.
  cambiar [-l/--lock] elige un fondo al azar para cambiar pantalla de inicio.
                       si se pasa -l, tambien bloqueo.
HELP
	exit "$1"
}

comandos=( -h --help gen estado cambiar check )

_comando="$1" 

[[ -z "$_comando" ]] && ayuda 1

comando="${comandos[(r)${_comando}*]}"

shift 

cd $RUTA_FONDOS 

case "$comando" in
  -h|--help)
    ayuda 0
    ;;
  gen)
    # generar el archivo de fondos desde cero
    vars=( 
      fondos_inicio $FONDOS_INICIO 
      fondos_bloqueo $FONDOS_BLOQUEO 
    )

    for var dir in $vars
    do
      gen "$var"
      salvar "$var" "$dir"
    done

    fondo_mas_reciente="$(eza --color=never -s=modified --oneline --no-quotes | tail -n 1)" 


    salvar fondo_mas_reciente $FONDO_MAS_RECIENTE
    ;;
  *)
    . $FONDOS_INICIO
    . $FONDOS_BLOQUEO

    long=( ${#fondos_inicio} ${#fondos_bloqueo} )

    case "$comando" in
      estado)
        # mostrar las listas de fondos restantes

        zparseopts -F -E -D f=completo -lock=completo || ayuda 1

        . $FONDO_MAS_RECIENTE

        msg_inicio="fondos de inicio: ${long[1]}"

        msg_bloqueo="fondos de bloqueo: ${long[2]}"

        echo "fondo mas reciente: $fondo_mas_reciente"

        if [[ "${#completo}" -gt 0 ]]
        then
          visualizar_fondos fondos_inicio  "$msg_inicio"

          visualizar_fondos fondos_bloqueo "$msg_bloqueo"
        else

          echo $msg_inicio
          echo $msg_bloqueo

        fi
        ;;

      cambiar)
        zparseopts -F -E -D l=bloqueo -lock=bloqueo || ayuda 1

        pop_random fondos_inicio

        termux-wallpaper -f "$FONDO" 

        [[ "${long[1]}" -eq 1 ]] && gen fondos_inicio

        salvar fondos_inicio $FONDOS_INICIO 

        if [[ "${#bloqueo}" -gt 0 ]]
        then
          pop_random fondos_bloqueo

          termux-wallpaper -l -f "$FONDO"

          [[ "${long[2]}" -eq 1 ]] && gen fondos_bloqueo

          salvar fondos_bloqueo $FONDOS_BLOQUEO
        fi

        ;;

      check)
        # verificar si existen nuevos fondos en $DIR_FONDOS
        
        . $FONDO_MAS_RECIENTE 

        {
          declare IFS

          IFS=$(echo -en "\n\b")

          nuevos=( 
            $( find . -type f -newermm "$fondo_mas_reciente" ) 
          )

        } > /dev/null

        [[ "${#nuevos}" -eq 0 ]] && return 0

        fondos_inicio+=$nuevos

        fondos_bloqueo+=$nuevos

        fondo_mas_reciente="${nuevos[-1]}"
        
        vars=( 
          fondos_inicio $FONDOS_INICIO 
          fondos_bloqueo $FONDOS_BLOQUEO 
          fondo_mas_reciente $FONDO_MAS_RECIENTE 
          ) 

        for var dir in $vars
        do 
          salvar "$var" "$dir"
        done

        ;;

      *)
        echo "No Se Reconoce Comando '$_comando'" 1>&2
        return 1
        ;;
    esac
    ;;
esac


