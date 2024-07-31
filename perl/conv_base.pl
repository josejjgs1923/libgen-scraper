#!/usr/bin/env perl

use strict; 
use v5.38;
use warnings;
use autodie;
use File::Basename;
use Data::Dump qw(dump);

sub convertir_base10($base, $num_base)
{
  my @digitos = split //, $num_base;

  my $idx_final = $#digitos;

  my $num_10 = 0;

  $num_10 += $digitos[$_] * $base ** ( $idx_final - $_)  for  ( 0 .. $#digitos );

  return $num_10;
}

sub convertir_basen($base, $num_10)
{
  my $dividendo = $num_10;

  my @digitos = ();
  
  while($base <= $dividendo )
  {
    push @digitos, ($dividendo % $base);
    $dividendo = int($dividendo / $base);
  }
  push @digitos, $dividendo;

  return scalar reverse @digitos;
}

my $base = shift;

my $num_10 = shift;

say(convertir_basen($base, $num_10));
