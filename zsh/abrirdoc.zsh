#!/data/data/com.termux/files/usr/bin/zsh
## shellcheck --shell=bash

MODULOS=~/programacion/modulos/sh
DIR_LIBROS=$MODULOS/datos/libros/libros.sh

. $MODULOS/funciones_dicc.sh
. $MODULOS/funciones_error.sh
. $DIR_LIBROS
 
ayuda() {
  less -FEXR <<- HELP
  uso: ${ZSH_ARGZERO:t} comando [opciones]

  abrir libros y organizar documentos.

     comandos y uso:
       --help, -h                 mostrar esta ayuda y salir
       modificar [alias] [ruta]   agregar rutas libros/doc con aliases. ruta y alias opcionales
                                  se preguntara por doc y alias si no se pasan.
       abrir, open alias          abrir el libro/doc
       borrar      alias          borra el libro/doc de la base de datos

HELP
	exit "$1"
}


comando_crudo="$1" 

[[ -z "$comando_crudo" ]] &&
{ print_tabla libros && exit }

shift  

comandos=( -h --help modificar borrar abrir open )
comando="${comandos[(r)${comando_crudo}*]}" 

case "$comando" in
  -h|--help)
    ayuda 0
    ;;

  modificar)
    ruta_libro="$2" 

    [[ -z "$ruta_libro" ]] &&
    { ruta_libro="$PWD/$( fzf --cycle --prompt='elegir ruta:' )" || return 0 }

    libro_alias="$1"

    [[ -z "$libro_alias" ]] &&
    { read "libro_alias?ingrese alias para el doc:" || return 1 }


    [[ -z "$libro_alias" ]] &&
    { error_exit "valor vacio alias de ruta de libro." }

    { modificar_entrada libros "$libro_alias" "$ruta_libro" } || 
    { error_exit "valor vacio de llave." }

    salvar_dict libros $DIR_LIBROS
    ;;

  *)
    libro_alias="$1"

    [[ -z "$libro_alias" ]] &&
    { error_exit "no se dio valor de libro para usar." }

    case "$comando" in
      borrar)

        { eliminar_entrada libros "$libro_alias" } || 
        { error_exit "no se encontro entrada para '$libro_alias.'" }

        salvar_dict libros $DIR_LIBROS
        ;;

      abrir|open)
        pagina=$( encontrar_valor_llave_mas_similar libros "$libro_alias" ) || 
        { error_exit "no se encontro ruta para '$libro_alias'." }

        termux-open "$pagina"
        ;;
      *)
        error "no se reconoce comando '$comando'." 
        ayuda 0
        ;;
    esac
    ;;
esac

