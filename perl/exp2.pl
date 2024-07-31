#!/usr/bin/env perl

use strict; 
use v5.38;
use warnings;
use autodie;
use Data::Dump qw(dump);


sub _pairwise($arr)
{
  my @idxs = (0, 1);
  my $limit = scalar @$arr;
  my @pair;

  return sub
  {
    return if $idxs[1] == $limit;
    @pair = @$arr[@idxs];
    @idxs = map {$_ + 1} @idxs;
    return  @pair; 
  }
}


my @otros = ("miu");

my $it = pairwise(\@otros);

while( my ($f, $s) = $it->() )
{
  dump($f, $s);
}


