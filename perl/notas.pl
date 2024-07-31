#!/usr/bin/env perl

use strict;
use v5.38;

use Getopt::Long qw(GetOptionsFromString);
use Syntax::Keyword::Match ;
use File::Basename;
use File::Copy;
use File::Path qw(remove_tree);
use File::Spec::Functions;
use POSIX;
use List::MoreUtils qw( each_array );
use List::Util qw(first);
# use Data::Dump qw(dump);

my $EXTENSION = "md";
my $ruta_LEER = "/sdcard/Documents/Leer";
my $ruta_MEDIA = catfile($ruta_LEER, "Media");
my $ruta_NUEVOS = "nuevos";
my $ruta_COMICS = "comics";
my $RE_EXTENSION = qr/\.[^\.]*/;
my @opt_spec =
( 
  "nombre=s",
  "artista=s",
  "aliases=s",
  "tags=s",
  "previo=s",
  "siguiente=s",
  "copiar=s",
  "renombrar=s",
  "anexar=s",
  "numerico",
  "sortear=s",
  "d-imagenes=s",
  "skip-renombrar",
  "skip-borrar",
 );

my %opts = 
(
  "accion" => "",
  "renombrar" => \&procesar_accion,
  "copiar" => \&procesar_accion,
  "anexar" => \&procesar_accion,
);


sub yieldfile($ruta) 
{
  open( my $file, "<", $ruta ) or
  die "no se puede abrir '$ruta': $!";

  return sub {
    my $linea = <$file>;

    if ( !defined($linea) ) {
      close($file);
      return;
    }
    return $linea;
  }
}


sub procesar_accion
{
  my ($callback, $valor) = @_;
  if (defined $callback)
  {
    $opts{accion} = $$callback{name};
    $opts{valor_accion} = $valor;
  }
}

sub numero_digitos($num)
{
  my $cant = ceil(log10($num));

  return $cant;
}

sub construir_nombre_arch($nombre, $ext) 
{
  if ( extension_vacia($ext) )
  {
    $ext = "." . $EXTENSION;
  }

  return $nombre . $ext;
}

sub extension_vacia($ext)
{
  return ((not length $ext) or $ext =~ m/^\.$/);
}

sub resolver_dir($dir_defecto, $dir_crudo)
{
  my $dir = $dir_crudo eq "./" ? $dir_defecto : $dir_crudo;

  $dir = catfile($ruta_LEER, $dir); 

  if (not -d $dir)
  { 
    die("no existe tal carpeta: $dir"); 
  } 
  return $dir;
}

sub resolver_ruta($dir_defecto, $ruta_cruda)
{
  my ($nombre, $dir, $ext) = fileparse($ruta_cruda, $RE_EXTENSION);

  $dir = resolver_dir($ruta_COMICS, $dir);

  return $dir, construir_nombre_arch($nombre, $ext);
}

sub ordenar_imgs($regex, $imgs_ref)
{
  return map 
  {@$_[0]} 
  sort { @$a[1] <=> @$b[1] } 
  map {[$_, /$regex/]} @$imgs_ref ;
}

sub listar_imgs($fuente)
{
  opendir(my $img_dir, $fuente) or die("carpeta '$fuente' no existe");

  my @imgs = readdir($img_dir);

  closedir($img_dir);

  return @imgs;
}

sub construir_nombre_img($fill, $nombre, $ruta, $idx)
{
  my ( $nm, undef, $suf) = fileparse($ruta, $RE_EXTENSION);

  return sprintf("%s %0${fill}d%s" , $nombre, $idx, $suf ) ;
}

sub procesar_imgs($op, $fuente, $destino, $imgs_ref, $nuevas_imgs_ref)
{
  my $it = each_array(@$imgs_ref, @$nuevas_imgs_ref);

  while ( my ($src, $dst) = $it->() )
  {
    &$op( "$fuente/$src", "$destino/$dst" );
  }
}

sub separador()
{
  return "---";
}

sub tags_defecto()
{
  return ( "comic", "porn", "furry" );
}

sub limpiar_tags($tags_crudo)
{
  my @tags = split(/\s/, $tags_crudo);

  push(@tags, tags_defecto());

  my %temp = map { $_, 1 } @tags;

  @tags = keys %temp;

  @tags = sort @tags;

  return @tags;
}

sub formatear_frontmatter($artista, $aliases, $tags_ref)
{
  return ( 
    separador() , "\n",

    "tags:", "\n",

    ( map {  ("  - " . $_, "\n") } @$tags_ref ),

    "aliases: ${aliases}", "\n",

    "artista: ${artista}", "\n",

    "editar: true", "\n",

    separador() , "\n", "\n" 
  );

}

