#!/bin/zsh

# Zsh Theme Chooser by fox (fox91 at anche dot no)
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://www.wtfpl.net/txt/copying/ for more details.

_pwd=$PWD 

[[ $_pwd == $HOME ]] || cd 

USED_PATH="${HOME}/.config/mytermux"

ayuda() {
  less -FERX <<- HELP
  uso: ${ZSH_ARGZERO:t} comando <query>
  herramienta para personalizar la terminal.
  comandos:
  help             mostrar esta ayuda y salir.
  tema, zsh        configurar tema del prompt.
  fuente           cambiar fuente de la terminal
  color            cambiar colores de la terminal
  usado [estilo]   mostrar configuracion estilo
                   los estilos son los mismos comandos.
HELP
	exit "$1"
}

comandos=( tema zsh color fuente usado help --help -h  )

# comparar con comandos aceptados, imprimir mas parecido, o dejar vacio

comando="${comandos[(r)${1}*]}"

[[ -z "$1" ]] && ayuda 1

shift || ayuda 1

case $comando in
  help|--help|-h)
    ayuda 0 
    ;;
  usado)
    IMPRIMIR_USADO=1
    comando="${comandos[(r)${1}*]}"
  ;;
esac

case $comando in
 zsh|tema) 

    CONF_PATH="${HOME}/.zshrc"
    USED_FILE="${USED_PATH}/zsh/used.log"
    DIRS="$ZSH/themes $ZSH/custom/themes"
    FAVLIST="${HOME}/.zsh_favlist"
    ZSH_CONFIGURATION_THEME_USED=$( 
      grep -Po "ZSH_THEME=(\S+)" $CONF_PATH | sed -E "s/.*=//g" 
    )

    cambiar_tema(){

      CHOICE="$*"
      CHOICE="${CHOICE:t}"

      if sed -i --follow-symlinks\
        "s/ZSH_THEME=${ZSH_CONFIGURATION_THEME_USED}.*/ZSH_THEME=${CHOICE}/g"\
        ${CONF_PATH}; then
        if [ ! -f ${USED_FILE} ]; then

          echo -e "${CHOICE}" >> $USED_FILE

        elif [ -f $USED_FILE ]; then

          sed -i --follow-symlinks "s/${USED}/${CHOICE}/g" $USED_FILE

        fi
      fi
    }

    theme_preview() {
        source $ZSH/oh-my-zsh.sh
       
        THEME_PATH=$1".zsh-theme"
        THEME_NAME="${THEME_PATH:t:r}"

        print "$fg[blue]${(l.((${COLUMNS}-${#THEME_NAME}-5))..─.)}$reset_color $THEME_NAME $fg[blue]───$reset_color"

        source "$THEME_PATH" 
      
        cols=$(tput cols)
        (exit 1)
        print -P "$PROMPT                                                                                      $RPROMPT"
    }

    INGRESAR_CAMBIO="ctrl-c:become@ 
      $( declare -f cambiar_tema ) ; 
      cambiar_tema {}; 
      exec zsh @"

    INGRESAR_PREVIEW="enter:preview|
      $( declare -f theme_preview ) ; 
        theme_preview {} |"

    export ZSH_CONFIGURATION_THEME_USED

     ;;
  *) 
    case "$comando" in
      fuente) 
        CONF_PATH="${HOME}/.termux/font.ttf"
        USED_FILE="${USED_PATH}/fonts/used.log"
        DIRS="$HOME/.fonts"
        FAVLIST="${HOME}/.font_favlist"
        EXTENSION="ttf"
        ESPERA="sleep 2 ;"
        ;;
      color) 
        CONF_PATH="${HOME}/.termux/colors.properties"
        USED_FILE="${USED_PATH}/colorscheme/used.log"
        DIRS="$HOME/.colorscheme"
        FAVLIST="${HOME}/.color_favlist"
        EXTENSION="colors"
        ESPERA=""
         ;;
     *) 
        ayuda 1 ;;  
    esac

    preview() {
      CHOICE="$1"
      cp -fr "${CHOICE}.${EXTENSION}" "$CONF_PATH"
      termux-reload-settings
    }

    cambiar(){

      CHOICE=$1".$EXTENSION"

      if cp -fr "$CHOICE" "$CONF_PATH"; then
        CHOICE=${CHOICE:t:r}
        echo 0 > "$modo_conf"
        if [ ! -f ${USED_FILE} ]; then
          echo -e "${CHOICE}" >> $USED_FILE
        elif [ -f $USED_FILE ]; then
          sed -i --follow-symlinks "s/${USED}/${CHOICE}/g" $USED_FILE
        fi
      fi
    }

    INGRESAR_CAMBIO="ctrl-c:become@ 
      $( declare -f cambiar ) ; 
      cambiar {}; 
      termux-reload-settings @"

    INGRESAR_PREVIEW="enter:execute| 
      $( declare -f preview ) ; 
          preview {}; 
          $ESPERA
          termux-reload-settings |"

    modo_conf="$(mktemp)"

    export modo_conf

    echo 1 > "$modo_conf"

    [[ -n ${IMPRIMIR_USADO:+1} ]] || mv "$CONF_PATH" "${CONF_PATH}.bck"
