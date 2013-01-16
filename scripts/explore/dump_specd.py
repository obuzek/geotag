#!/usr/bin/env python

import sys
import argparse
from collections import defaultdict

parser = argparse.ArgumentParser(description='Dump specified fields.')
parser.add_argument('integers', metavar='N', type=int, nargs='+',
                   help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                   const=sum, default=max,
                   help='sum the integers (default: find the max)')

args = parser.parse_args()

poss = ["username",
         "tweet_id",
         "place_id",
         "time",
        "source",
        "lat",
        "long",
        "tweet"]

uname_d = defaultdict(list)

for line in open(f):
    line_arr = line.strip().split("\t")

    uname_d[line_arr[0]].append([line_arr[6],line_arr[5],line_arr[-1]])


for uname in uname_d:
    print uname
    print "LAT\tLONG\tTWEET"
    for lat,lon,tweet in uname_d[uname]:
        print "\t".join([lat,lon,tweet])
    print "---"
