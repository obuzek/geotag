#!/usr/bin/env python

import sys
from collections import defaultdict

f = sys.argv[1]

# USERNAME                                                                                                                     
# TWEET_ID                                                                                                                   
# PLACE_ID                                                                                                                
# TIME                                                                                                                     
# SOURCE                                                                                                                     
# LAT                                                                                                                       
# LONG                                                                                                                  
# TWEET                                                                                                                  


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