esac

list_options() {
  find $( printf "$*" ) -maxdepth 1 -type f -print | sed -E "s/\.[^\/]+$//"
}

insert_favlist() {

  THEME_NAME="$*"

  if  [[ $(bat -p "$modo") == 1 ]]
  then
    if grep -q "$THEME_NAME" $FAVLIST 2> /dev/null
    then
        echo "change-header($prompt_ya_esta)"
    else
      echo "$THEME_NAME" >> "$FAVLIST" ; 
      sort -o "$FAVLIST" "$FAVLIST"
      echo "change-header($prompt_guardado)"
    fi
  else
    echo "execute(sed -i --follow-symlinks '\\@{}@d' $FAVLIST)+change-header($prompt_eliminado)+reload(bat -p $FAVLIST)"
  fi

}

alternar_favoritos(){ 

  if  [[ $(bat -p "$modo") == 1 ]]
  then 
    echo 0 > "$modo"
    echo "change-header($prompt_favoritas)+reload(bat -p $FAVLIST)"
  else
    echo 1 > "$modo"
    echo "change-header($prompt_global)+reload~
      $DEF_LIST_OPTIONS ; 
      list_options $DIRS ; ~" 
  fi 
}


USED="$(bat -p $USED_FILE)"

USED="${USED:t:r}"

[[ -n ${IMPRIMIR_USADO:+1} ]] && echo "usado: $USED" && exit 0

export DIRS CONF_PATH EXTENSION USED USED_FILE FAVLIST ZSH 

DEF_LIST_OPTIONS="$( declare -f list_options )"

export DEF_LIST_OPTIONS

GUARDAR_FAVORITOS="ctrl-g:transform| 
  $( declare -f insert_favlist ) ; 
  insert_favlist {} |"

ALTERNAR_FAVORITOS="ctrl-f:transform% 
$( declare -f alternar_favoritos ) ; 
alternar_favoritos %"

prompt_global="Lista Temas Global"
prompt_favoritas="Lista Favoritos"  
prompt_ya_esta="Ya esta en Favoritos"
prompt_guardado="Guardado en favoritos"  
prompt_eliminado="Eliminado"  

modo="$(mktemp)"

export prompt_favoritas prompt_global prompt_ya_esta prompt_guardado prompt_eliminado modo

echo 1 > "$modo"

list_options "$DIRS" | fzf\
  --query="$*"\
  --layout=reverse\
  -d "/"\
  --header=$prompt_global\
  --with-nth "-1"\
  --prompt "elegir tema:"\
  --cycle\
  --height="60%"\
  --preview-window="up,35%,hidden"\
  --border=bottom\
  --border-label="tema actual: $USED"\
  --bind $INGRESAR_PREVIEW\
  --bind $INGRESAR_CAMBIO\
  --bind $ALTERNAR_FAVORITOS\
  --bind $GUARDAR_FAVORITOS\
  --bind "ctrl-o:toggle-preview"


if [[ -f "$modo_conf" ]]
then
  if  [[ $(bat -p "$modo_conf") == 1 ]]
  then
    mv "${CONF_PATH}.bck"  "$CONF_PATH"
    termux-reload-settings
  else
    rm "${CONF_PATH}.bck"
  fi
  rm -f "$modo_conf"
fi 

rm -f "$modo" 

[[ $_pwd == $HOME ]] || popd -q  