sub formatear_imgs($imgs_ref)
{
  return ( 
    separador(), "\n", "\n",

    map { ( formatear_link_img($_), separador(), "\n", "\n" ) } @$imgs_ref,
  );
}

sub formatear_link_img($img)
{
  return ("![[$img]]", "\n", "\n");
}


sub formatear_link_nota($nombre)
{
  return ("[[ $nombre ]]", "\n", "\n");
}

sub procesar_args_desde_arch($archs_ref, $fuente_dir)
{
   my @idxs = grep {@$archs_ref[$_] =~ m/\.txt/ } keys @$archs_ref ;

  if (scalar @idxs)
  {
    my $argstr = "";

    my $extra_args_arch = catfile($fuente_dir, @$archs_ref[$idxs[0]]);

    splice(@$archs_ref, $_, 1) for (sort {$b <=> $a} @idxs);

    open(my $argfile,'<', $extra_args_arch);

    while(my $linea = <$argfile>)
    {
      $linea =~ s/\n/ /;
      $argstr = "$argstr $linea";
    }

    close($argfile);

    GetOptionsFromString
    (
      $argstr, 
      \%opts, 
      @opt_spec 
    ) or die("opciones no reconocidas: $!") ;
  }
}

sub crear_comic 
{
  my ($nombre, $dir, $ext) = fileparse($opts{nombre}, $RE_EXTENSION);

  $dir = resolver_dir($ruta_COMICS, $dir);

  my $ruta_nuevo_comic = catfile
  (
    $dir, 
    construir_nombre_arch($nombre, $ext)
  );

  my $carpeta_destino = catfile($opts{"d-imagenes"}, $nombre);
 
  mkdir($carpeta_destino);

  my $nuevas_imgs;

  my $op;

  if($opts{numerico})
  {
    $opts{sortear} = "(\\d+)";
  }

  if(defined $opts{sortear})
  {
    $opts{imgs} = [ ordenar_imgs(qr/$opts{sortear}/, $opts{imgs}) ];
  }

  if ($opts{"skip-renombrar"})
  {
    $nuevas_imgs = $opts{imgs};
    $op = \&move;
  }
  else 
  {
    my $fill = numero_digitos(scalar @{$opts{imgs}});

    my @renombradas = map 
    { construir_nombre_img($fill, $nombre, $opts{imgs}[$_], $_ + 1) }  
    keys @{$opts{imgs}} ;

    $nuevas_imgs = \@renombradas;
    $op = \&copy;
  }

  procesar_imgs
  (
    $op, 
    $opts{fuente}, 
    $carpeta_destino, 
    $opts{imgs}, 
    $nuevas_imgs
  );

  unless ($opts{"skip-borrar"})
  {
    remove_tree($opts{fuente});
  }

  open(my $nuevo_comic, '>', $ruta_nuevo_comic) ;

  print $nuevo_comic (
    formatear_frontmatter
    (
      $opts{artista}, 
      $opts{aliases}, 
      [ limpiar_tags($opts{tags}) ] 
    ),

    defined $opts{previo} ? formatear_link_nota($opts{previo}) : "",

    formatear_imgs($nuevas_imgs),

    defined $opts{siguiente} ? formatear_link_nota($opts{siguiente}) : "",

  );

  close $nuevo_comic;
}

