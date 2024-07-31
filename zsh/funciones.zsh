#!/usr/bin/env zsh

# ayuda() {
# 	printf "uso: ${ZSH_ARGZERO:t} "
# 	exit "$1"
# }
#
# zparseopts -F -E -D h=_ayuda -help=_ayuda || ayuda 1
#
# [[ -v _ayuda ]] && ayuda 0

video2gif(){
	arch="$*"

	ffmpeg -hide_banner -ss 0 -t 1 -i "$arch" -filter_complex "[0:v] palettegen" _palette.png

	ffmpeg -hide_banner -i "$arch" -i _palette.png -filter_complex "[0:v][1:v] paletteuse" "${arch:r}.gif"

	rm "$arch" _palette.png
}

metad(){
  fzf --prompt "cancion:" --preview-window="up,80%,hidden" --cycle\
  --bind "enter:preview|ffprobe -hide_banner --  $PWD/{}|"\
  --bind "ctrl-o:toggle-preview"
}

ver(){
  direct="$*"
  entrada=$'nuevo?nuevo nombre:\n'

  [[ -n "$direct" ]] && cd "$direct" || return 1

  eza -1 --no-quotes| fzf --height="40%" --prompt "elegir:" --cycle\
  --bind  "enter:execute| termux-open {}|"\
  --bind "ctrl-r:execute| arch={}; 
          read \"$entrada\" ; 
          mv \"\$arch\" \"\${nuevo}.\${arch:e}\"  |"\
  --bind "ctrl-r:+reload|eza -1 --no-quotes|"

  [[ -n "$direct" && "$direct" != "." ]] &&  popd -q
}


prev(){
  fzf --preview='bat --color=always --style=numbers {}' --preview-window=down
}

eya(){
  printf "cum%.0s"  {1..10}
}
