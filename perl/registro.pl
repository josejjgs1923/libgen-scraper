#!/usr/bin/env perl

use strict; 
use v5.38;
use warnings;
use autodie;
use Getopt::Long;
use Syntax::Keyword::Match ;
use Time::Piece;
use File::Temp qw(tempfile);
use File::Copy;

my @opt_spec =(
  "separador=s",
  "cabecera",
);
my %opts = (
  "separador" => ";",
  "formato_tiempo" => "%d %m %Y %H %M",
);
my $comm ;
my $arch ;
 
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


sub agregar()
{
  if ($opts{cabecera})
  {
    my ($registro, $ruta) = tempfile();

    print $registro ( join($opts{separador}, @ARGV), "\n");

    my $gen = yieldfile($arch);

    while(defined(my $linea = &$gen()))
    {
      print $registro $linea;
    }

    close($registro);

    copy($ruta, $arch);

    unlink($ruta);

    exit;
  }

  open(my $registro, ">>", $arch);

  my $t = localtime;

  my @tiempo = split "\\D", $t->strftime($opts{formato_tiempo});

  print $registro (  join($opts{separador}, (@tiempo, @ARGV)), "\n");

  close($registro);
}

$comm = shift;

match($comm : eq)
{
  case if ("agregar" =~ /^$comm/ )
  { 
     GetOptions
     (
       \%opts,
       @opt_spec,
     )  or die("opciones no reconocidas: $!") ;

    $arch = shift;
    agregar();
  }

  case if ("borrar" =~ /^$comm/ )
  { 
     GetOptions
     (
       \%opts,
    )  or die("opciones no reconocidas: $!") ;

    my $nombre = shift ;
  }

  default
  { 
    die("no se reconoce la opcion: '$comm'. opciones validas: agregar, borrar") ;
  }
}
