#!/usr/bin/env python

import sys
import os
import json
import re

#import pymongo
#from pymongo import Connection()
#conn = Connection()
#db = conn.test

s = ["USERNAME",
     "TWEET_ID",
     "PLACE_ID",
     "TIME",
     "SOURCE",
     "LAT",
     "LONG",
     "TWEET"]

sys.stdout.write("\t".join(s)+"\n")

for f in sys.argv[1:]:
    for line in open(f):
        line = line.strip()
        j = json.loads(line)


        # if has a location:
        if j["geo"] == None:
            continue

        # USERNAME "user" : "id" / "id_str" ; 
        # TWEET_ID "id_str"
        # PLACE_ID "place" : "id"
        # TIME "created_at"
        # SOURCE "source"
        # LAT "coordinates" : "coordinates" : [0]
        # LONG "coordinates" : "coordinates" : [1]
        # TWEET "text"

        place = str(None)
        if j["place"] is not None:
            place = j["place"]["id"]

        res = [ j["user"]["id_str"],
                j["id"],
                place,
                j["created_at"],
                j["source"],
                j["coordinates"]["coordinates"][0],
                j["coordinates"]["coordinates"][1],
                re.sub("\s"," ",j["text"])]


        sys.stdout.write("\t".join([unicode(x) for x in res])+"\n")
        sys.stdout.flush()
