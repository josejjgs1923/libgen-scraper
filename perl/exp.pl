#!/usr/bin/env perl

use strict;
use v5.38;
use warnings;
use autodie;
use List::Util qw(first);
use Data::Dump qw(dump);
use File::Basename;

my $ruta = "/storage/emulated/0/Documents/Leer/comics/Donut Mind If I do.md";

my $dir = "/storage/emulated/0/Documents/Leer/nuevos/Lucoa Titjob 1";

sub yieldfile($ruta) {

    open( my $file, "<", $ruta );

    return sub {
        my $linea = <$file>;

        if ( !defined($linea) ) {
            close($file);
            return;
        }
        return $linea;
    }
}

my $gen_file = yieldfile($ruta);

while ( my $linea = &$gen_file() ) {
    say($linea);
}