sub comics
{
  match($opts{accion} : eq)
  {
    case("renombrar")
    {
      my ($nuevo_nombre, undef, $ext) = 
      fileparse($opts{valor_accion}, $RE_EXTENSION);

      $nuevo_nombre = construir_nombre_arch($nuevo_nombre, $ext);

      my ($dir_original, $nombre_original) = 
      resolver_ruta($ruta_COMICS, $opts{fuente});

      my $ruta_original = catfile($dir_original, $nombre_original);
      
      my $ruta_nueva = catfile($dir_original, $nuevo_nombre);

      move($ruta_original, $ruta_nueva);
    }
    
    case ("copiar")
    {
      my $ruta_copia  = catfile( 
        resolver_ruta($ruta_COMICS, $opts{valor_accion})
      );

      my $ruta_original  = catfile( 
        resolver_ruta($ruta_COMICS, $opts{fuente})
      );

      copy($ruta_original, $ruta_copia);
    }

    case ("anexar")
    {
      # definir caarpeta de origen imagenes
      my ($stem_fuente, $dir_fuente, undef) = 
      fileparse($opts{fuente}, $RE_EXTENSION);

      if (! -d $opts{fuente})
      {
        my $nuevo_dir = resolver_dir($ruta_NUEVOS, $dir_fuente);

        $opts{fuente} = catfile($nuevo_dir, $stem_fuente);
      }

      # listar imagenes y ordensrlas si necesariaa
      $opts{imgs} = [ listar_imgs($opts{fuente}) ];

      procesar_args_desde_arch($opts{imgs}, $opts{fuente});

      if($opts{numerico})
      {
        $opts{sortear} = "(\\d+)";
      }

      if(defined $opts{sortear})
      {
        $opts{imgs} = [ ordenar_imgs(qr/$opts{sortear}/, $opts{imgs}) ];
      }

      # hallar mombre, ruta del comic existente, carpeta destino
      my ($nombre_comic, $dir, $ext) = 
      fileparse($opts{valor_accion}, $RE_EXTENSION);

      $dir = resolver_dir($ruta_COMICS, $dir);

      my $carpeta_destino = catfile($ruta_MEDIA, $nombre_comic);

      my $ruta_nuevo_comic = catfile
      (
        $dir, 
        construir_nombre_arch($nombre_comic, $ext)
      );

      # listar partes del documento, hallar el ultimo numero imagen  

      my $gen_lineas = yieldfile($ruta_nuevo_comic);

      my @lineas;

      while (my $linea = &$gen_lineas()) {
          push @lineas, $linea;
      }

      my $link_img_re = qr/!\[\[(.*)\]\]/;

      my $ultima_img_idx =
        first { $lineas[$_] =~ m/$link_img_re/ } sort { $b <=> $a } keys @lineas;

      my $ultima_img = $lineas[$ultima_img_idx];

      my ($entrada) = $ultima_img =~ $link_img_re;

      my ( $nombre, $num ) = $entrada =~ /(\D+)(\d+)\./;

      $/ = " ";

      chomp $nombre;

      my $fill = numero_digitos(scalar @{$opts{imgs}} + $num);

      my @renombradas = map 
      { construir_nombre_img($fill, $nombre, $opts{imgs}[$_], $_ + $num + 1) }  
      keys @{$opts{imgs}} ;

      splice @lineas, $ultima_img_idx + 3, 0,
        map { ( "\n", formatear_link_img($_), separador(), "\n" ) } @renombradas;

      open(my $comic_modificado, ">", $ruta_nuevo_comic);

      print $comic_modificado @lineas;

      close($comic_modificado);

      procesar_imgs
      (
        \&copy, 
        $opts{fuente}, 
        $carpeta_destino, 
        $opts{imgs}, 
        \@renombradas,
      );


      unless ($opts{"skip-borrar"})
      {
        remove_tree($opts{fuente});
      }

    }

    default
    {
      my ($stem_fuente, $dir_fuente, undef) = 
      fileparse($opts{fuente}, $RE_EXTENSION);

      if (! -d $opts{fuente})
      {
        my $nuevo_dir = resolver_dir($ruta_NUEVOS, $dir_fuente);

        $opts{fuente} = catfile($nuevo_dir, $stem_fuente);
      }

      $opts{imgs} = [ listar_imgs($opts{fuente}) ];

      procesar_args_desde_arch($opts{imgs}, $opts{fuente});

      $opts{nombre} //= $stem_fuente;

      $opts{artista} //= "";

      $opts{tags} //= "";
      
      $opts{aliases} //= "";

      if (defined $opts{"d-imagenes"} )
      {
        if(! -d $opts{"d-imagenes"})
        {
          die("no hay tal directorio: ${$opts{'d-imagenes'}}");
        }
      }
      else
      {
        $opts{"d-imagenes"} = $ruta_MEDIA;
      }

      crear_comic();
    }
  }
}


match(my $comm = shift : eq)
{
  case if ("comic" =~ /^$comm/ )
  { 
     GetOptions
     (
       \%opts,
       @opt_spec,
     )  or die("opciones no reconocidas: $!") ;

    $opts{fuente} = shift ;

    defined $opts{fuente} or die("no se paso nombre directorio origen.");

    comics(); 
  }

  case if ("tags" =~ /^$comm/ )
  { 
     GetOptions
     (
       \%opts,
       "modificar=s",
       "contar=s",
    )  or die("opciones no reconocidas: $!") ;

    my $nombre = shift ;
  }

  default
  { 
    die("no se reconoce la opcion: '$comm'. opciones validas: comic, tags") ;
  }
}

