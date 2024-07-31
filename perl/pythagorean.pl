#!/usr/bin/env perl

use strict; 
use v5.38;
use warnings;
use autodie;

my $obj = shift;

sub es_entero($num)
{
  return ($num =~ /^-?\d+\z/);
}

( $obj % 2 ) and die("debe darse un numero par");

my $a = 1;

my $b = ($obj * ($obj/2 - $a))/($obj - $a);

my $c;

while($a < $b)
{
  $b = ($obj * ($obj/2 - $a))/($obj - $a);

  if (es_entero($b))
  {
    $c = $obj - $a - $b;
    
    printf("a: %s, b: %s, c: %s\n", $a, $b ,$c);
  }
  $a++;
}
