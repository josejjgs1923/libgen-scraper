#!/usr/bin/env perl

use strict; 
use v5.38;
use warnings;
use autodie;
use List::MoreUtils qw(each_array);

my @den = (50, 100, 200, 500, 1000);

my @cant = ( 19, 37, 23, 9, 2 );

my $sum = 0;

my $it = each_array(@den, @cant);

while (my ($num, $d) = $it->() )
{
  $sum += $num * $d;
}

say $sum;
